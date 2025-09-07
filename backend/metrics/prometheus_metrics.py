# Prometheus Metrics Definitions
# All metric definitions in one place for easy management

from prometheus_client import Counter, Histogram, Gauge, Info
import os

# =============================================================================
# HTTP REQUEST METRICS
# =============================================================================

http_requests_total = Counter(
    'http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code', 'client_ip']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Time spent processing HTTP requests',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'Size of HTTP requests in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'Size of HTTP responses in bytes',
    ['method', 'endpoint', 'status_code']
)

# =============================================================================
# BUSINESS METRICS
# =============================================================================

user_registrations_total = Counter(
    'user_registrations_total',
    'Total number of user registrations'
)

user_logins_total = Counter(
    'user_logins_total',
    'Total number of successful user logins'
)

failed_login_attempts_total = Counter(
    'failed_login_attempts_total',
    'Total number of failed login attempts',
    ['reason']
)

orders_created_total = Counter(
    'orders_created_total',
    'Total number of orders created',
    ['payment_method', 'product_category']
)

revenue_total = Counter(
    'revenue_total_dollars',
    'Total revenue in dollars',
    ['currency', 'product_category']
)

# =============================================================================
# DATABASE METRICS
# =============================================================================

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Time spent on database queries',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

database_queries_total = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['operation', 'table', 'status']
)

# =============================================================================
# SYSTEM RESOURCE METRICS
# =============================================================================

memory_usage_bytes = Gauge(
    'app_memory_usage_bytes',
    'Memory usage of the application in bytes'
)

cpu_usage_percent = Gauge(
    'app_cpu_usage_percent',
    'CPU usage of the application as percentage'
)

open_file_descriptors = Gauge(
    'app_open_file_descriptors',
    'Number of open file descriptors'
)

# =============================================================================
# ERROR METRICS
# =============================================================================

errors_total = Counter(
    'app_errors_total',
    'Total number of application errors',
    ['error_type', 'endpoint', 'severity']
)

exceptions_total = Counter(
    'app_exceptions_total',
    'Total number of unhandled exceptions',
    ['exception_type', 'endpoint']
)

# =============================================================================
# APPLICATION INFO
# =============================================================================

app_info = Info(
    'app_info',
    'Application information'
)

# Set application info
app_info.info({
    'version': os.getenv('APP_VERSION', '1.0.0'),
    'environment': os.getenv('ENVIRONMENT', 'production'),
    'service_name': 'backend',
    'build_date': os.getenv('BUILD_DATE', 'unknown'),
    'git_commit': os.getenv('GIT_COMMIT', 'unknown')
})