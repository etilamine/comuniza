"""
Performance admin interface for Comuniza.
Manage performance monitoring, alerts, and optimization settings.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path

from .models import (
    CacheMetrics, DatabaseQueryMetrics, RequestPerformanceMetrics,
    UserSessionMetrics, PerformanceAlert, PerformanceSummary
)

@admin.register(PerformanceAlert)
class PerformanceAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'severity', 'threshold_value', 'message', 'timestamp', 'is_active']
    list_filter = ['alert_type', 'severity', 'is_active']
    search_fields = ['message']
    list_editable = ['threshold_value', 'message', 'is_active']
    readonly_fields = ['created_at', 'resolved_at', 'resolved_by']


@admin.register(CacheMetrics)
class CacheMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'cache_level', 'hit_count', 'miss_count', 'hit_rate', 'response_time_ms']
    list_filter = ['cache_level', 'timestamp']
    search_fields = ['cache_key_pattern']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']


@admin.register(DatabaseQueryMetrics)
class DatabaseQueryMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'query_type', 'table_name', 'execution_time_ms', 'rows_affected']
    list_filter = ['query_type', 'table_name', 'timestamp']
    search_fields = ['sql_explain', 'query_hash']
    readonly_fields = ['timestamp', 'sql_explain']
    ordering = ['-execution_time_ms']


@admin.register(RequestPerformanceMetrics)
class RequestPerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'endpoint', 'method', 'response_time_ms', 'status_code', 'user']
    list_filter = ['endpoint', 'method', 'status_code', 'timestamp']
    search_fields = ['endpoint', 'user_agent', 'ip_address']
    ordering = ['-timestamp']


@admin.register(UserSessionMetrics)
class UserSessionMetricsAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'session_id', 'page_views', 'time_on_site_seconds', 'cache_hit_rate']
    list_filter = ['user', 'timestamp']
    search_fields = ['user', 'session_id']
    ordering = ['-timestamp']


@admin.register(PerformanceSummary)
class PerformanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'summary_type', 'period_start', 'period_end']
    list_filter = ['summary_type', 'period_start']
    search_fields = ['summary_type']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-timestamp']


class PerformanceAdminSite(admin.AdminSite):
    site_header = "Comuniza Performance Monitoring"
    site_title = "Performance Dashboard"
    
    def get_urls(self):
        return [
            path('performance/', self.urls),
            path('alerts/', self.urls),
        ]
    
    def urls(self):
        return [
            path('metrics/', self.admin_view(CacheMetrics), name='cache_metrics'),
            path('alerts/', self.admin_view(PerformanceAlert), name='performance_alerts'),
            path('summaries/', self.admin_view(PerformanceSummary), name='performance_summaries'),
            path('database/', self.admin_view(DatabaseQueryMetrics), name='database_metrics'),
            path('requests/', self.admin_view(RequestPerformanceMetrics), name='request_metrics'),
            path('sessions/', self.admin_view(UserSessionMetrics), name='user_session_metrics'),
        ]


# Register the admin site
performance_site = PerformanceAdminSite()