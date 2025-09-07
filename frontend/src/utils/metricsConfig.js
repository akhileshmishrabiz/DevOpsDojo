// Frontend Metrics Configuration
// Centralized configuration for easy customization

export const METRICS_CONFIG = {
  // Backend API configuration
  backend: {
    url: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000',
    metricsEndpoint: '/api/frontend-metrics',
    timeout: 5000
  },

  // Collection intervals
  collection: {
    sendInterval: 30000,      // Send metrics every 30 seconds
    heartbeatInterval: 60000, // Heartbeat every minute
    errorBatchSize: 10,       // Send errors immediately after 10 errors
    maxStoredEvents: 1000     // Maximum events to store locally
  },

  // Feature toggles
  features: {
    webVitals: true,          // Collect Web Vitals (LCP, FID, CLS)
    performanceAPI: true,     // Use Performance Observer API
    errorTracking: true,      // Track JavaScript errors
    userInteractions: true,   // Track clicks and form submissions
    pageViews: true,          // Track page navigation
    apiCalls: true,           // Track API call performance
    businessEvents: true      // Track custom business events
  },

  // Sampling rates (0.0 to 1.0)
  sampling: {
    pageViews: 1.0,          // Sample 100% of page views
    clicks: 1.0,             // Sample 100% of clicks
    errors: 1.0,             // Sample 100% of errors (never skip errors)
    apiCalls: 1.0,           // Sample 100% of API calls
    debugLogs: 0.1           // Sample 10% of debug events
  },

  // Privacy settings
  privacy: {
    anonymizeIPs: true,       // Anonymize IP addresses
    respectDNT: true,         // Respect Do Not Track header
    excludePII: true,         // Exclude personally identifiable information
    maxTextLength: 100        // Limit text content length in events
  },

  // Development settings
  development: {
    debugMode: process.env.NODE_ENV === 'development',
    verbose: process.env.REACT_APP_METRICS_VERBOSE === 'true',
    mockData: false,          // Use mock data instead of real events
    consoleOutput: true       // Log metrics to console
  },

  // Browser compatibility
  compatibility: {
    requirePerformanceAPI: false,  // Gracefully degrade without Performance API
    requireLocalStorage: false,    // Work without localStorage
    fallbackMode: true            // Enable fallback for older browsers
  },

  // Event categories for organization
  eventCategories: {
    USER_INTERACTION: 'user_interaction',
    PERFORMANCE: 'performance',
    ERROR: 'error',
    BUSINESS: 'business',
    SYSTEM: 'system',
    API: 'api'
  },

  // Metric thresholds for alerting
  thresholds: {
    pageLoadTime: 3000,       // Alert if page load > 3 seconds
    apiResponseTime: 5000,    // Alert if API response > 5 seconds
    errorRate: 0.05,          // Alert if error rate > 5%
    memoryUsage: 100 * 1024 * 1024, // Alert if memory > 100MB
    jsHeapSize: 50 * 1024 * 1024    // Alert if JS heap > 50MB
  },

  // Custom dimensions for enriching metrics
  dimensions: {
    // Static dimensions (set once)
    static: {
      app_version: process.env.REACT_APP_VERSION || '1.0.0',
      environment: process.env.NODE_ENV || 'production',
      build_id: process.env.REACT_APP_BUILD_ID || 'unknown',
      deploy_date: process.env.REACT_APP_DEPLOY_DATE || new Date().toISOString().split('T')[0]
    },
    
    // Dynamic dimensions (calculated at runtime)
    dynamic: {
      screen_resolution: () => `${window.screen.width}x${window.screen.height}`,
      viewport_size: () => `${window.innerWidth}x${window.innerHeight}`,
      device_memory: () => navigator.deviceMemory || 'unknown',
      connection_type: () => navigator.connection?.effectiveType || 'unknown',
      user_agent_family: () => getBrowserFamily(),
      timezone: () => Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: () => navigator.language || 'en-US'
    }
  }
};

// Helper function to determine browser family
function getBrowserFamily() {
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (userAgent.includes('chrome')) return 'chrome';
  if (userAgent.includes('firefox')) return 'firefox';
  if (userAgent.includes('safari')) return 'safari';
  if (userAgent.includes('edge')) return 'edge';
  if (userAgent.includes('opera')) return 'opera';
  
  return 'unknown';
}

// Environment-specific overrides
if (process.env.NODE_ENV === 'development') {
  METRICS_CONFIG.collection.sendInterval = 10000; // Send more frequently in dev
  METRICS_CONFIG.development.verbose = true;
}

if (process.env.NODE_ENV === 'production') {
  METRICS_CONFIG.sampling.debugLogs = 0.01; // Sample less debug logs in prod
  METRICS_CONFIG.development.consoleOutput = false;
}

// Feature detection and graceful degradation
export const BROWSER_SUPPORT = {
  performanceObserver: 'PerformanceObserver' in window,
  intersectionObserver: 'IntersectionObserver' in window,
  webVitals: 'PerformanceObserver' in window && 'PerformanceEntry' in window,
  localStorage: (() => {
    try {
      localStorage.setItem('test', 'test');
      localStorage.removeItem('test');
      return true;
    } catch {
      return false;
    }
  })(),
  fetch: 'fetch' in window,
  sendBeacon: 'sendBeacon' in navigator
};

// Export individual config sections for easier importing
export const {
  backend: BACKEND_CONFIG,
  collection: COLLECTION_CONFIG,
  features: FEATURE_FLAGS,
  sampling: SAMPLING_CONFIG,
  privacy: PRIVACY_CONFIG,
  development: DEV_CONFIG,
  thresholds: THRESHOLD_CONFIG,
  dimensions: DIMENSIONS_CONFIG
} = METRICS_CONFIG;

export default METRICS_CONFIG;