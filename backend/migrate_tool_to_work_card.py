"""
Database migration: t_ai_tool → t_work_card

Prerequisites: Tables from init.sql must exist (t_work_card, t_work_collect, t_conversation)

Run this script to:
1. Transform old form_config JSON to new content JSON format
2. Remap IDs and update foreign keys
3. Drop old tables and MongoDB collections
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app
from app.utils.mysql import execute, query_one, query_all

app = create_app()


def resolve_tag_ids_to_objects(tag_ids_str):
    """Convert comma-separated tag ID string to array of {name, id, type}."""
    if not tag_ids_str:
        return []
    result = []
    seen = set()
    for tid in tag_ids_str.split(","):
        tid = tid.strip()
        if not tid or tid in seen:
            continue
        seen.add(tid)
        if tid.isdigit():
            tag_row = query_one(
                "SELECT id, name FROM t_tag WHERE id = %s", (int(tid),)
            )
            if tag_row:
                result.append({"id": tag_row["id"], "name": tag_row["name"], "type": "app"})
        else:
            result.append({"id": abs(hash(tid)) % 1000 + 100, "name": tid, "type": "app"})
    return result


def transform_form_config(old_row):
    """Transform old t_ai_tool row + form_config to new column values.
    Returns (name, desc, cover, author, language, category, summary, opening, openings, tags, role_config).
    """
    name = old_row.get("name", "")
    desc = old_row.get("desc", "")
    icon = old_row.get("icon", "")
    use_desc = old_row.get("use_desc", "")
    tag_ids = old_row.get("tag_ids", "")

    config = {}
    raw_config = old_row.get("form_config", "")
    if raw_config:
        try:
            config = json.loads(raw_config) if isinstance(raw_config, str) else raw_config
        except (json.JSONDecodeError, TypeError):
            config = {}

    old_chars = config.get("characters", [])
    npc_settings = []
    for c in old_chars:
        npc_settings.append({
            "name": c.get("name", ""),
            "occupation": c.get("occupation", ""),
            "age": c.get("age", ""),
            "gender": c.get("gender", ""),
            "appearance": c.get("appearance", ""),
            "personality": c.get("personality", ""),
            "tone": c.get("speechTone", ""),
            "background_setting": c.get("background", ""),
        })

    old_protagonist = config.get("protagonist", {})
    protagonist_setting = {
        "name": old_protagonist.get("name", ""),
        "setting": old_protagonist.get("description", ""),
        "core_motivation": old_protagonist.get("motivation", ""),
    }

    old_world = config.get("worldSetting", {})
    worldview_setting = {
        "name": old_world.get("worldName", ""),
        "era_background": old_world.get("eraTech", ""),
        "core_conflict": old_world.get("coreConflict", ""),
        "overall_atmosphere": old_world.get("toneAtmosphere", ""),
    }

    opening_text = config.get("opening", "")
    detailed_intro = config.get("detailedIntro", "") or use_desc
    summary = config.get("detailedIntro", "") or desc

    tags = config.get("tags")
    if tags is None:
        tags = resolve_tag_ids_to_objects(tag_ids)

    opening_statements = []
    if opening_text:
        opening_statements = [{"label": "默认开局", "text": opening_text}]

    role_config = {
        "main_plot": old_world.get("mainPlot", "") or detailed_intro,
        "play_rule": config.get("gameRules", ""),
        "status_bar": config.get("statusBar", ""),
        "npc_settings": npc_settings,
        "init_plot_status": opening_text,
        "worldview_setting": worldview_setting,
        "protagonist_setting": protagonist_setting,
    }

    return (
        name, desc, icon, config.get("author", ""), "zh-Hans", 0,
        summary, opening_text,
        json.dumps(opening_statements, ensure_ascii=False),
        json.dumps(tags, ensure_ascii=False),
        json.dumps(role_config, ensure_ascii=False),
    )


def run():
    with app.app_context():
        print("=" * 60)
        print("Migration: t_ai_tool → t_work_card")
        print("=" * 60)

        # 1. Read all t_ai_tool rows
        print("\n[1/4] Reading t_ai_tool rows...")
        old_rows = query_all("""
            SELECT id, name, icon, `desc`, use_desc, category_id,
                   tag_ids, form_config, ai_api, is_free, is_vip, use_count
            FROM t_ai_tool WHERE status = 1
        """)
        print(f"  Found {len(old_rows)} rows")

        # 2. Transform and insert
        print("\n[2/4] Transforming data and inserting into t_work_card...")
        id_map = {}  # old_id → new_id
        for i, row in enumerate(old_rows):
            old_id = row["id"]
            name, desc, cover, author, lang, cat, summary, opening, openings, tags, role_config = (
                transform_form_config(row)
            )
            new_id = execute(
                "INSERT INTO t_work_card (user_id, name, `desc`, cover, author, language, "
                "category, summary, opening, openings, tags, role_config, use_count, status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (0, name, desc, cover, author, lang, cat, summary, opening,
                 openings, tags, role_config, row.get("use_count", 0), 1),
            )
            id_map[old_id] = new_id
            if (i + 1) % 10 == 0:
                print(f"  ... {i + 1}/{len(old_rows)} migrated")

        print(f"  [OK] {len(id_map)} rows migrated")
        print(f"  ID map: {len(id_map)} entries")

        # 3. Update t_conversation.work_id
        print("\n[3/4] Updating t_conversation.work_id references...")
        conv_updated = 0
        for old_id, new_id in id_map.items():
            affected = execute(
                "UPDATE t_conversation SET work_id = %s WHERE work_id = %s",
                (new_id, old_id),
            )
            conv_updated += (affected or 0)
        print(f"  [OK] {conv_updated} conversation rows updated")

        # 4. Drop old tables and MongoDB collections
        print("\n[4/4] Cleaning up old resources...")

        try:
            execute("DROP TABLE IF EXISTS t_ai_tool")
            print("  [OK] t_ai_tool dropped")
        except Exception as e:
            print(f"  ⚠ t_ai_tool drop failed: {e}")

        try:
            execute("DROP TABLE IF EXISTS t_work_import_log")
            print("  [OK] t_work_import_log dropped")
        except Exception as e:
            print(f"  ⚠ t_work_import_log drop failed: {e}")

        print("\n" + "=" * 60)
        print("Migration complete!")
        print(f"  {len(id_map)} works migrated to t_work_card")
        print(f"  {conv_updated} conversation references updated")
        print("=" * 60)


if __name__ == "__main__":
    run()
