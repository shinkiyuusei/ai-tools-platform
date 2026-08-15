"""
Monitoring service for application health and performance tracking.

Request metrics live in a process-local ring buffer (single-process
deployment), while health checks verify the MySQL connection.
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Dict


_METRICS = deque(maxlen=10000)
_REQUEST_MINUTES: Dict[str, dict] = {}


class MonitoringService:

    def __init__(self, mysql_client, logger):
        self.mysql = mysql_client
        self.logger = logger

    def record_metric(self, metric_name: str, value: float, tags: dict = None):
        _METRICS.append({
            "name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {},
        })

    def check_health(self) -> dict:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }
        try:
            self.mysql.ping(reconnect=True)
            health_status["checks"]["mysql"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["mysql"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        return health_status

    def get_performance_metrics(self, minutes: int = 5) -> dict:
        end_time = datetime.utcnow()
        request_count = 0
        error_count = 0
        request_times = []

        for i in range(minutes):
            minute_key = (end_time - timedelta(minutes=i)).strftime("%Y%m%d%H%M")
            data = _REQUEST_MINUTES.get(minute_key)
            if not data:
                continue
            request_count += data.get("count", 0)
            error_count += data.get("errors", 0)
            request_times.extend(data.get("response_times", []))

        metrics = {
            "period": f"{minutes} minutes",
            "timestamp": end_time.isoformat(),
            "request_count": request_count,
            "error_count": error_count,
            "avg_response_time": 0,
            "p95_response_time": 0,
            "p99_response_time": 0,
        }
        if request_times:
            request_times.sort()
            metrics["avg_response_time"] = round(sum(request_times) / len(request_times), 2)
            metrics["p95_response_time"] = request_times[min(len(request_times) - 1, int(len(request_times) * 0.95))]
            metrics["p99_response_time"] = request_times[min(len(request_times) - 1, int(len(request_times) * 0.99))]
        return metrics

    def record_request(self, endpoint: str, response_time: float, status_code: int):
        minute_key = datetime.utcnow().strftime("%Y%m%d%H%M")
        data = _REQUEST_MINUTES.setdefault(
            minute_key, {"count": 0, "errors": 0, "response_times": []}
        )
        data["count"] += 1
        if status_code >= 400:
            data["errors"] += 1
        times = data["response_times"]
        times.append(response_time)
        if len(times) > 100:
            del times[:-100]

        # Prune stale minutes so the dict does not grow forever.
        cutoff = (datetime.utcnow() - timedelta(hours=2)).strftime("%Y%m%d%H%M")
        for key in [k for k in _REQUEST_MINUTES if k < cutoff]:
            _REQUEST_MINUTES.pop(key, None)

    def get_error_rate(self, minutes: int = 5) -> float:
        metrics = self.get_performance_metrics(minutes)
        if metrics["request_count"] > 0:
            return round((metrics["error_count"] / metrics["request_count"]) * 100, 2)
        return 0.0

    def alert_if_high_error_rate(self, threshold: float = 5.0):
        error_rate = self.get_error_rate(5)
        if error_rate > threshold:
            self.logger.error(
                "High error rate detected",
                error_rate=error_rate,
                threshold=threshold,
            )
            # TODO: Send alert notification (email, Slack, etc.)

    def get_system_metrics(self) -> dict:
        import psutil

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids()),
        }
