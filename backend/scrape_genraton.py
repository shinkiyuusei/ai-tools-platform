"""
Scrape work cards from genraton.xyz explore page markdown content
and save as genraton_apps.json for import.
"""
import sys
import re
import json
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Read the scraped page content
scrape_file = r'C:\Users\40935\.claude\projects\c--Users-40935-Desktop-python-ai-tools-platform\347ab3dc-545b-4711-abb6-2d153af75822\tool-results\mcp-firecrawl-firecrawl_scrape-1784907763200.txt'

with open(scrape_file, 'r', encoding='utf-8') as f:
    content = json.load(f)

md = content.get('markdown', '')
print(f'Markdown length: {len(md)} chars')

# Separator between fields: \\ + \n + \\ + \n
# In Python string: chr(92)+chr(92)+chr(10)+chr(92)+chr(92)+chr(10)
# Or as raw bytes: backslash backslash newline backslash backslash newline
SEP = chr(92) + chr(92) + chr(10) + chr(92) + chr(92) + chr(10)

# Each line ends with: \\ + \n
LINE_END = chr(92) + chr(92) + chr(10)

# Find all card positions by locating "作者：" markers
author_pattern = re.compile(r'作者[：:]')
author_matches = list(author_pattern.finditer(md))
print(f'Found {len(author_matches)} author markers')

apps = []
seen_ids = set()

for author_match in author_matches:
    author_pos = author_match.start()

    # Find the nearest installed link AFTER this position
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

    # Find the start of this card - look for [! that is before author_pos
    before_author = md[:author_pos]
    card_starts = list(re.finditer(r'\[!', before_author))
    if not card_starts:
        continue

    card_start = card_starts[-1].start()

    # Extract the full card text (from [! to end of link)
    card_full = md[card_start:author_pos + link_end_in_after]

    # Remove outer [ and ](link_url)
    # Find the last ]( before the link
    bracket_link_pos = card_full.rfind('](')
    if bracket_link_pos < 0:
        continue
    inner = card_full[1:bracket_link_pos]  # Strip outer [ and ](link)

    # Split by double separator
    parts = inner.split(SEP)
    # Clean up each part: strip LINE_END from each part
    clean_parts = []
    for p in parts:
        p = p.strip()
        # Remove trailing \\ + \n (line end markers)
        while p.endswith(LINE_END):
            p = p[:-len(LINE_END)]
        # Remove trailing \\ without newline
        while p.endswith(chr(92) + chr(92)):
            p = p[:-2]
        p = p.strip()
        if p:
            clean_parts.append(p)

    if len(clean_parts) < 4:
        print(f'\nSKIP {link_id}: only {len(clean_parts)} parts')
        continue

    # Part 0: ![](cover_url)
    img_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', clean_parts[0])
    cover = img_match.group(1) if img_match else ''
    # Check if there's content after the image in part 0
    if img_match:
        after_img = clean_parts[0][img_match.end():].strip()
        if after_img:
            # This might be the usage count
            clean_parts.insert(1, after_img)

    idx = 0
    # Skip the image part
    if img_match and img_match.group(0) == clean_parts[0].strip():
        idx = 1
    elif cover:
        # The cover URL might be the first content
        idx = 1

    if len(clean_parts) <= idx:
        continue

    # Now parse: usage, name, description(s)..., author, rating, tags
    remaining = clean_parts[idx:]

    # Find author index
    author_idx = None
    author_name = ''
    for i, part in enumerate(remaining):
        if re.match(r'作者[：:]', part):
            author_idx = i
            author_name = re.sub(r'^作者[：:]\s*', '', part).strip()
            break

    if author_idx is None or author_idx < 2:
        print(f'\nSKIP {link_id}: author_idx={author_idx}')
        continue

    usage = remaining[0] if len(remaining) > 0 else ''
    name = remaining[1] if len(remaining) > 1 else ''

    # Description = everything between name and author
    desc_parts = remaining[2:author_idx]
    desc = chr(10).join(desc_parts) if desc_parts else ''

    # After author: rating, tags
    after_author = remaining[author_idx + 1:]
    rating = after_author[0] if len(after_author) > 0 else ''
    tags_str = after_author[1] if len(after_author) > 1 else ''

    # Clean up escaped brackets in name
    name = name.replace(chr(92) + '[', '[').replace(chr(92) + ']', ']')

    # Clean up description - remove line-end markers
    desc = desc.replace(LINE_END, chr(10)).replace(chr(92) + chr(92), '')

    app_data = {
        'id': link_id,
        'name': name.strip(),
        'summary': desc.strip(),
        'cover': cover.strip(),
        'author': author_name.strip(),
        'usage': usage.strip(),
        'rating': rating.strip(),
        'tags_str': tags_str.strip(),
    }

    print(f'\n=== Card: {app_data["name"][:80]} ===')
    print(f'  Author: {app_data["author"]}')
    print(f'  Usage: {app_data["usage"]}')
    print(f'  Rating: {app_data["rating"]}')
    print(f'  Tags: {app_data["tags_str"][:100]}')
    print(f'  Cover: {app_data["cover"][:80]}')
    print(f'  Desc: {app_data["summary"][:150]}')

    apps.append(app_data)

print(f'\n\n=== TOTAL: {len(apps)} apps parsed ===')

# Save for import
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
        for a in apps
    ]
}

output_file = 'genraton_apps.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\nSaved {len(apps)} apps to {output_file}')
for a in apps:
    print(f'  - [{a["rating"]}] {a["name"][:60]} | by {a["author"]}')
