"""
Analytics service for user behavior tracking and insights.
Pure Redis implementation — no MongoDB dependency.
"""
import json
import uuid
from datetime import datetime, timedelta


class AnalyticsService:

    def __init__(self, redis_client):
        self.redis = redis_client

    def track_event(self, event_type: str, user_id: int | None, event_data: dict):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        event = {
            "id": uuid.uuid4().hex,
            "eventType": event_type,
            "userId": user_id or 0,
            "timestamp": datetime.utcnow().isoformat(),
            "ipAddress": event_data.get("ipAddress", ""),
            "userAgent": event_data.get("userAgent", ""),
        }

        # Store event in Redis list (keep last 10k events)
        key = f"analytics:events:{today}"
        self.redis.lpush(key, json.dumps(event, ensure_ascii=False))
        self.redis.ltrim(key, 0, 9999)
        self.redis.expire(key, 86400 * 31)

        # Daily counters
        self.redis.incr(f"analytics:daily:{event_type}:{today}")
        self.redis.expire(f"analytics:daily:{event_type}:{today}", 86400 * 31)

        # Daily active users
        if user_id:
            self.redis.sadd(f"analytics:dau:{today}", str(user_id))
            self.redis.expire(f"analytics:dau:{today}", 86400 * 31)
            self.redis.hincrby(f"analytics:user:{user_id}:counters", event_type, 1)

    def get_user_analytics(self, user_id: int, days: int = 30) -> dict:
        end_date = datetime.utcnow()
        counters = self.redis.hgetall(f"analytics:user:{user_id}:counters")

        total = sum(int(v) for v in (counters or {}).values())
        return {
            "userId": user_id,
            "period": f"{days} days",
            "totalEvents": total,
            "eventsByType": {k: int(v) for k, v in (counters or {}).items()},
        }

    def get_platform_analytics(self, days: int = 7) -> dict:
        end_date = datetime.utcnow()

        total_events = 0
        unique_users = set()
        daily_active_users = []

        for i in range(days):
            d = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            dau = self.redis.scard(f"analytics:dau:{d}") or 0
            daily_active_users.append({"date": d, "count": int(dau)})

            # Aggregate event counts for this day
            keys = self.redis.keys(f"analytics:daily:*:{d}")
            for k in keys:
                total_events += int(self.redis.get(k) or 0)

            members = self.redis.smembers(f"analytics:dau:{d}")
            unique_users.update(members)

        daily_active_users.reverse()

        return {
            "period": f"{days} days",
            "totalEvents": total_events,
            "uniqueUsers": len(unique_users),
            "dailyActiveUsers": daily_active_users,
        }
