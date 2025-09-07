// React Hooks for Frontend Metrics
// Easy integration with React components

import { useState, useEffect, useContext, createContext } from 'react';
import FrontendMetrics from '../utils/metrics';

// Metrics Context for sharing across components
const MetricsContext = createContext(null);

// Provider component
export const MetricsProvider = ({ children, config = {} }) => {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const metricsInstance = new FrontendMetrics(config);
    setMetrics(metricsInstance);

    return () => {
      // Cleanup if needed
      if (metricsInstance) {
        metricsInstance.sendMetrics();
      }
    };
  }, []);

  return (
    <MetricsContext.Provider value={metrics}>
      {children}
    </MetricsContext.Provider>
  );
};

// Hook to use metrics in any component
export const useMetrics = () => {
  const metrics = useContext(MetricsContext);
  if (!metrics) {
    console.warn('useMetrics must be used within a MetricsProvider');
  }
  return metrics;
};

// Hook for page tracking
export const usePageTracking = () => {
  const metrics = useMetrics();

  useEffect(() => {
    if (metrics) {
      metrics.trackPageView(window.location.pathname);
    }
  }, [window.location.pathname, metrics]);
};

// Hook for API call tracking
export const useApiTracking = () => {
  const metrics = useMetrics();

  const trackApiCall = (url, method, startTime, response, error = null) => {
    if (metrics) {
      const duration = Date.now() - startTime;
      const status = response?.status || (error ? 0 : 200);
      metrics.trackApiCall(url, method, duration, status, error?.message);
    }
  };

  return { trackApiCall };
};

// Hook for user action tracking
export const useActionTracking = () => {
  const metrics = useMetrics();

  const trackAction = (action, data = {}) => {
    if (metrics) {
      metrics.trackUserAction(action, data);
    }
  };

  const trackConversion = (type, value = 1) => {
    if (metrics) {
      metrics.trackConversion(type, value);
    }
  };

  const trackError = (error, context = {}) => {
    if (metrics) {
      metrics.trackError(error.message || String(error), context.filename, context.lineno);
    }
  };

  return { trackAction, trackConversion, trackError };
};

// Higher-order component for automatic metrics
export const withMetrics = (WrappedComponent) => {
  return function MetricsWrapper(props) {
    const metrics = useMetrics();
    const { trackAction, trackConversion, trackError } = useActionTracking();

    return (
      <WrappedComponent
        {...props}
        metrics={metrics}
        trackAction={trackAction}
        trackConversion={trackConversion}
        trackError={trackError}
      />
    );
  };
};