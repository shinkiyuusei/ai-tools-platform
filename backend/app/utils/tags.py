def resolve_tag_names(items):
    """Batch-resolve tag IDs to tag names for a list of item dicts.
    Handles both numeric IDs (1,2,3) and text tags.
    """
    if not items:
        return items
    from .mysql import query_all

    all_tag_ids = set()
    for item in items:
        raw = item.get("tagIds", "")
        if raw:
            for tid in raw.split(","):
                tid = tid.strip()
                if tid and tid.isdigit():
                    all_tag_ids.add(int(tid))
    id_to_name = {}
    if all_tag_ids:
        placeholders = ",".join(["%s"] * len(all_tag_ids))
        tag_rows = query_all(
            f"SELECT id, name FROM t_tag WHERE id IN ({placeholders})",
            tuple(all_tag_ids),
        )
        id_to_name = {row["id"]: row["name"] for row in tag_rows}
    for item in items:
        raw = item.get("tagIds", "")
        tags = []
        seen = set()
        if raw:
            for tid in raw.split(","):
                tid = tid.strip()
                if not tid:
                    continue
                if tid.isdigit():
                    tag_id = int(tid)
                    if tag_id in id_to_name and tag_id not in seen:
                        tags.append({"id": tag_id, "name": id_to_name[tag_id]})
                        seen.add(tag_id)
                else:
                    if tid not in seen:
                        pseudo_id = abs(hash(tid)) % 1000 + 100
                        tags.append({"id": pseudo_id, "name": tid})
                        seen.add(tid)
        item["tags"] = tags
    return items
