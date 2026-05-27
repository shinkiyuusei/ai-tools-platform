"""
Monitoring service for application health and performance tracking
Provides metrics collection, health checks, and alerting
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MonitoringService:
    """
    Monitoring service for:
    - Application health checks
    - Performance metrics
    - Error tracking
    - Resource usage monitoring
    """
    
    def __init__(self, redis_client, mysql_client, logger):
        self.redis = redis_client
        self.mysql = mysql_client
        self.logger = logger
    
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict] = None):
        """Record a metric for monitoring"""
        timestamp = datetime.utcnow().isoformat()
        metric_data = {
            "name": metric_name,
            "value": value,
            "timestamp": timestamp,
            "tags": tags or {}
        }
        
        # Store in Redis for recent metrics
        self.redis.lpush(f"metrics:{metric_name}", str(metric_data))
        self.redis.ltrim(f"metrics:{metric_name}", 0, 9999)
        self.redis.expire(f"metrics:{metric_name}", 3600)
    
    def check_health(self) -> Dict:
        """
        Perform comprehensive health check
        Returns status of all system components
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check Redis
        try:
            self.redis.ping()
            health_status["checks"]["redis"] = {"status": "healthy", "latency_ms": self._check_redis_latency()}
        except Exception as e:
            health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check MySQL
        try:
            self.mysql.ping(reconnect=True)
            health_status["checks"]["mysql"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["mysql"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        return health_status
    
    def _check_redis_latency(self) -> float:
        """Check Redis connection latency in milliseconds"""
        start = datetime.utcnow()
        self.redis.ping()
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        return round(latency, 2)
    
    def get_performance_metrics(self, minutes: int = 5) -> Dict:
        """Get performance metrics for the specified time period"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        metrics = {
            "period": f"{minutes} minutes",
            "timestamp": end_time.isoformat(),
            "request_count": 0,
            "error_count": 0,
            "avg_response_time": 0,
            "p95_response_time": 0,
            "p99_response_time": 0
        }
        
        # Get request metrics from Redis
        request_times = []
        for i in range(minutes):
            minute_key = f"requests:minute:{(end_time - timedelta(minutes=i)).strftime('%Y%m%d%H%M')}"
            data = self.redis.get(minute_key)
            if data:
                import json
                minute_data = json.loads(data)
                metrics["request_count"] += minute_data.get("count", 0)
                metrics["error_count"] += minute_data.get("errors", 0)
                request_times.extend(minute_data.get("response_times", []))
        
        # Calculate percentiles
        if request_times:
            request_times.sort()
            metrics["avg_response_time"] = sum(request_times) / len(request_times)
            metrics["p95_response_time"] = request_times[int(len(request_times) * 0.95)]
            metrics["p99_response_time"] = request_times[int(len(request_times) * 0.99)]
        
        return metrics
    
    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """Record a request for monitoring"""
        minute_key = f"requests:minute:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        
        import json
        current_data = self.redis.get(minute_key)
        if current_data:
            data = json.loads(current_data)
        else:
            data = {"count": 0, "errors": 0, "response_times": []}
        
        data["count"] += 1
        if status_code >= 400:
            data["errors"] += 1
        data["response_times"].append(response_time)
        
        # Keep only last 100 response times per minute
        if len(data["response_times"]) > 100:
            data["response_times"] = data["response_times"][-100:]
        
        self.redis.setex(minute_key, 3600, json.dumps(data))
    
    def get_error_rate(self, minutes: int = 5) -> float:
        """Get error rate for the specified time period"""
        metrics = self.get_performance_metrics(minutes)
        if metrics["request_count"] > 0:
            return (metrics["error_count"] / metrics["request_count"]) * 100
        return 0.0
    
    def alert_if_high_error_rate(self, threshold: float = 5.0):
        """Alert if error rate exceeds threshold"""
        error_rate = self.get_error_rate(5)
        if error_rate > threshold:
            self.logger.error(
                "High error rate detected",
                error_rate=error_rate,
                threshold=threshold
            )
            # TODO: Send alert notification (email, Slack, etc.)
    
    def get_system_metrics(self) -> Dict:
        """Get system resource metrics"""
        import psutil
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids())
        }
