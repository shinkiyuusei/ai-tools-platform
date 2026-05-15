"""
Migrate existing genraton works to rich structured format using DeepSeek API.
Extracts characters, protagonist, world setting, game rules from existing data.
Run: python migrate_works_to_rich_format.py
"""
import json
import time
import pymysql


def get_mysql_conn():
    return pymysql.connect(
        host="127.0.0.1", port=3306,
        user="ai_user", password="ai_pass_123",
        database="ai_tools_platform", charset="utf8mb4"
    )


def call_deepseek(prompt: str) -> dict:
    """Call DeepSeek API to extract structured data."""
    import requests
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-v4-flash")

    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"]["content"]

    # Extract JSON from response
    start = content.find("{")
    end = content.rfind("}") + 1
    if start == -1 or end <= start:
        print(f"  WARNING: No JSON found in response")
        return {}
    return json.loads(content[start:end])


def build_extraction_prompt(name: str, desc: str, opening: str, system_prompt: str, author: str) -> str:
    return f"""请根据以下作品信息，提取并生成结构化的作品设定JSON。只返回JSON，不要其他内容。

作品名称：{name}
作品简介：{desc}
作者：{author}
开场白：{opening}
系统提示词：{system_prompt}

请按以下JSON格式提取（缺失的信息根据上下文合理填充，确实没有的字段留空字符串""）：

{{
  "detailedIntro": "面向玩家的详细介绍，200-500字，介绍角色、故事背景、版本信息等。不对AI展示。",
  "characters": [
    {{
      "name": "姓名",
      "occupation": "职业",
      "age": "年龄",
      "gender": "女",
      "appearance": "外貌描述--身高、发色、体型、穿着等",
      "personality": "角色性格--性格、爱好、性癖等",
      "speechTone": "角色语气--语气、口吻、说话方式等",
      "background": "背景设定--与主角关系、家境、情感经历、出身等"
    }}
  ],
  "protagonist": {{
    "name": "主人公名称",
    "description": "玩家扮演的角色设定",
    "motivation": "核心动机/目标"
  }},
  "worldSetting": {{
    "worldName": "世界名称",
    "eraTech": "时代背景与科技/魔法水平",
    "coreConflict": "核心冲突/主题",
    "toneAtmosphere": "整体基调与氛围",
    "mainPlot": "主线情节设定",
    "initialState": "初始剧情状态"
  }},
  "gameRules": "AI扮演角色时需遵守的规则。提炼自系统提示词。",
  "statusBar": "状态栏模板"
}}

注意：
1. 角色设定数组中应包含作品中所有主要角色，0到10个。
2. 主人公设定描述的是玩家扮演的角色，而非AI扮演的角色。
3. 如果原文是女性视角，请反转视角：原女性角色变为可攻略角色，原默认的男性交互对象变为主人公。
4. 每个角色的外貌、性格、语气、背景应详细且符合原始设定。
5. 严格按照JSON格式返回，不要添加注释或额外文字。"""


def migrate_works(dry_run=False, limit=None):
    """Migrate all works lacking rich structure."""
    conn = get_mysql_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT id, name, `desc`, form_config, use_desc
        FROM t_ai_tool WHERE status = 1
        ORDER BY id
    """)
    works = cursor.fetchall()

    # Filter to chat-type works that lack rich data
    targets = []
    for w in works:
        config = {}
        if w.get("form_config"):
            try:
                config = json.loads(w["form_config"])
            except (json.JSONDecodeError, TypeError):
                pass
        # Skip non-dict configs (e.g. form field arrays for tool-type entries)
        if not isinstance(config, dict):
            continue
        # Skip if already has rich data
        if config.get("characters") or config.get("detailedIntro"):
            continue
        # Only migrate chat-type works
        if config.get("type") == "chat":
            targets.append((w, config))

    if limit:
        targets = targets[:limit]

    print(f"Found {len(targets)} works to migrate (out of {len(works)} total)")

    for i, (work, config) in enumerate(targets):
        work_id = work["id"]
        name = work["name"]
        desc = work["desc"] or ""
        opening = config.get("opening", "")
        system_prompt = config.get("systemPrompt", desc)
        author = config.get("author", "")

        safe_name = name[:30].encode('ascii', errors='replace').decode('ascii')
        print(f"\n[{i+1}/{len(targets)}] Processing: {safe_name} (id={work_id})...")

        try:
            prompt = build_extraction_prompt(name, desc, opening, system_prompt, author)
            rich_data = call_deepseek(prompt)

            if not rich_data:
                print("  WARNING: Empty response, skipping")
                continue

            # Merge rich fields into config
            for key in ("detailedIntro", "characters", "protagonist", "worldSetting", "gameRules", "statusBar"):
                if key in rich_data:
                    config[key] = rich_data[key]

            if not dry_run:
                cursor.execute(
                    "UPDATE t_ai_tool SET form_config = %s WHERE id = %s",
                    (json.dumps(config, ensure_ascii=False), work_id)
                )
                conn.commit()
                print(f"  OK - Updated (id={work_id})")
                print(f"    Characters: {len(rich_data.get('characters', []))}")
                print(f"    Has protagonist: {bool(rich_data.get('protagonist'))}")
            else:
                print(f"  DRY RUN - Would update (id={work_id})")

        except Exception as e:
            print(f"  ERROR: {e}")
            time.sleep(5)
            continue

        time.sleep(0.5)  # Rate limit

    cursor.close()
    conn.close()
    print(f"\nDone! Processed {len(targets)} works.")


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    limit = None
    for arg in sys.argv:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
    migrate_works(dry_run=dry, limit=limit)
