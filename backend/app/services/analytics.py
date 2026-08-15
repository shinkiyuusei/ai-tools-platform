"""
Analytics service — MySQL-backed event tracking and aggregation.
"""

import json
from datetime import datetime, timedelta

from ..utils.mysql import execute, query_all, query_one


class AnalyticsService:

    def track_event(self, event_type: str, user_id: int | None, event_data: dict):
        event_data = dict(event_data or {})
        execute(
            "INSERT INTO t_analytics_event "
            "(event_type, user_id, event_data, ip_address, user_agent) "
            "VALUES (%s,%s,%s,%s,%s)",
            (
                event_type,
                user_id or 0,
                json.dumps(event_data, ensure_ascii=False),
                event_data.get("ipAddress", ""),
                event_data.get("userAgent", ""),
            ),
        )

    def get_user_analytics(self, user_id: int, days: int = 30) -> dict:
        rows = query_all(
            "SELECT event_type, COUNT(*) AS cnt FROM t_analytics_event "
            "WHERE user_id = %s AND created_at >= NOW() - INTERVAL %s DAY "
            "GROUP BY event_type",
            (user_id, days),
        )
        events_by_type = {r["event_type"]: int(r["cnt"]) for r in (rows or [])}
        return {
            "userId": user_id,
            "period": f"{days} days",
            "totalEvents": sum(events_by_type.values()),
            "eventsByType": events_by_type,
        }

    def get_platform_analytics(self, days: int = 7) -> dict:
        total_row = query_one(
            "SELECT COUNT(*) AS cnt FROM t_analytics_event "
            "WHERE created_at >= NOW() - INTERVAL %s DAY",
            (days,),
        )
        unique_row = query_one(
            "SELECT COUNT(DISTINCT user_id) AS cnt FROM t_analytics_event "
            "WHERE user_id != 0 AND created_at >= NOW() - INTERVAL %s DAY",
            (days,),
        )
        daily_rows = query_all(
            "SELECT DATE(created_at) AS d, COUNT(DISTINCT user_id) AS cnt "
            "FROM t_analytics_event WHERE user_id != 0 "
            "AND created_at >= NOW() - INTERVAL %s DAY "
            "GROUP BY DATE(created_at) ORDER BY d",
            (days,),
        )
        by_date = {str(r["d"]): int(r["cnt"]) for r in (daily_rows or [])}

        today = datetime.utcnow().date()
        daily_active_users = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            daily_active_users.append({
                "date": d.isoformat(),
                "count": by_date.get(d.isoformat(), 0),
            })

        return {
            "period": f"{days} days",
            "totalEvents": int(total_row["cnt"]) if total_row else 0,
            "uniqueUsers": int(unique_row["cnt"]) if unique_row else 0,
            "dailyActiveUsers": daily_active_users,
        }
