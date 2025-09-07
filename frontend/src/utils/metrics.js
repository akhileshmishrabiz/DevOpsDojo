// Frontend Metrics Utility
// Simplified and organized for easy integration

class FrontendMetrics {
  constructor(config = {}) {
    this.config = {
      backendUrl: config.backendUrl || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
      sendInterval: config.sendInterval || 30000, // 30 seconds
      debugMode: config.debugMode || process.env.NODE_ENV === 'development',
      ...config
    };

    this.metrics = {
      pageViews: 0,
      buttonClicks: {},
      apiCalls: {},
      errors: [],
      userActions: {},
      conversions: {},
      sessionId: this.getSessionId()
    };

    this.init();
  }

  init() {
    this.setupEventListeners();
    this.trackPageView();
    this.startPeriodicCollection();
    
    // Send metrics periodically
    setInterval(() => this.sendMetrics(), this.config.sendInterval);
    
    // Send before page unload
    window.addEventListener('beforeunload', () => this.sendMetrics());
    
    this.log('Frontend metrics initialized');
  }

  setupEventListeners() {
    // Track clicks
    document.addEventListener('click', (event) => {
      this.trackClick(event);
    });

    // Track JavaScript errors
    window.addEventListener('error', (event) => {
      this.trackError(event.message, event.filename, event.lineno);
    });

    // Track promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.trackError(`Unhandled promise rejection: ${event.reason}`);
    });
  }

  // =============================================================================
  // CORE TRACKING METHODS
  // =============================================================================

  trackPageView(page = window.location.pathname) {
    this.metrics.pageViews++;
    this.log('Page view tracked:', page);
  }

  trackClick(event) {
    const element = event.target;
    const elementType = element.tagName.toLowerCase();
    const elementId = element.id || 'unknown';
    const elementText = element.textContent?.slice(0, 30) || 'unknown';

    const key = `${elementType}_${elementId}`;
    this.metrics.buttonClicks[key] = (this.metrics.buttonClicks[key] || 0) + 1;

    this.log('Click tracked:', { elementType, elementId, elementText });
  }

  trackApiCall(url, method, duration, status, error = null) {
    const key = `${method}_${url}`;
    if (!this.metrics.apiCalls[key]) {
      this.metrics.apiCalls[key] = { count: 0, totalDuration: 0, errors: 0 };
    }
    
    this.metrics.apiCalls[key].count++;
    this.metrics.apiCalls[key].totalDuration += duration;
    
    if (error || status >= 400) {
      this.metrics.apiCalls[key].errors++;
    }

    this.log('API call tracked:', { url, method, duration, status, error });
  }

  trackError(message, filename = '', lineno = 0) {
    const errorData = {
      message,
      filename,
      lineno,
      timestamp: Date.now(),
      page: window.location.pathname,
      userAgent: navigator.userAgent
    };

    this.metrics.errors.push(errorData);
    this.log('Error tracked:', errorData);
  }

  trackUserAction(action, data = {}) {
    this.metrics.userActions[action] = (this.metrics.userActions[action] || 0) + 1;
    this.log('User action tracked:', { action, data });
  }

  trackConversion(type, value = 1) {
    if (!this.metrics.conversions[type]) {
      this.metrics.conversions[type] = { count: 0, totalValue: 0 };
    }
    this.metrics.conversions[type].count++;
    this.metrics.conversions[type].totalValue += value;
    
    this.log('Conversion tracked:', { type, value });
  }

  // =============================================================================
  // UTILITY METHODS
  // =============================================================================

  getSessionId() {
    let sessionId = sessionStorage.getItem('metricsSessionId');
    if (!sessionId) {
      sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('metricsSessionId', sessionId);
    }
    return sessionId;
  }

  startPeriodicCollection() {
    // Collect basic browser metrics every 30 seconds
    setInterval(() => {
      this.collectBrowserMetrics();
    }, 30000);
  }

  collectBrowserMetrics() {
    // Memory usage (if available)
    if ('memory' in performance) {
      this.metrics.memoryUsage = {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        timestamp: Date.now()
      };
    }

    // Connection info (if available)
    if ('connection' in navigator) {
      this.metrics.connectionInfo = {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      };
    }
  }

  // =============================================================================
  // DATA TRANSMISSION
  // =============================================================================

  async sendMetrics() {
    const payload = {
      timestamp: Date.now(),
      sessionId: this.metrics.sessionId,
      page: window.location.pathname,
      metrics: this.metrics
    };

    try {
      const response = await fetch(`${this.config.backendUrl}/api/frontend-metrics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        this.log('Metrics sent successfully');
        this.resetTransientMetrics();
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      this.log('Failed to send metrics:', error);
      // Could store locally for retry
    }
  }

  resetTransientMetrics() {
    // Reset metrics that shouldn't accumulate
    this.metrics.errors = [];
    this.metrics.apiCalls = {};
  }

  log(...args) {
    if (this.config.debugMode) {
      console.log('[FrontendMetrics]', ...args);
    }
  }
}

export default FrontendMetrics;