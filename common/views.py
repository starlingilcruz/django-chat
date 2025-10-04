"""
Common views including health check
"""

import logging

from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from messaging.redis_stream import redis_stream_client

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    Checks PostgreSQL and Redis connectivity
    """
    checks = {
        "postgres": False,
        "redis": False,
    }
    overall_healthy = True

    # Check PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["postgres"] = True
    except Exception as e:
        logger.error("PostgreSQL health check failed", extra={"error": str(e)})
        overall_healthy = False

    # Check Redis
    try:
        checks["redis"] = redis_stream_client.ping_redis()
        if not checks["redis"]:
            overall_healthy = False
    except Exception as e:
        logger.error("Redis health check failed", extra={"error": str(e)})
        overall_healthy = False

    response_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JsonResponse(
        {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": checks,
        },
        status=response_status,
    )
