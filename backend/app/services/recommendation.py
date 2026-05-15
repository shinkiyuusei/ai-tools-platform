"""
Recommendation engine service for personalized content discovery
Implements collaborative filtering, content-based filtering, and trending algorithms
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math


class RecommendationEngine:
    """
    Recommendation engine combining multiple algorithms:
    - Collaborative filtering (user-user similarity)
    - Content-based filtering (item-item similarity)
    - Trending/popularity-based recommendations
    - Time-decay scoring
    """
    
    def __init__(self, mysql_client, mongo_client, redis_client, cache_service=None):
        self.mysql = mysql_client
        self.mongo = mongo_client
        self.redis = redis_client
        self.cache = cache_service
    
    def get_personalized_recommendations(
        self, 
        user_id: int, 
        limit: int = 20,
        category_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get personalized recommendations for a user
        Combines collaborative filtering, content-based filtering, and trending
        """
        # Check cache first
        from .cache import generate_recommendation_cache_key
        cache_key = generate_recommendation_cache_key(user_id, category_id)
        
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached[:limit]
        
        # Get recommendations from multiple sources
        collaborative_scores = self._collaborative_filtering(user_id, category_id)
        content_scores = self._content_based_filtering(user_id, category_id)
        trending_scores = self._get_trending_score(category_id)
        
        # Combine scores with weights
        final_scores = {}
        for item_id in set(list(collaborative_scores.keys()) + 
                          list(content_scores.keys()) + 
                          list(trending_scores.keys())):
            score = (
                collaborative_scores.get(item_id, 0) * 0.4 +
                content_scores.get(item_id, 0) * 0.4 +
                trending_scores.get(item_id, 0) * 0.2
            )
            final_scores[item_id] = score
        
        # Sort by score and get top N
        sorted_items = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        top_item_ids = [item_id for item_id, _ in sorted_items[:limit]]
        
        # Fetch item details
        recommendations = self._fetch_items_details(top_item_ids)
        
        # Cache for 5 minutes
        if self.cache:
            self.cache.set(cache_key, recommendations, 300)
        
        return recommendations
    
    def _collaborative_filtering(
        self, 
        user_id: int, 
        category_id: Optional[int] = None
    ) -> Dict[int, float]:
        """
        Collaborative filtering: find similar users and recommend what they liked
        """
        # Get user's interaction history
        user_interactions = self.mongo["t_generate_record"].find(
            {"userId": user_id}
        ).to_list(None)
        
        if not user_interactions:
            return {}
        
        # Get tools user interacted with
        user_tool_ids = set(doc["toolId"] for doc in user_interactions)
        
        # Find users with similar tool preferences (simple Jaccard similarity)
        similar_users = self._find_similar_users(user_id, user_tool_ids)
        
        # Get tools liked by similar users
        recommendations = {}
        for similar_user in similar_users[:50]:  # Top 50 similar users
            similar_user_tools = self.mongo["t_generate_record"].find(
                {"userId": similar_user["userId"]}
            ).to_list(None)
            
            for doc in similar_user_tools:
                tool_id = doc["toolId"]
                if tool_id not in user_tool_ids:
                    recommendations[tool_id] = recommendations.get(tool_id, 0) + similar_user["similarity"]
        
        return recommendations
    
    def _find_similar_users(
        self, 
        user_id: int, 
        user_tool_ids: set
    ) -> List[Dict]:
        """
        Find users with similar tool preferences using Jaccard similarity
        """
        # Get all users who interacted with the same tools
        similar_users = []
        
        # Aggregate tool usage by user
        pipeline = [
            {"$match": {"toolId": {"$in": list(user_tool_ids)}}},
            {"$group": {
                "_id": "$userId",
                "toolIds": {"$addToSet": "$toolId"}
            }},
            {"$match": {"_id": {"$ne": user_id}}}
        ]
        
        results = self.mongo["t_generate_record"].aggregate(pipeline).to_list(None)
        
        for result in results:
            other_user_id = result["_id"]
            other_tool_ids = set(result["toolIds"])
            
            # Jaccard similarity
            intersection = len(user_tool_ids & other_tool_ids)
            union = len(user_tool_ids | other_tool_ids)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.1:  # Minimum similarity threshold
                similar_users.append({
                    "userId": other_user_id,
                    "similarity": similarity
                })
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_users
    
    def _content_based_filtering(
        self, 
        user_id: int, 
        category_id: Optional[int] = None
    ) -> Dict[int, float]:
        """
        Content-based filtering: recommend items similar to what user liked
        """
        # Get user's preferred categories from interaction history
        user_interactions = self.mongo["t_generate_record"].find(
            {"userId": user_id}
        ).to_list(None)
        
        if not user_interactions:
            return {}
        
        # Count category preferences
        category_counts = {}
        for doc in user_interactions:
            tool_id = doc["toolId"]
            tool = self._get_tool_by_id(tool_id)
            if tool:
                cat_id = tool.get("category_id")
                if cat_id:
                    category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
        
        if not category_counts:
            return {}
        
        # Recommend tools from preferred categories
        recommendations = {}
        for cat_id, count in category_counts.items():
            if category_id and cat_id != category_id:
                continue
            
            # Get popular tools in this category
            tools = self._get_tools_by_category(cat_id)
            for tool in tools:
                recommendations[tool["id"]] = recommendations.get(tool["id"], 0) + count
        
        return recommendations
    
    def _get_trending_score(self, category_id: Optional[int] = None) -> Dict[int, float]:
        """
        Calculate trending score based on recent activity with time decay
        """
        # Get tools with recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        pipeline = [
            {"$match": {"createTime": {"$gte": seven_days_ago}}},
            {"$group": {
                "_id": "$toolId",
                "count": {"$sum": 1}
            }}
        ]
        
        results = self.mongo["t_generate_record"].aggregate(pipeline).to_list(None)
        
        trending_scores = {}
        for result in results:
            tool_id = result["_id"]
            count = result["count"]
            
            # Apply time decay (more recent = higher score)
            trending_scores[tool_id] = math.log(count + 1) * 1.5
        
        return trending_scores
    
    def _get_tool_by_id(self, tool_id: int) -> Optional[Dict]:
        """Get tool details by ID"""
        from ..utils.mysql import query_one
        return query_one(
            "SELECT id, name, category_id FROM t_ai_tool WHERE id = %s AND status = 1",
            (tool_id,)
        )
    
    def _get_tools_by_category(self, category_id: int) -> List[Dict]:
        """Get tools by category"""
        from ..utils.mysql import query_all
        return query_all(
            "SELECT id, name FROM t_ai_tool WHERE category_id = %s AND status = 1",
            (category_id,)
        )
    
    def _fetch_items_details(self, item_ids: List[int]) -> List[Dict]:
        """Fetch item details for recommendation results"""
        if not item_ids:
            return []
        
        from ..utils.mysql import query_all
        placeholders = ",".join(["%s"] * len(item_ids))
        items = query_all(
            f"SELECT id, name, icon, `desc`, use_count AS useCount, is_free AS isFree, "
            f"category_id AS categoryId FROM t_ai_tool WHERE id IN ({placeholders}) AND status = 1",
            tuple(item_ids)
        )
        return items
    
    def get_ranking_by_period(
        self, 
        period: str = "daily",
        category_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get ranking by time period (daily, weekly, monthly, total)
        """
        from .cache import generate_ranking_cache_key
        cache_key = generate_ranking_cache_key(period, category_id)
        
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached[:limit]
        
        # Calculate time range
        now = datetime.now()
        if period == "daily":
            start_time = now - timedelta(days=1)
        elif period == "weekly":
            start_time = now - timedelta(weeks=1)
        elif period == "monthly":
            start_time = now - timedelta(days=30)
        else:  # total
            start_time = None
        
        # Build query
        if start_time:
            # Time-based ranking
            pipeline = [
                {"$match": {"createTime": {"$gte": start_time}}},
                {"$group": {
                    "_id": "$toolId",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            results = self.mongo["t_generate_record"].aggregate(pipeline).to_list(None)
            tool_ids = [r["_id"] for r in results]
        else:
            # Total ranking based on use_count
            where_clause = "status = 1"
            params = []
            if category_id:
                where_clause += " AND category_id = %s"
                params.append(category_id)
            
            from ..utils.mysql import query_all
            items = query_all(
                f"SELECT id FROM t_ai_tool WHERE {where_clause} ORDER BY use_count DESC LIMIT %s",
                tuple(params + [limit])
            )
            tool_ids = [item["id"] for item in items]
        
        # Fetch item details
        ranking = self._fetch_items_details(tool_ids)
        
        # Cache for 10 minutes
        if self.cache:
            self.cache.set(cache_key, ranking, 600)
        
        return ranking
