"""
Batch enhance work cards with AI-generated openings, NPCs, and protagonist.

Usage:
    python -m backend.enhance_works --test          # 3 works only
    python -m backend.enhance_works --all            # all 103 works
    python -m backend.enhance_works --ids 1 2 3      # specific IDs
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pymysql
import requests
from dotenv import load_dotenv

# Load env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_DB_PORT", "3306")),
    "user": os.getenv("MYSQL_DB_USER", "ai_user"),
    "password": os.getenv("MYSQL_DB_PASSWORD", "ai_pass_123"),
    "database": os.getenv("MYSQL_DB_NAME", "ai_tools_platform"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

DEEPSEEK_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-v4-flash")

SYSTEM_PROMPT = """你是一个 NSFW 互动小说编辑专家。你需要根据作品信息，为作品卡生成高质量的开场白、NPC角色和主角设定。

输出格式必须是严格的 JSON，不要输出任何其他内容：

```json
{
  "openings": [
    {"label": "场景名称（8字以内）", "text": "详细的开场白叙事（150-400字，第一人称沉浸式）"}
  ],
  "characters": [
    {
      "name": "角色名",
      "gender": "女/男",
      "age": "年龄数字",
      "occupation": "职业身份",
      "personality": "性格描述（20-50字）",
      "appearance": "外貌描述（20-50字）",
      "speechTone": "语气风格（10-20字）"
    }
  ],
  "protagonist": {
    "name": "主人公名",
    "description": "主人公设定（20-50字）",
    "motivation": "核心动机（10-30字）"
  }
}
```

规则：
1. openings: 保留原有的开场白（label设为"原版"），额外生成1-2个新场景入口。每个开场白应该是不同场景/时间/氛围，给用户多入口选择。开场白用第一人称沉浸式叙事。
2. characters: 提取作品中所有可视角切换的NPC角色（2-5个），每个人设鲜明、有记忆点。没有明确角色就从剧情场景中合理推断创建。
3. protagonist: 设定主人公（即玩家的角色），名字、简短描述和核心动机。
4. 所有文本禁止使用"你"，用"我"代替。这是第一人称互动小说。"""


def get_db():
    return pymysql.connect(**DB_CONFIG)


def call_ai(work_info: str) -> dict:
    """Call DeepSeek Flash with the work info, return parsed JSON."""
    resp = requests.post(
        f"{DEEPSEEK_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": work_info},
            ],
            "max_tokens": 4096,
            "temperature": 0.8,
        },
        timeout=120,
    )
    resp.raise_for_status()
    body = resp.json()
    content = body["choices"][0]["message"]["content"].strip()

    # Extract JSON from markdown code fence if present
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()

    return json.loads(content)


def build_work_info(work: dict) -> str:
    """Build a text prompt describing the work for the AI."""
    role_config = {}
    if work.get("role_config"):
        try:
            role_config = json.loads(work["role_config"]) if isinstance(work["role_config"], str) else work["role_config"]
        except (json.JSONDecodeError, TypeError):
            pass

    openings = []
    if work.get("openings"):
        try:
            openings = json.loads(work["openings"]) if isinstance(work["openings"], str) else work["openings"]
        except (json.JSONDecodeError, TypeError):
            pass

    parts = [
        f"作品名称：{work['name']}",
        f"作品简介：{work.get('desc', '')}",
        f"详细描述：{work.get('summary', '')}",
    ]

    if openings:
        parts.append(f"现有开场白：{openings[0].get('text', '')[:500]}")

    ws = role_config.get("worldview_setting", {})
    if ws:
        parts.append(f"世界观：{ws.get('era_background', '')} / {ws.get('overall_atmosphere', '')}")

    return "\n\n".join(parts)


def update_work(db, work_id: int, data: dict):
    """Update a single work's openings and role_config in the database."""
    cur = db.cursor()

    # Read current role_config
    cur.execute("SELECT role_config FROM t_work_card WHERE id = %s", (work_id,))
    row = cur.fetchone()
    role_config = {}
    if row and row.get("role_config"):
        try:
            role_config = json.loads(row["role_config"]) if isinstance(row["role_config"], str) else row["role_config"]
        except (json.JSONDecodeError, TypeError):
            role_config = {}

    # Update openings
    new_openings = json.dumps(data["openings"], ensure_ascii=False)

    # Update role_config
    role_config["npc_settings"] = data.get("characters", [])
    role_config["protagonist_setting"] = {
        "name": data.get("protagonist", {}).get("name", ""),
        "setting": data.get("protagonist", {}).get("description", ""),
        "core_motivation": data.get("protagonist", {}).get("motivation", ""),
    }

    cur.execute(
        "UPDATE t_work_card SET openings = %s, role_config = %s WHERE id = %s",
        (new_openings, json.dumps(role_config, ensure_ascii=False), work_id),
    )
    db.commit()

    print(f"  ✅ open={len(data['openings'])} NPCs={len(data.get('characters', []))} "
          f"主角={data.get('protagonist', {}).get('name', '?')}")


def process_works(work_ids: list, dry_run: bool = False):
    """Process a list of work IDs."""
    db = get_db()
    failed = []
    success = 0

    print(f"\n{'[DRY RUN] ' if dry_run else ''}处理 {len(work_ids)} 个作品\n")

    for i, wid in enumerate(work_ids, 1):
        cur = db.cursor()
        cur.execute(
            "SELECT id, name, `desc`, summary, openings, role_config FROM t_work_card WHERE id = %s",
            (wid,),
        )
        work = cur.fetchone()
        if not work:
            print(f"[{i}/{len(work_ids)}] ID={wid} ❌ 不存在")
            failed.append((wid, "不存在"))
            continue

        name = work["name"]
        print(f"[{i}/{len(work_ids)}] {name} ...", end=" ", flush=True)

        try:
            work_info = build_work_info(work)
            result = call_ai(work_info)

            if dry_run:
                print(f"\n  生成开场白: {len(result.get('openings', []))} 条")
                for op in result.get("openings", []):
                    print(f"    [{op['label']}] {op['text'][:80]}...")
                print(f"  角色: {[c['name'] for c in result.get('characters', [])]}")
                print(f"  主角: {result.get('protagonist', {}).get('name', '?')}")
                print("---")
            else:
                update_work(db, wid, result)

            success += 1
            time.sleep(1)  # Rate limit: 1 req/s

        except Exception as e:
            print(f"❌ {e}")
            failed.append((wid, str(e)))

    db.close()

    print(f"\n{'='*50}")
    print(f"成功: {success}  失败: {len(failed)}")
    if failed:
        print("失败列表:")
        for wid, err in failed:
            print(f"  ID={wid}: {err}")


def main():
    parser = argparse.ArgumentParser(description="Enhance work cards with AI")
    parser.add_argument("--test", action="store_true", help="Test with first 3 works")
    parser.add_argument("--all", action="store_true", help="Process all works")
    parser.add_argument("--ids", type=int, nargs="+", help="Process specific work IDs")
    parser.add_argument("--dry-run", action="store_true", help="Print results without saving to DB")
    args = parser.parse_args()

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM t_work_card WHERE status IN (1,2) ORDER BY id")
    all_ids = [r["id"] for r in cur.fetchall()]
    db.close()

    if args.test:
        work_ids = all_ids[:3]
    elif args.ids:
        work_ids = args.ids
    elif args.all:
        work_ids = all_ids
    else:
        parser.print_help()
        return

    process_works(work_ids, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
