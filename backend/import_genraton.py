"""
Import genraton.xyz scraped apps into work cards and character cards.
Maps genraton "apps" to the ai-tools-platform work card + character card model.
"""
import json
import sys
import os
import io
from datetime import datetime

# Fix GBK encoding issues on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.snowflake import generate_id
from app.utils.mysql import execute, init_pool, query_one
from app.core.config import get_config
from app.services.cache import invalidate_work

# Load scraped data
with open('genraton_apps.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

apps = data.get('installed_apps', [])
print(f'Loaded {len(apps)} apps from genraton_apps.json')

# Init
config = get_config()
init_pool(config.MYSQL_CONFIG)

# Default user_id for imported works
DEFAULT_USER_ID = 1000000000000001
MAX_DESC_LENGTH = 500

imported_works = 0
imported_characters = 0
skipped = 0

for item in apps:
    app = item.get('app', {})
    name = (app.get('name') or '').strip()
    if not name:
        skipped += 1
        continue

    summary = (app.get('summary') or '').strip()
    desc = summary[:MAX_DESC_LENGTH] if summary else name
    cover_url = (app.get('cover') or '').strip()
    author = (app.get('created_by_account_name') or '未知作者').strip()
    mode = (app.get('mode') or 'chat').strip()

    # Extract tags as plain strings
    raw_tags = app.get('tags') or []
    tag_names = []
    if isinstance(raw_tags, list):
        for t in raw_tags:
            if isinstance(t, dict):
                rt = t.get('relation_tag') or {}
                tn = rt.get('name', '')
                if tn:
                    tag_names.append(tn)
            elif isinstance(t, str):
                tag_names.append(t)

    # Build opening from summary
    opening_text = summary[:300] if summary else name

    # Build role_config
    role_config = {
        "protagonist_setting": {
            "name": "",
            "setting": "",
            "core_motivation": "",
        },
        "worldview_setting": {
            "name": "",
            "era_background": "",
            "core_conflict": "",
            "overall_atmosphere": "",
        },
        "init_plot_status": opening_text,
        "writing_style": {
            "style": "novel",
            "tone": "neutral",
            "pace": "normal",
            "nsfwLevel": "nsfw",
        },
        "npc_settings": [],
        "play_rule": "",
        "status_bar": "",
        "main_plot": "",
    }

    try:
        work_id = generate_id()

        # Check for duplicate by name
        existing = query_one(
            "SELECT id FROM t_work_card WHERE name = %s LIMIT 1",
            (name,)
        )
        if existing:
            print(f'  SKIP (duplicate): {name}')
            skipped += 1
            continue

        execute(
            """INSERT INTO t_work_card
               (id, user_id, name, `desc`, cover, author, language, category,
                summary, opening, openings, tags, role_config, content, use_count, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                work_id,
                DEFAULT_USER_ID,
                name,
                desc,
                cover_url,
                author,
                'zh-Hans',
                0,
                summary,
                opening_text,
                json.dumps([{"text": opening_text}], ensure_ascii=False),
                json.dumps(tag_names, ensure_ascii=False),
                json.dumps(role_config, ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                0,
                1,
            ),
        )
        imported_works += 1
        print(f'  OK: [{mode}] {name}')

    except Exception as e:
        print(f'  ERROR importing "{name}": {e}')
        skipped += 1

print(f'\n=== Import Summary ===')
print(f'Works imported: {imported_works}')
print(f'Characters imported: {imported_characters}')
print(f'Skipped: {skipped}')
print(f'Total apps processed: {len(apps)}')
