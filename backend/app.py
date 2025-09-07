# Example Flask App with Integrated Metrics
# This shows how to use the metrics in your main application

from flask import Flask, request, jsonify
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging

# Import your metrics
from metrics import (
    setup_metrics_middleware,
    track_database_query,
    track_business_metric,
    track_user_registration,
    track_user_login,
    user_registrations_total,
    user_logins_total,
    failed_login_attempts_total,
    orders_created_total,
    revenue_total,
    errors_total
)

app = Flask(__name__)

# Setup metrics middleware - this automatically tracks HTTP requests
setup_metrics_middleware(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

# =============================================================================
# METRICS ENDPOINT
# =============================================================================

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'backend',
        'version': '1.0.0'
    })

@app.route('/ready')
def ready():
    """Readiness check endpoint"""
    return jsonify({
        'status': 'ready',
        'service': 'backend'
    })

# =============================================================================
# EXAMPLE BUSINESS ENDPOINTS WITH METRICS
# =============================================================================

@app.route('/api/register', methods=['POST'])
@track_user_registration
def register_user():
    """User registration endpoint with automatic metrics"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        # Your registration logic here
        if not username or not email:
            return jsonify({'error': 'Username and email required'}), 400
        
        # Simulate registration process
        success = create_user_in_database(username, email)
        
        if success:
            logging.info(f"User registered successfully: {username}")
            return jsonify({'status': 'success', 'message': 'User registered'})
        else:
            return jsonify({'error': 'Registration failed'}), 400
            
    except Exception as e:
        errors_total.labels(
            error_type='registration_error',
            endpoint='register_user',
            severity='medium'
        ).inc()
        logging.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/login', methods=['POST'])
@track_user_login
def login_user():
    """User login endpoint with automatic metrics"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Simulate authentication
        if authenticate_user(username, password):
            logging.info(f"User logged in successfully: {username}")
            return jsonify({'status': 'success', 'token': 'fake-jwt-token'})
        else:
            failed_login_attempts_total.labels(reason='invalid_credentials').inc()
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        errors_total.labels(
            error_type='login_error',
            endpoint='login_user',
            severity='medium'
        ).inc()
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create order with business metrics tracking"""
    try:
        data = request.json
        payment_method = data.get('payment_method', 'unknown')
        category = data.get('category', 'general')
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        # Simulate order creation
        order_id = create_order_in_database(data)
        
        if order_id:
            # Track business metrics manually
            orders_created_total.labels(
                payment_method=payment_method,
                product_category=category
            ).inc()
            
            revenue_total.labels(
                currency='USD',
                product_category=category
            ).inc(amount)
            
            logging.info(f"Order created: {order_id}, Amount: ${amount}")
            return jsonify({'status': 'success', 'order_id': order_id})
        else:
            return jsonify({'error': 'Order creation failed'}), 500
            
    except Exception as e:
        errors_total.labels(
            error_type='order_error',
            endpoint='create_order',
            severity='high'
        ).inc()
        logging.error(f"Order creation error: {e}")
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/api/products', methods=['GET'])
@track_database_query('select', 'products')
def get_products():
    """Get products with database metrics tracking"""
    try:
        # This decorator automatically tracks database query metrics
        products = query_products_from_database()
        return jsonify({'products': products})
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        return jsonify({'error': 'Failed to fetch products'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
@track_database_query('select', 'users')
def get_user(user_id):
    """Get user by ID with database metrics"""
    try:
        user = get_user_from_database(user_id)
        if user:
            return jsonify({'user': user})
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logging.error(f"Error fetching user {user_id}: {e}")
        return jsonify({'error': 'Failed to fetch user'}), 500

# =============================================================================
# TEST ENDPOINTS FOR METRICS DEMONSTRATION
# =============================================================================

@app.route('/simulate/traffic')
def simulate_traffic():
    """Generate sample metrics for testing"""
    import random
    
    # Simulate different types of requests
    for _ in range(10):
        if random.random() < 0.1:  # 10% error rate
            errors_total.labels(
                error_type='simulated_error',
                endpoint='simulate_traffic',
                severity='low'
            ).inc()
        
        if random.random() < 0.3:  # 30% create orders
            orders_created_total.labels(
                payment_method=random.choice(['credit_card', 'paypal', 'bank_transfer']),
                product_category=random.choice(['electronics', 'books', 'clothing'])
            ).inc()
            
            revenue_total.labels(
                currency='USD',
                product_category=random.choice(['electronics', 'books', 'clothing'])
            ).inc(random.uniform(10, 200))
    
    return jsonify({'message': 'Traffic simulation completed'})

@app.route('/simulate/users')
def simulate_users():
    """Simulate user registrations and logins"""
    import random
    
    # Simulate user activity
    for _ in range(5):
        if random.random() < 0.7:  # 70% successful registrations
            user_registrations_total.inc()
        
        if random.random() < 0.8:  # 80% successful logins
            user_logins_total.inc()
        else:
            failed_login_attempts_total.labels(
                reason=random.choice(['invalid_password', 'user_not_found', 'account_locked'])
            ).inc()
    
    return jsonify({'message': 'User simulation completed'})

# =============================================================================
# MOCK DATABASE FUNCTIONS (Replace with your actual database code)
# =============================================================================

def authenticate_user(username, password):
    """Mock authentication - replace with real implementation"""
    return username == 'admin' and password == 'password'

def create_user_in_database(username, email):
    """Mock user creation - replace with real implementation"""
    return True  # Simulate successful creation

def create_order_in_database(order_data):
    """Mock order creation - replace with real implementation"""
    import uuid
    return str(uuid.uuid4())  # Return fake order ID

def query_products_from_database():
    """Mock product query - replace with real implementation"""
    return [
        {'id': 1, 'name': 'Product 1', 'price': 19.99},
        {'id': 2, 'name': 'Product 2', 'price': 29.99},
        {'id': 3, 'name': 'Product 3', 'price': 39.99}
    ]

def get_user_from_database(user_id):
    """Mock user query - replace with real implementation"""
    return {
        'id': user_id,
        'username': f'user_{user_id}',
        'email': f'user_{user_id}@example.com'
    }

# =============================================================================
# MAIN APPLICATION
# =============================================================================

if __name__ == '__main__':
    print("Starting Flask application with metrics...")
    print("Metrics endpoint: http://localhost:8000/metrics")
    print("Health check: http://localhost:8000/health")
    print("Test endpoints:")
    print("  - http://localhost:8000/simulate/traffic")
    print("  - http://localhost:8000/simulate/users")
    
    app.run(host='0.0.0.0', port=8000, debug=True)