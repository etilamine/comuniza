"""
Performance monitoring models for Comuniza.
Stores real-time performance metrics and analytics data.
"""

from django.db import models
from django.db.models import Count, Avg, Min, Max
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class CacheMetrics(models.Model):
    """Cache performance metrics over time."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    cache_level = models.CharField(max_length=10)  # L1, L2, L3
    hit_count = models.PositiveIntegerField(default=0)
    miss_count = models.PositiveIntegerField(default=0)
    response_time_ms = models.FloatField()
    cache_key_pattern = models.CharField(max_length=200, blank=True)
    
    class Meta:
        app_label = 'performance'
        db_table = 'performance_cache_metrics'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['cache_level']),
            models.Index(fields=['timestamp', 'cache_level']),
        ]


class DatabaseQueryMetrics(models.Model):
    """Database query performance tracking."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    query_type = models.CharField(max_length=100)  # SELECT, INSERT, UPDATE, etc.
    table_name = models.CharField(max_length=100)
    execution_time_ms = models.FloatField()
    rows_affected = models.PositiveIntegerField(default=0)
    sql_explain = models.TextField(blank=True)
    query_hash = models.CharField(max_length=64, blank=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        app_label = 'performance'
        db_table = 'performance_database_metrics'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['query_type']),
            models.Index(fields=['user_id']),
            models.Index(fields=['execution_time_ms']),
        ]


class RequestPerformanceMetrics(models.Model):
    """HTTP request performance tracking."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)  # GET, POST, etc.
    response_time_ms = models.FloatField()
    status_code = models.PositiveIntegerField()
    response_size_bytes = models.PositiveIntegerField(default=0)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    cache_hit = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'performance'
        db_table = 'performance_request_metrics'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['user_id']),
            models.Index(fields=['response_time_ms']),
            models.Index(fields=['status_code']),
        ]


class UserSessionMetrics(models.Model):
    """User session and experience tracking."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=128)
    page_views = models.PositiveIntegerField(default=0)
    time_on_site_seconds = models.FloatField(default=0)
    cache_hits = models.PositiveIntegerField(default=0)
    cache_misses = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0)
    bounce_rate = models.FloatField(default=0)
    
    class Meta:
        app_label = 'performance'
        db_table = 'performance_user_session_metrics'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user_id']),
            models.Index(fields=['session_id']),
        ]


class PerformanceAlert(models.Model):
    """Performance alert configurations and history."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    alert_type = models.CharField(max_length=50)  # SLOW_QUERY, HIGH_RESPONSE_TIME, etc.
    severity = models.CharField(max_length=20)  # LOW, MEDIUM, HIGH, CRITICAL
    threshold_value = models.FloatField()
    current_value = models.FloatField()
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        app_label = 'performance'
        db_table = 'performance_alerts'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['is_active']),
        ]


class PerformanceSummary(models.Model):
    """Aggregated performance summaries for reporting."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    summary_type = models.CharField(max_length=50)  # HOURLY, DAILY, WEEKLY
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Cache metrics
    total_cache_requests = models.PositiveIntegerField(default=0)
    cache_hit_rate = models.FloatField(default=0)
    avg_cache_response_time_ms = models.FloatField(default=0)
    l1_hit_rate = models.FloatField(default=0)
    l2_hit_rate = models.FloatField(default=0)
    
    # Database metrics
    avg_query_time_ms = models.FloatField(default=0)
    total_queries = models.PositiveIntegerField(default=0)
    slow_queries = models.PositiveIntegerField(default=0)
    
    # Request metrics
    avg_response_time_ms = models.FloatField(default=0)
    total_requests = models.PositiveIntegerField(default=0)
    error_rate = models.FloatField(default=0)
    
    class Meta:
        app_label = 'performance'
        db_table = 'performance_summaries'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['summary_type']),
            models.Index(fields=['period_start', 'period_end']),
        ]