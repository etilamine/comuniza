"""
Performance API endpoints for Comuniza dashboard.
Provides real-time performance metrics and analytics.
"""

from django.http import JsonResponse
from django.db.models import Count, Avg, Min, Max, Q
from django.utils.decorators import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta

from .models import (
    CacheMetrics, DatabaseQueryMetrics, RequestPerformanceMetrics,
    UserSessionMetrics, PerformanceAlert, PerformanceSummary
)

@csrf_exempt
def cache_metrics_api(request):
    """Real-time cache performance metrics."""
    
    # Get metrics from ultra cache
    from apps.core.ultra_cache import get_ultimate_cache
    current_metrics = get_ultimate_cache().get_metrics()
    
    # Get recent cache metrics from database
    recent_metrics = CacheMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).aggregate(
        avg_response_time=Avg('response_time_ms'),
        hit_rate=Avg('hit_rate'),
        total_requests=Count('id'),
        hit_count=Count('hit_count'),
        miss_count=Count('miss_count')
    )
    
    return JsonResponse({
        'current': current_metrics,
        'last_24h': recent_metrics,
        'status': 'active'
    })


@csrf_exempt
def database_performance_api(request):
    """Database query performance metrics."""
    
    # Get recent database performance
    recent_db_metrics = DatabaseQueryMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).annotate(
        avg_execution_time=Avg('execution_time_ms'),
        slow_queries=Count('id', filter=Q(execution_time_ms__gt=1000)),
        total_queries=Count('id')
    ).order_by('-timestamp')[:10]
    
    # Aggregate by query type
    query_performance = DatabaseQueryMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).values('query_type').annotate(
        avg_time=Avg('execution_time_ms'),
        count=Count('id'),
        max_time=Max('execution_time_ms')
    )
    
    return JsonResponse({
        'recent_slow_queries': list(recent_db_metrics),
        'query_performance_by_type': list(query_performance),
        'status': 'active'
    })


@csrf_exempt
def request_performance_api(request):
    """HTTP request performance metrics."""
    
    # Get recent request performance
    recent_requests = RequestPerformanceMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=30)
    ).order_by('-timestamp')[:100]
    
    # Aggregate by endpoint
    endpoint_performance = RequestPerformanceMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).values('endpoint').annotate(
        avg_response_time=Avg('response_time_ms'),
        request_count=Count('id'),
        error_rate=Avg('status_code', filter=Q(status_code__gte=400))
    ).order_by('-avg_response_time')[:20]
    
    return JsonResponse({
        'recent_requests': list(recent_requests),
        'endpoint_performance': list(endpoint_performance),
        'status': 'active'
    })


@csrf_exempt
def user_session_metrics_api(request):
    """User session and experience metrics."""
    
    # Get recent user sessions
    recent_sessions = UserSessionMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=2)
    ).order_by('-timestamp')[:50]
    
    # Aggregate user experience metrics
    user_experience = UserSessionMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).aggregate(
        avg_response_time=Avg('avg_response_time_ms'),
        avg_time_on_site=Avg('time_on_site_seconds'),
        total_sessions=Count('id'),
        bounce_rate=Avg('bounce_rate'),
        cache_hit_rate=Avg('cache_hits')
    )
    
    return JsonResponse({
        'recent_sessions': list(recent_sessions),
        'user_experience': user_experience,
        'status': 'active'
    })


@csrf_exempt
def alerts_api(request):
    """Active performance alerts."""
    
    active_alerts = PerformanceAlert.objects.filter(
        is_active=True
    ).order_by('-timestamp')[:20]
    
    recent_resolved = PerformanceAlert.objects.filter(
        resolved_at__isnull=False
    ).order_by('-resolved_at')[:10]
    
    return JsonResponse({
        'active_alerts': list(active_alerts),
        'recent_resolved': list(recent_resolved),
        'status': 'active'
    })


@csrf_exempt
def summary_api(request):
    """Performance summary and trends."""
    
    # Get performance summaries
    period_type = request.GET.get('period', 'HOURLY')
    
    if period_type == 'HOURLY':
        period_start = timezone.now() - timedelta(hours=24)
    elif period_type == 'DAILY':
        period_start = timezone.now() - timedelta(days=1)
    elif period_type == 'WEEKLY':
        period_start = timezone.now() - timedelta(days=7)
    else:
        period_start = timezone.now() - timedelta(hours=6)
    
    summaries = PerformanceSummary.objects.filter(
        period_start__gte=period_start
    ).order_by('-timestamp')[:10]
    
    return JsonResponse({
        'summaries': list(summaries),
        'period_type': period_type,
        'status': 'active'
    })


@csrf_exempt
def performance_health_api(request):
    """Overall system performance health score."""
    
    # Get latest cache metrics
    from apps.core.ultra_cache import get_ultimate_cache
    current_metrics = get_ultimate_cache().get_metrics()
    
    # Get recent performance averages
    recent_cache = CacheMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=5)
    ).aggregate(
        avg_hit_rate=Avg('hit_rate'),
        avg_response_time=Avg('response_time_ms')
    )
    
    recent_db = DatabaseQueryMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=5)
    ).aggregate(
        avg_execution_time=Avg('execution_time_ms'),
        slow_query_count=Count('id', filter=Q(execution_time_ms__gt=1000))
    )
    
    recent_requests = RequestPerformanceMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=5)
    ).aggregate(
        avg_response_time=Avg('response_time_ms'),
        error_rate=Avg('status_code', filter=Q(status_code__gte=400))
    )
    
    # Calculate health score (0-100)
    cache_health = min(100, current_metrics.get('hit_rate', 0) * 100)  # Cache hit rate
    db_health = max(0, 100 - (recent_db['slow_query_count'] / max(1, recent_db['total_queries']) * 100))  # Database health
    response_health = max(0, 100 - (recent_requests['error_rate'] * 100))  # Response health
    
    overall_health = (cache_health + db_health + response_health) / 3
    
    health_status = 'excellent' if overall_health >= 90 else \
                  'good' if overall_health >= 75 else \
                  'warning' if overall_health >= 60 else \
                  'critical'
    
    return JsonResponse({
        'health_score': overall_health,
        'health_status': health_status,
        'components': {
            'cache': cache_health,
            'database': db_health,
            'response_time': response_health
        },
        'current_metrics': current_metrics,
        'recent_averages': {
            'cache': recent_cache,
            'database': recent_db,
            'requests': recent_requests
        },
        'status': health_status
    })