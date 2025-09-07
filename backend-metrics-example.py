# Comprehensive Backend Metrics for Flask Application
# Add this to your Flask backend code

from flask import Flask, request, jsonify, g
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
import time
import psutil
import os
import threading
import logging
from functools import wraps

app = Flask(__name__)

# =============================================================================
# PROMETHEUS METRICS DEFINITIONS
# =============================================================================

# HTTP Request Metrics
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

# Application Performance Metrics
active_connections = Gauge(
    'app_active_connections',
    'Number of active connections to the application'
)

request_queue_size = Gauge(
    'app_request_queue_size',
    'Number of requests waiting to be processed'
)

# Business Logic Metrics
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
    ['reason']  # invalid_password, user_not_found, etc.
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

# Database Metrics
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
    ['operation', 'table', 'status']  # success, error
)

# System Resource Metrics
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

# Error Metrics
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

# Cache Metrics (if using Redis/Memcached)
cache_operations_total = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['operation', 'status']  # get, set, delete | hit, miss, error
)

cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio as percentage'
)

# Application Info
app_info = Info(
    'app_info',
    'Application information'
)

# Set application info
app_info.info({
    'version': os.getenv('APP_VERSION', '1.0.0'),
    'environment': os.getenv('ENVIRONMENT', 'production'),
    'build_date': os.getenv('BUILD_DATE', 'unknown'),
    'git_commit': os.getenv('GIT_COMMIT', 'unknown')
})

# =============================================================================
# MIDDLEWARE AND DECORATORS
# =============================================================================

@app.before_request
def before_request():
    """Start timing request and increment active connections"""
    g.start_time = time.time()
    active_connections.inc()
    
    # Log request details
    logging.info(f"Request started: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Record metrics after each request"""
    if hasattr(g, 'start_time'):
        # Request duration
        duration = time.time() - g.start_time
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)
        
        # Request count
        http_requests_total.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status_code=response.status_code,
            client_ip=request.remote_addr or 'unknown'
        ).inc()
        
        # Request size
        request_size = len(request.get_data())
        http_request_size_bytes.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(request_size)
        
        # Response size
        response_size = len(response.get_data())
        http_response_size_bytes.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status_code=response.status_code
        ).observe(response_size)
    
    active_connections.dec()
    return response

def track_database_query(operation, table):
    """Decorator to track database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                database_queries_total.labels(
                    operation=operation,
                    table=table,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                database_queries_total.labels(
                    operation=operation,
                    table=table,
                    status='error'
                ).inc()
                errors_total.labels(
                    error_type='database_error',
                    endpoint=request.endpoint or 'unknown',
                    severity='high'
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                database_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
        return wrapper
    return decorator

def track_business_metric(metric_name, labels=None):
    """Decorator to track business metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if metric_name == 'user_registration' and result:
                    user_registrations_total.inc()
                elif metric_name == 'user_login' and result:
                    user_logins_total.inc()
                elif metric_name == 'order_created' and result and labels:
                    orders_created_total.labels(**labels).inc()
                return result
            except Exception as e:
                exceptions_total.labels(
                    exception_type=type(e).__name__,
                    endpoint=request.endpoint or 'unknown'
                ).inc()
                raise
        return wrapper
    return decorator

# =============================================================================
# SYSTEM METRICS COLLECTOR (Background Thread)
# =============================================================================

def collect_system_metrics():
    """Background thread to collect system metrics"""
    while True:
        try:
            # Memory usage
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_usage_bytes.set(memory_info.rss)
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            cpu_usage_percent.set(cpu_percent)
            
            # Open file descriptors
            try:
                num_fds = process.num_fds()
                open_file_descriptors.set(num_fds)
            except AttributeError:
                # Windows doesn't support num_fds()
                pass
            
            # Database connections (mock - replace with real DB pool)
            database_connections_active.set(get_active_db_connections())
            
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
        
        time.sleep(10)  # Collect every 10 seconds

def get_active_db_connections():
    """Get number of active database connections - implement based on your DB"""
    # Mock implementation - replace with real database pool query
    return 5

# Start system metrics collection thread
metrics_thread = threading.Thread(target=collect_system_metrics, daemon=True)
metrics_thread.start()

# =============================================================================
# METRICS ENDPOINT
# =============================================================================

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# =============================================================================
# HEALTH CHECKS
# =============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'backend',
        'version': os.getenv('APP_VERSION', '1.0.0')
    })

@app.route('/ready')
def ready():
    """Readiness check endpoint"""
    # Add your readiness checks here (database, cache, etc.)
    return jsonify({
        'status': 'ready',
        'timestamp': time.time(),
        'checks': {
            'database': check_database_connection(),
            'cache': check_cache_connection()
        }
    })

def check_database_connection():
    """Check if database is available"""
    # Implement your database check
    return True

def check_cache_connection():
    """Check if cache is available"""
    # Implement your cache check
    return True

# =============================================================================
# EXAMPLE BUSINESS ENDPOINTS WITH METRICS
# =============================================================================

@app.route('/api/register', methods=['POST'])
@track_business_metric('user_registration')
def register_user():
    """User registration with metrics"""
    try:
        # Your registration logic here
        data = request.json
        
        # Simulate registration
        success = True  # Replace with actual registration logic
        
        if success:
            logging.info("User registered successfully")
            return jsonify({'status': 'success', 'message': 'User registered'})
        else:
            failed_login_attempts_total.labels(reason='registration_failed').inc()
            return jsonify({'status': 'error', 'message': 'Registration failed'}), 400
            
    except Exception as e:
        errors_total.labels(
            error_type='registration_error',
            endpoint='register_user',
            severity='medium'
        ).inc()
        logging.error(f"Registration error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal error'}), 500

@app.route('/api/login', methods=['POST'])
@track_business_metric('user_login')
def login_user():
    """User login with metrics"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        # Your authentication logic here
        if authenticate_user(username, password):
            return jsonify({'status': 'success', 'token': 'fake-jwt-token'})
        else:
            failed_login_attempts_total.labels(reason='invalid_credentials').inc()
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        errors_total.labels(
            error_type='login_error',
            endpoint='login_user',
            severity='medium'
        ).inc()
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create order with business metrics"""
    try:
        data = request.json
        payment_method = data.get('payment_method', 'unknown')
        category = data.get('category', 'general')
        amount = data.get('amount', 0)
        
        # Simulate order creation
        success = create_order_in_db(data)
        
        if success:
            # Track business metrics
            orders_created_total.labels(
                payment_method=payment_method,
                product_category=category
            ).inc()
            
            revenue_total.labels(
                currency='USD',
                product_category=category
            ).inc(amount)
            
            return jsonify({'status': 'success', 'order_id': '12345'})
        else:
            return jsonify({'status': 'error', 'message': 'Order creation failed'}), 400
            
    except Exception as e:
        errors_total.labels(
            error_type='order_error',
            endpoint='create_order',
            severity='high'
        ).inc()
        return jsonify({'status': 'error', 'message': 'Order failed'}), 500

@app.route('/api/products', methods=['GET'])
@track_database_query('select', 'products')
def get_products():
    """Get products with database metrics"""
    try:
        # Simulate database query
        products = query_products_from_db()
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to fetch products'}), 500

# =============================================================================
# HELPER FUNCTIONS (Implement based on your application)
# =============================================================================

def authenticate_user(username, password):
    """Mock authentication - replace with real implementation"""
    return username == 'admin' and password == 'password'

def create_order_in_db(order_data):
    """Mock order creation - replace with real implementation"""
    return True

def query_products_from_db():
    """Mock product query - replace with real implementation"""
    return [{'id': 1, 'name': 'Product 1', 'price': 10.99}]

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    print("Starting Flask application with comprehensive metrics...")
    print("Metrics available at: http://localhost:8001/metrics")
    print("Health check at: http://localhost:8000/health")
    
    # Run the app
    app.run(host='0.0.0.0', port=8000, debug=False)