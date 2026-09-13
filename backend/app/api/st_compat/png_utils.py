"""Minimal pure-Python PNG reader/writer for SillyTavern character cards.

SillyTavern stores character cards inside the PNG's tEXt chunks:
* keyword "chara"  -> base64(V2 JSON)
* keyword "ccv3"   -> base64(V3 JSON)
"""

from __future__ import annotations

import base64
import json
import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CARD_KEYWORDS = ("chara", "ccv3")


def is_png(data: bytes) -> bool:
    return data.startswith(PNG_SIGNATURE)


def _iter_chunks(data: bytes):
    position = len(PNG_SIGNATURE)
    while position + 8 <= len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        chunk_type = data[position + 4:position + 8]
        chunk_data = data[position + 8:position + 8 + length]
        yield chunk_type, chunk_data
        position += 12 + length


def _make_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    return (
        struct.pack(">I", len(chunk_data))
        + chunk_type
        + chunk_data
        + struct.pack(">I", zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
    )


def _text_keyword(chunk_data: bytes) -> str:
    nul = chunk_data.find(b"\x00")
    if nul == -1:
        return ""
    return chunk_data[:nul].decode("latin-1").lower()


def _text_chunk(keyword: str, text: str) -> bytes:
    return keyword.encode("latin-1") + b"\x00" + text.encode("latin-1")


def read_character_data(png_bytes: bytes) -> str:
    """Extract the embedded card JSON from a PNG (V3 takes precedence)."""
    found = {}
    for chunk_type, chunk_data in _iter_chunks(png_bytes):
        if chunk_type == b"tEXt":
            keyword = _text_keyword(chunk_data)
            if keyword in _CARD_KEYWORDS:
                nul = chunk_data.find(b"\x00")
                text = chunk_data[nul + 1:].decode("latin-1")
                found[keyword] = text

    for keyword in ("ccv3", "chara"):
        if keyword in found:
            return base64.b64decode(found[keyword]).decode("utf-8")
    raise ValueError("PNG does not contain character data")


def write_character_data(png_bytes: bytes, card_json: str) -> bytes:
    """Embed card JSON into a PNG, writing both V2 (chara) and V3 (ccv3) chunks."""
    chunks = [
        (chunk_type, chunk_data)
        for chunk_type, chunk_data in _iter_chunks(png_bytes)
        if not (chunk_type == b"tEXt" and _text_keyword(chunk_data) in _CARD_KEYWORDS)
    ]

    text_chunks = [
        (b"tEXt", _text_chunk("chara", base64.b64encode(card_json.encode("utf-8")).decode("ascii"))),
    ]
    try:
        card = json.loads(card_json)
        if isinstance(card, dict):
            v3 = dict(card)
            v3["spec"] = "chara_card_v3"
            v3["spec_version"] = "3.0"
            text_chunks.append(
                (b"tEXt", _text_chunk("ccv3", base64.b64encode(json.dumps(v3).encode("utf-8")).decode("ascii")))
            )
    except (json.JSONDecodeError, TypeError):
        pass

    output = bytearray(PNG_SIGNATURE)
    inserted = False
    for chunk_type, chunk_data in chunks:
        if chunk_type == b"IEND" and not inserted:
            for text_type, text_data in text_chunks:
                output += _make_chunk(text_type, text_data)
            inserted = True
        output += _make_chunk(chunk_type, chunk_data)

    if not inserted:
        for text_type, text_data in text_chunks:
            output += _make_chunk(text_type, text_data)
        output += _make_chunk(b"IEND", b"")
    return bytes(output)


def default_avatar_png(card_json: str) -> bytes:
    """Create a tiny valid 1x1 RGB PNG with the card JSON embedded."""
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00\x60\x60\x60"  # filter byte + dark gray RGB pixel
    png = PNG_SIGNATURE
    png += _make_chunk(b"IHDR", ihdr)
    png += _make_chunk(b"IDAT", zlib.compress(raw))
    png += _make_chunk(b"IEND", b"")
    return write_character_data(png, card_json)
