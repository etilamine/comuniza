"""
Performance dashboard views for Comuniza.
Real-time monitoring and analytics interface.
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Min, Max
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

from .models import (
    CacheMetrics, DatabaseQueryMetrics, RequestPerformanceMetrics,
    UserSessionMetrics, PerformanceAlert, PerformanceSummary
)

@staff_member_required
def dashboard(request):
    """Main performance dashboard."""
    
    # Get recent metrics
    recent_cache = CacheMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).order_by('-timestamp')[:100]
    
    # Calculate performance stats
    cache_stats = recent_cache.aggregate(
        avg_response_time=Avg('response_time_ms'),
        hit_rate=Avg('hit_rate'),
        total_requests=Count('id')
    )
    
    # Recent database queries
    recent_db = DatabaseQueryMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=30)
    ).order_by('-execution_time_ms')[:20]
    
    # Recent requests
    recent_requests = RequestPerformanceMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(minutes=30)
    ).order_by('-timestamp')[:50]
    
    # Calculate system health
    avg_response_time = cache_stats['avg_response_time'] or 0
    error_rate = recent_requests.aggregate(
        error_rate=Avg('status_code', filter=models.Q(status_code__gte=400))
    )['error_rate'] or 0
    
    # Calculate health score (0-100)
    health_score = min(100, max(0, 100 - (avg_response_time * 2) - (error_rate * 10)))
    
    health_status = 'excellent' if health_score >= 90 else \
                   'good' if health_score >= 75 else \
                   'warning' if health_score >= 60 else \
                   'critical'
    
    return render(request, 'performance/dashboard.html', {
        'cache_metrics': cache_stats,
        'recent_cache': recent_cache,
        'recent_db_queries': recent_db,
        'recent_requests': recent_requests,
        'health_score': health_score,
        'health_status': health_status,
        'avg_response_time': avg_response_time,
        'error_rate': error_rate,
    })


@staff_member_required
def cache_details(request):
    """Detailed cache performance metrics."""
    
    # Get cache metrics with filtering
    cache_level = request.GET.get('level', 'L1')
    time_range = request.GET.get('time_range', '24h')
    
    if time_range == '24h':
        timestamp_filter = {'timestamp__gte': timezone.now() - timedelta(hours=24)}
    elif time_range == '7d':
        timestamp_filter = {'timestamp__gte': timezone.now() - timedelta(days=7)}
    else:
        timestamp_filter = {'timestamp__gte': timezone.now() - timedelta(hours=1)}
    
    metrics = CacheMetrics.objects.filter(
        cache_level=cache_level,
        **timestamp_filter
    ).order_by('-timestamp')[:500]
    
    # Aggregate by cache level
    cache_stats = metrics.aggregate(
        avg_response_time=Avg('response_time_ms'),
        hit_rate=Avg('hit_rate'),
        total_requests=Count('id')
    )
    
    return render(request, 'performance/cache_details.html', {
        'cache_level': cache_level,
        'time_range': time_range,
        'metrics': metrics,
        'cache_stats': cache_stats,
    })


@staff_member_required
def database_details(request):
    """Database query performance details."""
    
    # Get slow queries
    slow_queries = DatabaseQueryMetrics.objects.filter(
        execution_time_ms__gt=500  # Queries slower than 500ms
    ).order_by('-execution_time_ms')[:50]
    
    # Get query performance by type
    query_performance = DatabaseQueryMetrics.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).values('query_type').annotate(
        avg_time=Avg('execution_time_ms'),
        count=Count('id'),
        max_time=Max('execution_time_ms'),
        slow_count=Count('id', filter=models.Q(execution_time_ms__gt=1000))
    )
    
    return render(request, 'performance/database_details.html', {
        'slow_queries': slow_queries,
        'query_performance': list(query_performance),
    })


@staff_member_required
def alerts(request):
    """Performance alerts management."""
    
    active_alerts = PerformanceAlert.objects.filter(
        is_active=True
    ).order_by('-timestamp')
    
    resolved_alerts = PerformanceAlert.objects.filter(
        resolved_at__isnull=False
    ).order_by('-resolved_at')[:20]
    
    return render(request, 'performance/alerts.html', {
        'active_alerts': active_alerts,
        'resolved_alerts': resolved_alerts,
    })


@staff_member_required
def reports(request):
    """Performance reports and summaries."""
    
    period_type = request.GET.get('period', 'HOURLY')
    
    if period_type == 'HOURLY':
        period_start = timezone.now() - timedelta(hours=24)
    elif period_type == 'DAILY':
        period_start = timezone.now() - timedelta(days=1)
    elif period_type == 'WEEKLY':
        period_start = timezone.now() - timedelta(days=7)
    else:
        period_start = timezone.now() - timedelta(days=30)
    
    summaries = PerformanceSummary.objects.filter(
        period_start__gte=period_start
    ).order_by('-timestamp')[:10]
    
    return render(request, 'performance/reports.html', {
        'period_type': period_type,
        'summaries': summaries,
        'period_start': period_start,
    })