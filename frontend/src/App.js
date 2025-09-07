// Example React App with Metrics Integration

import React from 'react';
import { MetricsProvider, useMetrics, usePageTracking, useActionTracking } from './hooks/useMetrics';
import './App.css';

// Main App component with MetricsProvider
function App() {
  const metricsConfig = {
    backendUrl: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
    debugMode: process.env.NODE_ENV === 'development'
  };

  return (
    <MetricsProvider config={metricsConfig}>
      <div className="App">
        <header className="App-header">
          <h1>3-Tier Application</h1>
          <p>Frontend with Metrics Tracking</p>
        </header>
        <main>
          <HomePage />
          <ProductSection />
          <UserSection />
        </main>
        {process.env.NODE_ENV === 'development' && <MetricsDebugger />}
      </div>
    </MetricsProvider>
  );
}

// Home page component with page tracking
const HomePage = () => {
  usePageTracking(); // Automatically tracks page views

  return (
    <section>
      <h2>Welcome to Our App</h2>
      <p>This page automatically tracks page views and user interactions.</p>
    </section>
  );
};

// Product section with business metrics
const ProductSection = () => {
  const { trackAction, trackConversion } = useActionTracking();

  const handleViewProduct = (productId) => {
    trackAction('product_viewed', { productId });
  };

  const handleAddToCart = (productId, price) => {
    trackAction('add_to_cart', { productId, price });
    trackConversion('cart_addition', 1);
  };

  const handlePurchase = (orderId, total) => {
    trackAction('purchase_completed', { orderId, total });
    trackConversion('purchase', total);
  };

  return (
    <section>
      <h2>Products</h2>
      <div className="products">
        <div className="product">
          <h3>Product 1</h3>
          <p>Price: $19.99</p>
          <button onClick={() => handleViewProduct('prod1')}>
            View Details
          </button>
          <button onClick={() => handleAddToCart('prod1', 19.99)}>
            Add to Cart
          </button>
        </div>
        
        <div className="product">
          <h3>Product 2</h3>
          <p>Price: $29.99</p>
          <button onClick={() => handleViewProduct('prod2')}>
            View Details
          </button>
          <button onClick={() => handleAddToCart('prod2', 29.99)}>
            Add to Cart
          </button>
        </div>
      </div>
      
      <button 
        className="purchase-btn"
        onClick={() => handlePurchase('order123', 49.98)}
      >
        Complete Purchase
      </button>
    </section>
  );
};

// User section with API calls and error tracking
const UserSection = () => {
  const { trackAction, trackError } = useActionTracking();
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  const handleLogin = async () => {
    setLoading(true);
    const startTime = Date.now();
    
    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'admin',
          password: 'password'
        })
      });

      // Track API call duration
      const duration = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        trackAction('login_success', { duration });
      } else {
        throw new Error(`Login failed: ${response.status}`);
      }
    } catch (error) {
      trackError(error, { context: 'login_attempt' });
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    setLoading(true);
    const startTime = Date.now();
    
    try {
      const response = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'newuser',
          email: 'newuser@example.com'
        })
      });

      const duration = Date.now() - startTime;
      
      if (response.ok) {
        trackAction('registration_success', { duration });
        alert('Registration successful!');
      } else {
        throw new Error(`Registration failed: ${response.status}`);
      }
    } catch (error) {
      trackError(error, { context: 'registration_attempt' });
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const simulateError = () => {
    try {
      // Intentional error for testing
      throw new Error('Simulated frontend error for testing metrics');
    } catch (error) {
      trackError(error, { context: 'intentional_test' });
      console.error('Simulated error:', error);
    }
  };

  return (
    <section>
      <h2>User Actions</h2>
      
      {!user ? (
        <div className="auth-buttons">
          <button 
            onClick={handleLogin} 
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
          
          <button 
            onClick={handleRegister} 
            disabled={loading}
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </div>
      ) : (
        <div>
          <p>Welcome back! Status: {user.status}</p>
          <button onClick={() => setUser(null)}>Logout</button>
        </div>
      )}

      <div className="test-actions">
        <h3>Test Metrics</h3>
        <button onClick={simulateError}>
          Simulate Error (for testing)
        </button>
        
        <button onClick={() => trackAction('feature_clicked', { feature: 'test_button' })}>
          Track Custom Action
        </button>
      </div>
    </section>
  );
};

// Component to display current metrics (for debugging)
const MetricsDebugger = () => {
  const metrics = useMetrics();
  const [metricsData, setMetricsData] = React.useState(null);

  React.useEffect(() => {
    if (metrics) {
      // Update metrics display every 5 seconds
      const interval = setInterval(() => {
        setMetricsData({ ...metrics.metrics });
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [metrics]);

  if (!metricsData) {
    return null;
  }

  return (
    <div style={{ 
      position: 'fixed', 
      bottom: 0, 
      right: 0, 
      background: '#f0f0f0', 
      padding: '10px',
      maxWidth: '300px',
      fontSize: '12px',
      border: '1px solid #ccc'
    }}>
      <h4>Metrics Debug</h4>
      <p>Page Views: {metricsData.pageViews}</p>
      <p>Clicks: {Object.keys(metricsData.buttonClicks).length}</p>
      <p>Actions: {Object.keys(metricsData.userActions).length}</p>
      <p>Errors: {metricsData.errors.length}</p>
      <p>API Calls: {Object.keys(metricsData.apiCalls).length}</p>
    </div>
  );
};

export default App;