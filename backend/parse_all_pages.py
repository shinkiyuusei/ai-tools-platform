"""
Parse all genraton page markdown files and generate genraton_apps.json.
Reads genraton_page*.md files (each containing the markdown from one page).
"""
import sys
import re
import json
import io
import os
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SEP = chr(92) + chr(92) + chr(10) + chr(92) + chr(92) + chr(10)
LINE_END = chr(92) + chr(92) + chr(10)

def parse_markdown_for_cards(md: str) -> list:
    """Parse markdown content and extract work card data."""
    apps = []
    seen_ids = set()

    author_matches = list(re.finditer(r'作者[：:]', md))

    for author_match in author_matches:
        author_pos = author_match.start()
        after_text = md[author_pos:]
        link_match = re.search(
            r'\]\(https://genraton\.xyz/explore/installed/([a-f0-9-]+)\)',
            after_text
        )
        if not link_match:
            continue

        link_id = link_match.group(1)
        if link_id in seen_ids:
            continue
        seen_ids.add(link_id)

        link_end_in_after = link_match.end()
        before_author = md[:author_pos]
        card_starts = list(re.finditer(r'\[!', before_author))
        if not card_starts:
            continue

        card_start = card_starts[-1].start()
        card_full = md[card_start:author_pos + link_end_in_after]

        bracket_link_pos = card_full.rfind('](')
        if bracket_link_pos < 0:
            continue
        inner = card_full[1:bracket_link_pos]

        parts = inner.split(SEP)
        clean_parts = []
        for p in parts:
            p = p.strip()
            while p.endswith(LINE_END):
                p = p[:-len(LINE_END)]
            while p.endswith(chr(92) + chr(92)):
                p = p[:-2]
            p = p.strip()
            if p:
                clean_parts.append(p)

        if len(clean_parts) < 4:
            continue

        img_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', clean_parts[0])
        cover = img_match.group(1) if img_match else ''
        if img_match:
            after_img = clean_parts[0][img_match.end():].strip()
            if after_img:
                clean_parts.insert(1, after_img)

        idx = 1 if (img_match and img_match.group(0) == clean_parts[0].strip()) else 1
        if len(clean_parts) <= idx:
            continue

        remaining = clean_parts[idx:]
        author_idx = None
        author_name = ''
        for i, part in enumerate(remaining):
            if re.match(r'作者[：:]', part):
                author_idx = i
                author_name = re.sub(r'^作者[：:]\s*', '', part).strip()
                break

        if author_idx is None or author_idx < 2:
            continue

        usage = remaining[0] if len(remaining) > 0 else ''
        name = remaining[1] if len(remaining) > 1 else ''
        desc_parts = remaining[2:author_idx]
        desc = chr(10).join(desc_parts) if desc_parts else ''
        after_author = remaining[author_idx + 1:]
        rating = after_author[0] if len(after_author) > 0 else ''
        tags_str = after_author[1] if len(after_author) > 1 else ''

        name = name.replace(chr(92) + '[', '[').replace(chr(92) + ']', ']')
        desc = desc.replace(LINE_END, chr(10)).replace(chr(92) + chr(92), '')

        apps.append({
            'id': link_id,
            'name': name.strip(),
            'summary': desc.strip(),
            'cover': cover.strip(),
            'author': author_name.strip(),
            'usage': usage.strip(),
            'rating': rating.strip(),
            'tags_str': tags_str.strip(),
        })

    return apps


# Find all page files
page_files = sorted(glob.glob('genraton_page*.md'))
if not page_files:
    print("ERROR: No genraton_page*.md files found!")
    print("Expected files: genraton_page1.md through genraton_page7.md")
    sys.exit(1)

print(f'Found {len(page_files)} page files')

all_apps = []
seen_names = set()

for page_file in page_files:
    with open(page_file, 'r', encoding='utf-8') as f:
        md = f.read()
    apps = parse_markdown_for_cards(md)
    for app in apps:
        if app['name'] not in seen_names:
            seen_names.add(app['name'])
            all_apps.append(app)
    print(f'  {page_file}: {len(apps)} cards found')

print(f'\nTotal unique cards: {len(all_apps)}')

# Save as genraton_apps.json in the format expected by import_genraton.py
output = {
    'installed_apps': [
        {
            'app': {
                'name': a['name'],
                'summary': a['summary'],
                'cover': a['cover'],
                'created_by_account_name': a['author'],
                'mode': 'chat',
                'tags': [t.strip() for t in a['tags_str'].split('/') if t.strip()],
            }
        }
        for a in all_apps
    ]
}

output_file = 'genraton_apps.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\nSaved {len(all_apps)} apps to {output_file}')
for i, a in enumerate(all_apps):
    print(f'  {i+1}. [{a["rating"]}] {a["name"][:70]} | by {a["author"]}')
