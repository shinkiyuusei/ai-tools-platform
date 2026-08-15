"""
Monitoring API endpoints for health checks and metrics
"""
import logging

from flask import Blueprint, request

from ...services.monitoring import MonitoringService
from ...utils.mysql import get_mysql_connection
from ...utils.response import success_response

monitoring_bp = Blueprint("monitoring", __name__)


def get_monitoring_service():
    """Get monitoring service instance"""
    logger = logging.getLogger("monitoring")
    return MonitoringService(get_mysql_connection(), logger)


@monitoring_bp.get("/monitoring/health")
def health_check():
    """Comprehensive health check of all system components"""
    service = get_monitoring_service()
    health = service.check_health()
    return success_response(health)


@monitoring_bp.get("/monitoring/metrics")
def get_metrics():
    """Get performance metrics"""
    minutes = min(int(request.args.get("minutes", 5)), 60)
    service = get_monitoring_service()
    metrics = service.get_performance_metrics(minutes)
    return success_response(metrics)


@monitoring_bp.get("/monitoring/system")
def get_system_metrics():
    """Get system resource metrics"""
    service = get_monitoring_service()
    metrics = service.get_system_metrics()
    return success_response(metrics)


@monitoring_bp.get("/monitoring/error-rate")
def get_error_rate():
    """Get current error rate"""
    minutes = min(int(request.args.get("minutes", 5)), 60)
    service = get_monitoring_service()
    error_rate = service.get_error_rate(minutes)
    return success_response({
        "error_rate": error_rate,
        "period_minutes": minutes
    })
