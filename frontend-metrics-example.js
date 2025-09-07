// Comprehensive Frontend Metrics for React Application
// Add this to your React frontend application

// Install required packages:
// npm install web-vitals axios

import axios from 'axios';

class FrontendMetrics {
  constructor(config = {}) {
    this.config = {
      backendUrl: config.backendUrl || 'http://localhost:8000',
      metricsEndpoint: config.metricsEndpoint || '/api/metrics',
      sendInterval: config.sendInterval || 30000, // 30 seconds
      maxBatchSize: config.maxBatchSize || 100,
      debugMode: config.debugMode || false,
      ...config
    };

    this.metrics = {
      // User Interaction Metrics
      pageViews: 0,
      buttonClicks: {},
      formSubmissions: {},
      userSessions: 0,
      
      // Performance Metrics
      pageLoadTimes: [],
      apiCallDurations: {},
      renderTimes: {},
      
      // Error Metrics
      jsErrors: [],
      apiErrors: [],
      networkErrors: [],
      
      // Business Metrics
      userActions: {},
      conversions: {},
      featureUsage: {},
      
      // Technical Metrics
      browserInfo: this.getBrowserInfo(),
      deviceInfo: this.getDeviceInfo(),
      connectionInfo: this.getConnectionInfo(),
      
      // Web Vitals
      webVitals: {}
    };

    this.init();
  }

  // =============================================================================
  // INITIALIZATION
  // =============================================================================

  init() {
    this.setupEventListeners();
    this.trackPageView();
    this.measureWebVitals();
    this.startMetricsCollection();
    this.setupPerformanceObserver();
    
    // Send metrics periodically
    setInterval(() => this.sendMetrics(), this.config.sendInterval);
    
    // Send metrics before page unload
    window.addEventListener('beforeunload', () => this.sendMetrics());
    
    console.log('Frontend metrics initialized');
  }

  // =============================================================================
  // EVENT LISTENERS
  // =============================================================================

  setupEventListeners() {
    // Track all clicks
    document.addEventListener('click', (event) => {
      this.trackClick(event);
    });

    // Track form submissions
    document.addEventListener('submit', (event) => {
      this.trackFormSubmission(event);
    });

    // Track JavaScript errors
    window.addEventListener('error', (event) => {
      this.trackJSError(event);
    });

    // Track unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.trackPromiseRejection(event);
    });

    // Track navigation
    window.addEventListener('popstate', () => {
      this.trackPageView();
    });

    // Track visibility changes (tab switching)
    document.addEventListener('visibilitychange', () => {
      this.trackVisibilityChange();
    });
  }

  // =============================================================================
  // USER INTERACTION TRACKING
  // =============================================================================

  trackPageView(page = window.location.pathname) {
    this.metrics.pageViews++;
    const timestamp = Date.now();
    
    // Measure page load time
    if (window.performance && window.performance.timing) {
      const loadTime = window.performance.timing.loadEventEnd - 
                      window.performance.timing.navigationStart;
      this.metrics.pageLoadTimes.push({
        page,
        loadTime,
        timestamp
      });
    }

    this.log('Page view tracked:', page);
  }

  trackClick(event) {
    const element = event.target;
    const elementType = element.tagName.toLowerCase();
    const elementId = element.id || 'unknown';
    const elementClass = element.className || 'unknown';
    const elementText = element.textContent?.slice(0, 50) || 'unknown';

    const clickData = {
      elementType,
      elementId,
      elementClass,
      elementText,
      timestamp: Date.now(),
      page: window.location.pathname
    };

    const key = `${elementType}_${elementId}`;
    this.metrics.buttonClicks[key] = (this.metrics.buttonClicks[key] || 0) + 1;

    this.log('Click tracked:', clickData);
  }

  trackFormSubmission(event) {
    const form = event.target;
    const formId = form.id || 'unknown';
    const formAction = form.action || 'unknown';

    const submissionData = {
      formId,
      formAction,
      timestamp: Date.now(),
      page: window.location.pathname
    };

    this.metrics.formSubmissions[formId] = (this.metrics.formSubmissions[formId] || 0) + 1;

    this.log('Form submission tracked:', submissionData);
  }

  // =============================================================================
  // PERFORMANCE TRACKING
  // =============================================================================

  setupPerformanceObserver() {
    if ('PerformanceObserver' in window) {
      // Track Long Tasks (> 50ms)
      const longTaskObserver = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          this.trackLongTask(entry);
        });
      });
      
      try {
        longTaskObserver.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        console.warn('Long task observer not supported');
      }

      // Track Navigation Timing
      const navigationObserver = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          this.trackNavigationTiming(entry);
        });
      });
      
      try {
        navigationObserver.observe({ entryTypes: ['navigation'] });
      } catch (e) {
        console.warn('Navigation observer not supported');
      }
    }
  }

  trackLongTask(entry) {
    const longTaskData = {
      duration: entry.duration,
      startTime: entry.startTime,
      timestamp: Date.now()
    };

    this.metrics.renderTimes.longTasks = this.metrics.renderTimes.longTasks || [];
    this.metrics.renderTimes.longTasks.push(longTaskData);

    this.log('Long task detected:', longTaskData);
  }

  trackNavigationTiming(entry) {
    const navigationData = {
      domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
      loadComplete: entry.loadEventEnd - entry.loadEventStart,
      domInteractive: entry.domInteractive - entry.domLoading,
      firstPaint: this.getFirstPaint(),
      firstContentfulPaint: this.getFirstContentfulPaint()
    };

    this.metrics.renderTimes.navigation = navigationData;
    this.log('Navigation timing:', navigationData);
  }

  getFirstPaint() {
    if (window.performance && window.performance.getEntriesByType) {
      const paintEntries = window.performance.getEntriesByType('paint');
      const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
      return firstPaint ? firstPaint.startTime : 0;
    }
    return 0;
  }

  getFirstContentfulPaint() {
    if (window.performance && window.performance.getEntriesByType) {
      const paintEntries = window.performance.getEntriesByType('paint');
      const firstContentfulPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');
      return firstContentfulPaint ? firstContentfulPaint.startTime : 0;
    }
    return 0;
  }

  // =============================================================================
  // API CALL TRACKING
  // =============================================================================

  trackApiCall(url, method, duration, status, error = null) {
    const apiCallData = {
      url,
      method,
      duration,
      status,
      error,
      timestamp: Date.now()
    };

    const key = `${method}_${url}`;
    if (!this.metrics.apiCallDurations[key]) {
      this.metrics.apiCallDurations[key] = [];
    }
    this.metrics.apiCallDurations[key].push(apiCallData);

    if (error || status >= 400) {
      this.metrics.apiErrors.push(apiCallData);
    }

    this.log('API call tracked:', apiCallData);
  }

  // Axios interceptor for automatic API tracking
  setupAxiosInterceptors() {
    // Request interceptor
    axios.interceptors.request.use(
      (config) => {
        config.metadata = { startTime: Date.now() };
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    axios.interceptors.response.use(
      (response) => {
        const duration = Date.now() - response.config.metadata.startTime;
        this.trackApiCall(
          response.config.url,
          response.config.method.toUpperCase(),
          duration,
          response.status
        );
        return response;
      },
      (error) => {
        if (error.config && error.config.metadata) {
          const duration = Date.now() - error.config.metadata.startTime;
          this.trackApiCall(
            error.config.url,
            error.config.method.toUpperCase(),
            duration,
            error.response?.status || 0,
            error.message
          );
        }
        return Promise.reject(error);
      }
    );
  }

  // =============================================================================
  // ERROR TRACKING
  // =============================================================================

  trackJSError(event) {
    const errorData = {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error?.stack,
      timestamp: Date.now(),
      page: window.location.pathname,
      userAgent: navigator.userAgent
    };

    this.metrics.jsErrors.push(errorData);
    this.log('JS Error tracked:', errorData);
  }

  trackPromiseRejection(event) {
    const errorData = {
      reason: event.reason,
      promise: event.promise,
      timestamp: Date.now(),
      page: window.location.pathname
    };

    this.metrics.jsErrors.push(errorData);
    this.log('Promise rejection tracked:', errorData);
  }

  trackCustomError(error, context = {}) {
    const errorData = {
      message: error.message || String(error),
      stack: error.stack,
      context,
      timestamp: Date.now(),
      page: window.location.pathname
    };

    this.metrics.jsErrors.push(errorData);
    this.log('Custom error tracked:', errorData);
  }

  // =============================================================================
  // BUSINESS METRICS
  // =============================================================================

  trackUserAction(action, data = {}) {
    const actionData = {
      action,
      data,
      timestamp: Date.now(),
      page: window.location.pathname,
      sessionId: this.getSessionId()
    };

    this.metrics.userActions[action] = (this.metrics.userActions[action] || 0) + 1;
    this.log('User action tracked:', actionData);
  }

  trackConversion(conversionType, value = 1, data = {}) {
    const conversionData = {
      type: conversionType,
      value,
      data,
      timestamp: Date.now(),
      page: window.location.pathname
    };

    if (!this.metrics.conversions[conversionType]) {
      this.metrics.conversions[conversionType] = { count: 0, totalValue: 0 };
    }
    this.metrics.conversions[conversionType].count++;
    this.metrics.conversions[conversionType].totalValue += value;

    this.log('Conversion tracked:', conversionData);
  }

  trackFeatureUsage(feature, data = {}) {
    const usageData = {
      feature,
      data,
      timestamp: Date.now(),
      page: window.location.pathname
    };

    this.metrics.featureUsage[feature] = (this.metrics.featureUsage[feature] || 0) + 1;
    this.log('Feature usage tracked:', usageData);
  }

  // =============================================================================
  // WEB VITALS
  // =============================================================================

  measureWebVitals() {
    // Import web-vitals library functions
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS((metric) => {
        this.metrics.webVitals.cls = metric.value;
        this.log('CLS measured:', metric.value);
      });

      getFID((metric) => {
        this.metrics.webVitals.fid = metric.value;
        this.log('FID measured:', metric.value);
      });

      getFCP((metric) => {
        this.metrics.webVitals.fcp = metric.value;
        this.log('FCP measured:', metric.value);
      });

      getLCP((metric) => {
        this.metrics.webVitals.lcp = metric.value;
        this.log('LCP measured:', metric.value);
      });

      getTTFB((metric) => {
        this.metrics.webVitals.ttfb = metric.value;
        this.log('TTFB measured:', metric.value);
      });
    }).catch((error) => {
      console.warn('Web vitals not available:', error);
    });
  }

  // =============================================================================
  // SYSTEM INFO
  // =============================================================================

  getBrowserInfo() {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      screen: {
        width: window.screen.width,
        height: window.screen.height,
        colorDepth: window.screen.colorDepth
      }
    };
  }

  getDeviceInfo() {
    return {
      deviceMemory: navigator.deviceMemory || 'unknown',
      hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
      maxTouchPoints: navigator.maxTouchPoints || 0,
      devicePixelRatio: window.devicePixelRatio || 1
    };
  }

  getConnectionInfo() {
    if ('connection' in navigator) {
      return {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt,
        saveData: navigator.connection.saveData
      };
    }
    return { type: 'unknown' };
  }

  // =============================================================================
  // UTILITIES
  // =============================================================================

  getSessionId() {
    let sessionId = sessionStorage.getItem('metricsSessionId');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('metricsSessionId', sessionId);
    }
    return sessionId;
  }

  trackVisibilityChange() {
    if (document.hidden) {
      this.log('Page hidden');
    } else {
      this.log('Page visible');
      this.trackPageView(); // Count as new page view when returning to tab
    }
  }

  startMetricsCollection() {
    // Start collecting periodic metrics
    setInterval(() => {
      this.collectPeriodicMetrics();
    }, 10000); // Every 10 seconds
  }

  collectPeriodicMetrics() {
    // Memory usage
    if ('memory' in performance) {
      this.metrics.memoryUsage = {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
        timestamp: Date.now()
      };
    }

    // Connection status
    this.metrics.connectionInfo = this.getConnectionInfo();
  }

  // =============================================================================
  // METRICS TRANSMISSION
  // =============================================================================

  sendMetrics() {
    const payload = {
      timestamp: Date.now(),
      sessionId: this.getSessionId(),
      page: window.location.pathname,
      metrics: this.metrics
    };

    // Send to backend
    this.sendToBackend(payload);

    // Reset counters but keep cumulative data
    this.resetTransientMetrics();
  }

  async sendToBackend(payload) {
    try {
      const response = await fetch(this.config.backendUrl + this.config.metricsEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      this.log('Metrics sent successfully');
    } catch (error) {
      this.log('Failed to send metrics:', error);
      // Store metrics locally for retry
      this.storeMetricsLocally(payload);
    }
  }

  storeMetricsLocally(payload) {
    try {
      const stored = localStorage.getItem('unsent_metrics') || '[]';
      const unsentMetrics = JSON.parse(stored);
      unsentMetrics.push(payload);
      
      // Keep only last 50 unsent metric batches
      if (unsentMetrics.length > 50) {
        unsentMetrics.splice(0, unsentMetrics.length - 50);
      }
      
      localStorage.setItem('unsent_metrics', JSON.stringify(unsentMetrics));
    } catch (error) {
      console.warn('Failed to store metrics locally:', error);
    }
  }

  resetTransientMetrics() {
    // Reset metrics that should not accumulate
    this.metrics.apiCallDurations = {};
    this.metrics.jsErrors = [];
    this.metrics.apiErrors = [];
    this.metrics.pageLoadTimes = [];
  }

  log(...args) {
    if (this.config.debugMode) {
      console.log('[FrontendMetrics]', ...args);
    }
  }
}

// =============================================================================
// REACT HOOKS FOR EASY INTEGRATION
// =============================================================================

// Custom React hooks for tracking metrics
export const useMetrics = () => {
  const [metricsInstance, setMetricsInstance] = React.useState(null);

  React.useEffect(() => {
    const metrics = new FrontendMetrics({
      debugMode: process.env.NODE_ENV === 'development'
    });
    
    metrics.setupAxiosInterceptors();
    setMetricsInstance(metrics);

    return () => {
      // Cleanup if needed
    };
  }, []);

  return metricsInstance;
};

export const usePageTracking = () => {
  const metrics = useMetrics();

  React.useEffect(() => {
    if (metrics) {
      metrics.trackPageView();
    }
  }, [window.location.pathname, metrics]);
};

// Higher-order component for automatic tracking
export const withMetrics = (WrappedComponent) => {
  return function MetricsWrapper(props) {
    const metrics = useMetrics();

    const trackClick = (eventName, data) => {
      if (metrics) {
        metrics.trackUserAction(eventName, data);
      }
    };

    const trackError = (error, context) => {
      if (metrics) {
        metrics.trackCustomError(error, context);
      }
    };

    const trackFeature = (feature, data) => {
      if (metrics) {
        metrics.trackFeatureUsage(feature, data);
      }
    };

    return (
      <WrappedComponent
        {...props}
        trackClick={trackClick}
        trackError={trackError}
        trackFeature={trackFeature}
        metrics={metrics}
      />
    );
  };
};

// =============================================================================
// USAGE EXAMPLES
// =============================================================================

/*
// Initialize metrics in your main App component
const App = () => {
  const metrics = useMetrics();
  
  const handleLogin = async (credentials) => {
    try {
      const response = await api.login(credentials);
      metrics.trackConversion('user_login', 1);
      metrics.trackUserAction('login_success');
    } catch (error) {
      metrics.trackCustomError(error, { action: 'login' });
    }
  };

  const handlePurchase = (orderData) => {
    metrics.trackConversion('purchase', orderData.total, {
      items: orderData.items.length,
      paymentMethod: orderData.paymentMethod
    });
  };

  return <div>Your App Content</div>;
};

// Use in components
const ProductPage = withMetrics(({ trackClick, trackFeature }) => {
  const handleAddToCart = () => {
    trackClick('add_to_cart', { productId: 123 });
    trackFeature('shopping_cart');
  };

  return (
    <button onClick={handleAddToCart}>
      Add to Cart
    </button>
  );
});
*/

export default FrontendMetrics;