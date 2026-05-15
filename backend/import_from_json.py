"""Import a work from a JSON file into t_ai_tool."""
import json, sys, pymysql

def import_work(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    form_config = {
        "type": "chat",
        "author": data.get("author", ""),
        "rating": data.get("rating", 0),
        "sourceId": data.get("sourceId", ""),
        "models": data.get("models", ["deepseek-v4-flash"]),
        "opening": data.get("opening", ""),
        "systemPrompt": data.get("systemPrompt", ""),
        "detailedIntro": data.get("detailedIntro", ""),
        "characters": data.get("characters", []),
        "protagonist": data.get("protagonist", {}),
        "worldSetting": data.get("worldSetting", {}),
        "gameRules": data.get("gameRules", ""),
        "statusBar": data.get("statusBar", ""),
    }

    conn = pymysql.connect(
        host="127.0.0.1", port=3306,
        user="ai_user", password="ai_pass_123",
        database="ai_tools_platform", charset="utf8mb4"
    )
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO t_ai_tool
           (name, icon, `desc`, use_desc, category_id, tag_ids, form_config, ai_api,
            is_free, is_vip, use_count, sort_order, status)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (data["name"], data.get("icon", ""), data["desc"], data.get("use_desc", ""),
         data.get("category_id", 2), data.get("tag_ids", ""),
         json.dumps(form_config, ensure_ascii=False), data.get("ai_api", "deepseek"),
         data.get("is_free", 1), data.get("is_vip", 0), data.get("use_count", 0),
         data.get("sort_order", 0), 1)
    )
    tool_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    print(f"OK - {data['name']} (id={tool_id})")
    print(f"  Characters: {len(form_config['characters'])}")
    return tool_id

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_from_json.py <json_file>")
        sys.exit(1)
    import_work(sys.argv[1])
