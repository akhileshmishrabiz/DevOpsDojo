# API Routes with Full Metrics Integration
# Example of how to add metrics to your existing API endpoints

from flask import Blueprint, request, jsonify
from metrics import (
    track_user_login,
    track_user_registration,
    track_database_query,
    orders_created_total,
    revenue_total,
    failed_login_attempts_total,
    errors_total,
    user_logins_total
)
import logging

api = Blueprint('api', __name__, url_prefix='/api')

# =============================================================================
# FRONTEND METRICS COLLECTION ENDPOINT
# =============================================================================

@api.route('/frontend-metrics', methods=['POST'])
def collect_frontend_metrics():
    """Collect metrics from frontend application"""
    try:
        data = request.json
        session_id = data.get('sessionId')
        metrics = data.get('metrics', {})
        page = data.get('page', 'unknown')
        
        logging.info(f"Frontend metrics received from session {session_id}")
        
        # You could store these in a database or forward to another service
        # For now, just log them
        
        # Track frontend page views as backend metric
        if metrics.get('pageViews', 0) > 0:
            logging.info(f"Frontend page views: {metrics['pageViews']} for {page}")
        
        # Track frontend errors
        if metrics.get('errors'):
            for error in metrics['errors']:
                logging.error(f"Frontend error: {error.get('message')} on {error.get('page')}")
        
        return jsonify({'status': 'success', 'message': 'Metrics received'})
        
    except Exception as e:
        errors_total.labels(
            error_type='frontend_metrics_error',
            endpoint='collect_frontend_metrics',
            severity='medium'
        ).inc()
        logging.error(f"Error collecting frontend metrics: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to collect metrics'}), 500

# =============================================================================
# USER AUTHENTICATION ENDPOINTS WITH METRICS
# =============================================================================

@api.route('/register', methods=['POST'])
@track_user_registration
def register():
    """User registration with comprehensive metrics"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists (mock implementation)
        if user_exists(username, email):
            return jsonify({'error': 'User already exists'}), 409
        
        # Create user (mock implementation)
        user_id = create_user(username, email, password)
        
        if user_id:
            logging.info(f"User registered successfully: {username}")
            return jsonify({
                'status': 'success',
                'message': 'User registered successfully',
                'user_id': user_id
            }), 201
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except Exception as e:
        errors_total.labels(
            error_type='registration_error',
            endpoint='register',
            severity='high'
        ).inc()
        logging.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/login', methods=['POST'])
@track_user_login
def login():
    """User login with detailed metrics tracking"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            failed_login_attempts_total.labels(reason='missing_credentials').inc()
            return jsonify({'error': 'Username and password required'}), 400
        
        # Authenticate user (mock implementation)
        user = authenticate_user(username, password)
        
        if user:
            # Generate JWT token (mock)
            token = generate_jwt_token(user['id'])
            
            logging.info(f"User logged in successfully: {username}")
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })
        else:
            failed_login_attempts_total.labels(reason='invalid_credentials').inc()
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        errors_total.labels(
            error_type='login_error',
            endpoint='login',
            severity='high'
        ).inc()
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

# =============================================================================
# PRODUCT ENDPOINTS WITH DATABASE METRICS
# =============================================================================

@api.route('/products', methods=['GET'])
@track_database_query('select', 'products')
def get_products():
    """Get products with database performance tracking"""
    try:
        # Query parameters
        category = request.args.get('category')
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 items
        offset = int(request.args.get('offset', 0))
        
        # Fetch products (mock implementation)
        products = fetch_products(category, limit, offset)
        total_count = get_products_count(category)
        
        return jsonify({
            'status': 'success',
            'data': {
                'products': products,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
        })
        
    except Exception as e:
        errors_total.labels(
            error_type='product_fetch_error',
            endpoint='get_products',
            severity='medium'
        ).inc()
        logging.error(f"Error fetching products: {e}")
        return jsonify({'error': 'Failed to fetch products'}), 500

@api.route('/products/<int:product_id>', methods=['GET'])
@track_database_query('select', 'products')
def get_product(product_id):
    """Get single product with caching metrics"""
    try:
        # Check cache first (mock implementation)
        product = get_product_from_cache(product_id)
        
        if not product:
            # Cache miss - fetch from database
            product = fetch_product_by_id(product_id)
            if product:
                cache_product(product_id, product)
        
        if product:
            return jsonify({
                'status': 'success',
                'data': product
            })
        else:
            return jsonify({'error': 'Product not found'}), 404
            
    except Exception as e:
        errors_total.labels(
            error_type='product_detail_error',
            endpoint='get_product',
            severity='medium'
        ).inc()
        return jsonify({'error': 'Failed to fetch product'}), 500

# =============================================================================
# ORDER ENDPOINTS WITH BUSINESS METRICS
# =============================================================================

@api.route('/orders', methods=['POST'])
def create_order():
    """Create order with comprehensive business metrics"""
    try:
        data = request.json
        user_id = data.get('user_id')
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'unknown')
        
        # Validation
        if not user_id or not items:
            return jsonify({'error': 'User ID and items required'}), 400
        
        # Calculate order total
        total_amount = calculate_order_total(items)
        
        if total_amount <= 0:
            return jsonify({'error': 'Invalid order total'}), 400
        
        # Create order (mock implementation)
        order_id = create_order_in_database({
            'user_id': user_id,
            'items': items,
            'total': total_amount,
            'payment_method': payment_method
        })
        
        if order_id:
            # Track business metrics
            primary_category = get_primary_category(items)
            
            orders_created_total.labels(
                payment_method=payment_method,
                product_category=primary_category
            ).inc()
            
            revenue_total.labels(
                currency='USD',
                product_category=primary_category
            ).inc(total_amount)
            
            logging.info(f"Order created: {order_id}, Total: ${total_amount}, Method: {payment_method}")
            
            return jsonify({
                'status': 'success',
                'message': 'Order created successfully',
                'order_id': order_id,
                'total': total_amount
            }), 201
        else:
            return jsonify({'error': 'Failed to create order'}), 500
            
    except Exception as e:
        errors_total.labels(
            error_type='order_creation_error',
            endpoint='create_order',
            severity='critical'  # Orders are critical for business
        ).inc()
        logging.error(f"Order creation error: {e}")
        return jsonify({'error': 'Failed to create order'}), 500

@api.route('/orders/<string:order_id>', methods=['GET'])
@track_database_query('select', 'orders')
def get_order(order_id):
    """Get order details"""
    try:
        order = fetch_order_by_id(order_id)
        
        if order:
            return jsonify({
                'status': 'success',
                'data': order
            })
        else:
            return jsonify({'error': 'Order not found'}), 404
            
    except Exception as e:
        errors_total.labels(
            error_type='order_fetch_error',
            endpoint='get_order',
            severity='medium'
        ).inc()
        return jsonify({'error': 'Failed to fetch order'}), 500

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@api.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get dashboard analytics for admin"""
    try:
        # This could fetch from your metrics database
        analytics = {
            'total_users': get_total_users(),
            'total_orders': get_total_orders(),
            'revenue_today': get_revenue_today(),
            'top_products': get_top_products(5)
        }
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
        
    except Exception as e:
        errors_total.labels(
            error_type='analytics_error',
            endpoint='get_dashboard_analytics',
            severity='low'
        ).inc()
        return jsonify({'error': 'Failed to fetch analytics'}), 500

# =============================================================================
# MOCK DATABASE FUNCTIONS (Replace with your actual database code)
# =============================================================================

def user_exists(username, email):
    """Mock function - check if user exists"""
    return False  # Always return False for demo

def create_user(username, email, password):
    """Mock function - create user"""
    import uuid
    return str(uuid.uuid4())

def authenticate_user(username, password):
    """Mock function - authenticate user"""
    if username == 'admin' and password == 'password':
        return {
            'id': '1',
            'username': username,
            'email': 'admin@example.com'
        }
    return None

def generate_jwt_token(user_id):
    """Mock function - generate JWT token"""
    return f'fake_jwt_token_for_user_{user_id}'

def fetch_products(category=None, limit=20, offset=0):
    """Mock function - fetch products"""
    products = [
        {'id': i, 'name': f'Product {i}', 'price': 10.99 + i, 'category': 'electronics'}
        for i in range(offset + 1, offset + limit + 1)
    ]
    return products

def get_products_count(category=None):
    """Mock function - get total products count"""
    return 100

def fetch_product_by_id(product_id):
    """Mock function - fetch single product"""
    return {
        'id': product_id,
        'name': f'Product {product_id}',
        'price': 10.99 + product_id,
        'description': f'Description for product {product_id}',
        'category': 'electronics'
    }

def get_product_from_cache(product_id):
    """Mock function - get from cache"""
    return None  # Always cache miss for demo

def cache_product(product_id, product):
    """Mock function - cache product"""
    pass

def calculate_order_total(items):
    """Calculate order total from items"""
    return sum(item.get('price', 0) * item.get('quantity', 1) for item in items)

def create_order_in_database(order_data):
    """Mock function - create order"""
    import uuid
    return str(uuid.uuid4())

def get_primary_category(items):
    """Get primary category from order items"""
    if items:
        return items[0].get('category', 'general')
    return 'general'

def fetch_order_by_id(order_id):
    """Mock function - fetch order"""
    return {
        'id': order_id,
        'user_id': '1',
        'total': 99.99,
        'status': 'completed',
        'items': [
            {'name': 'Product 1', 'price': 49.99, 'quantity': 1},
            {'name': 'Product 2', 'price': 49.99, 'quantity': 1}
        ]
    }

def get_total_users():
    """Mock function - get total users"""
    return 1250

def get_total_orders():
    """Mock function - get total orders"""
    return 456

def get_revenue_today():
    """Mock function - get today's revenue"""
    return 2847.50

def get_top_products(limit):
    """Mock function - get top products"""
    return [
        {'name': f'Top Product {i}', 'sales': 100 - i * 10}
        for i in range(1, limit + 1)
    ]