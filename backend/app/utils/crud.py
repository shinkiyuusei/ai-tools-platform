import json

from .mysql import execute


def dynamic_update(table: str, field_map: dict, payload: dict, where_col: str, where_val):
    fields = []
    params = []
    for json_key, db_key in field_map.items():
        if json_key in payload and payload[json_key] is not None:
            fields.append(f"{db_key} = %s")
            params.append(payload[json_key])
    if not fields:
        from ..core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")
    params.append(where_val)
    execute(f"UPDATE {table} SET {', '.join(fields)} WHERE {where_col} = %s", tuple(params))
