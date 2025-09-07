# Backend Metrics Module
# Import and initialize metrics for easy use

from .prometheus_metrics import (
    # HTTP Metrics
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    
    # Business Metrics
    user_registrations_total,
    user_logins_total,
    failed_login_attempts_total,
    orders_created_total,
    revenue_total,
    
    # Database Metrics
    database_connections_active,
    database_query_duration_seconds,
    database_queries_total,
    
    # System Metrics
    memory_usage_bytes,
    cpu_usage_percent,
    open_file_descriptors,
    
    # Error Metrics
    errors_total,
    exceptions_total,
    
    # Application Info
    app_info
)

from .middleware import setup_metrics_middleware
from .decorators import track_database_query, track_business_metric

__all__ = [
    'http_requests_total',
    'http_request_duration_seconds',
    'user_registrations_total',
    'user_logins_total',
    'orders_created_total',
    'revenue_total',
    'database_connections_active',
    'database_queries_total',
    'errors_total',
    'setup_metrics_middleware',
    'track_database_query',
    'track_business_metric'
]