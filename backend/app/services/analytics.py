"""
Analytics service for user behavior tracking and insights
Tracks user interactions, content performance, and platform metrics
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class AnalyticsService:
    """
    Analytics service for tracking:
    - User behavior patterns
    - Content engagement metrics
    - Platform performance indicators
    - Conversion funnels
    """
    
    def __init__(self, mongo_client, redis_client):
        self.mongo = mongo_client
        self.redis = redis_client
    
    def track_event(self, event_type: str, user_id: Optional[int], event_data: Dict):
        """
        Track a user event for analytics
        Event types: page_view, tool_use, search, click, share, collect, etc.
        """
        event = {
            "eventType": event_type,
            "userId": user_id,
            "timestamp": datetime.utcnow(),
            "ipAddress": event_data.get("ipAddress"),
            "userAgent": event_data.get("userAgent"),
            "data": event_data
        }
        
        # Store in MongoDB for long-term analysis
        self.mongo["t_analytics_events"].insert_one(event)
        
        # Update real-time counters in Redis
        self._update_realtime_counters(event_type, user_id, event_data)
    
    def _update_realtime_counters(self, event_type: str, user_id: Optional[int], event_data: Dict):
        """Update real-time counters in Redis"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Daily event counters
        self.redis.incr(f"analytics:daily:{event_type}:{today}")
        self.redis.expire(f"analytics:daily:{event_type}:{today}", 86400 * 30)
        
        # Tool-specific counters
        if "toolId" in event_data:
            tool_id = event_data["toolId"]
            self.redis.incr(f"analytics:tool:{tool_id}:views")
            self.redis.incr(f"analytics:tool:{tool_id}:daily:{today}")
            self.redis.expire(f"analytics:tool:{tool_id}:daily:{today}", 86400 * 30)
        
        # User-specific counters
        if user_id:
            self.redis.incr(f"analytics:user:{user_id}:events")
    
    def get_tool_analytics(self, tool_id: int, days: int = 30) -> Dict:
        """
        Get analytics data for a specific tool
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Aggregate events from MongoDB
        pipeline = [
            {
                "$match": {
                    "eventType": {"$in": ["page_view", "tool_use"]},
                    "data.toolId": tool_id,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$eventType",
                    "count": {"$sum": 1},
                    "uniqueUsers": {"$addToSet": "$userId"}
                }
            }
        ]
        
        results = self.mongo["t_analytics_events"].aggregate(pipeline).to_list(None)
        
        analytics = {
            "toolId": tool_id,
            "period": f"{days} days",
            "totalViews": 0,
            "totalUses": 0,
            "uniqueUsers": 0,
            "dailyStats": []
        }
        
        for result in results:
            if result["_id"] == "page_view":
                analytics["totalViews"] = result["count"]
            elif result["_id"] == "tool_use":
                analytics["totalUses"] = result["count"]
            analytics["uniqueUsers"] = max(analytics["uniqueUsers"], len(result["uniqueUsers"]))
        
        # Get daily breakdown
        analytics["dailyStats"] = self._get_daily_tool_stats(tool_id, days)
        
        return analytics
    
    def _get_daily_tool_stats(self, tool_id: int, days: int) -> List[Dict]:
        """Get daily statistics for a tool"""
        daily_stats = []
        end_date = datetime.utcnow()
        
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            views = int(self.redis.get(f"analytics:tool:{tool_id}:daily:{date_str}") or 0)
            
            daily_stats.append({
                "date": date_str,
                "views": views
            })
        
        return reversed(daily_stats)
    
    def get_user_analytics(self, user_id: int, days: int = 30) -> Dict:
        """
        Get analytics data for a specific user
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "userId": user_id,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$eventType",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = self.mongo["t_analytics_events"].aggregate(pipeline).to_list(None)
        
        analytics = {
            "userId": user_id,
            "period": f"{days} days",
            "totalEvents": 0,
            "eventsByType": {}
        }
        
        for result in results:
            analytics["eventsByType"][result["_id"]] = result["count"]
            analytics["totalEvents"] += result["count"]
        
        # Get user's favorite categories
        analytics["topCategories"] = self._get_user_top_categories(user_id, days)
        
        return analytics
    
    def _get_user_top_categories(self, user_id: int, days: int) -> List[Dict]:
        """Get user's most interacted categories"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "userId": user_id,
                    "eventType": "tool_use",
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$lookup": {
                    "from": "t_ai_tool",
                    "localField": "data.toolId",
                    "foreignField": "id",
                    "as": "tool"
                }
            },
            {
                "$unwind": "$tool"
            },
            {
                "$group": {
                    "_id": "$tool.category_id",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 5
            }
        ]
        
        results = self.mongo["t_analytics_events"].aggregate(pipeline).to_list(None)
        
        return [
            {"categoryId": r["_id"], "count": r["count"]}
            for r in results
        ]
    
    def get_platform_analytics(self, days: int = 7) -> Dict:
        """
        Get platform-wide analytics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily active users
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                        "userId": "$userId"
                    }
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "dailyActiveUsers": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        dau_results = self.mongo["t_analytics_events"].aggregate(pipeline).to_list(None)
        
        # Get total events
        total_events = self.mongo["t_analytics_events"].count_documents({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        
        # Get unique users
        unique_users = self.mongo["t_analytics_events"].distinct(
            "userId",
            {"timestamp": {"$gte": start_date, "$lte": end_date}}
        )
        
        return {
            "period": f"{days} days",
            "totalEvents": total_events,
            "uniqueUsers": len(unique_users),
            "dailyActiveUsers": [
                {"date": r["_id"], "count": r["dailyActiveUsers"]}
                for r in dau_results
            ]
        }
    
    def get_trending_content(self, limit: int = 20) -> List[Dict]:
        """
        Get trending content based on recent analytics
        """
        # Get tools with most views in the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        pipeline = [
            {
                "$match": {
                    "eventType": "page_view",
                    "data.toolId": {"$exists": True},
                    "timestamp": {"$gte": seven_days_ago}
                }
            },
            {
                "$group": {
                    "_id": "$data.toolId",
                    "views": {"$sum": 1},
                    "uniqueUsers": {"$addToSet": "$userId"}
                }
            },
            {
                "$sort": {"views": -1}
            },
            {
                "$limit": limit
            }
        ]
        
        results = self.mongo["t_analytics_events"].aggregate(pipeline).to_list(None)
        
        return [
            {
                "toolId": r["_id"],
                "views": r["views"],
                "uniqueUsers": len(r["uniqueUsers"])
            }
            for r in results
        ]
