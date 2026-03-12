// Health check hook to monitor backend server availability
import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export interface HealthCheckConfig {
  checkInterval?: number;      // Interval between health checks in ms (default: 30000 - 30 seconds)
  failureThreshold?: number;    // Number of consecutive failures before marking server as down (default: 3)
  timeout?: number;             // Request timeout in ms (default: 5000 - 5 seconds)
  endpoint?: string;            // Health check endpoint (default: '/health')
}

export interface HealthCheckState {
  isHealthy: boolean;
  isChecking: boolean;
  consecutiveFailures: number;
  lastCheckTime: Date | null;
  error: Error | null;
}

const DEFAULT_CONFIG: Required<HealthCheckConfig> = {
  checkInterval: 30000,      // Check every 30 seconds
  failureThreshold: 3,       // Mark as down after 3 consecutive failures
  timeout: 5000,             // 5 second timeout
  endpoint: '/'              // Use root endpoint or '/' for basic connectivity check
};

/**
 * Hook to monitor backend server health
 * Returns the current health state and a manual check function
 */
export function useHealthCheck(config: HealthCheckConfig = {}) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };
  
  const [state, setState] = useState<HealthCheckState>({
    isHealthy: true,  // Start as healthy, will check immediately
    isChecking: true, // Start in checking state
    consecutiveFailures: 0,
    lastCheckTime: null,
    error: null,
  });

  const consecutiveFailuresRef = useRef(0);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);
  const hasPerformedInitialCheck = useRef(false);

  const performHealthCheck = useCallback(async () => {
    setState(prev => ({ ...prev, isChecking: true }));

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), mergedConfig.timeout);

      const response = await fetch(`${API_BASE_URL}${mergedConfig.endpoint}`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      clearTimeout(timeoutId);

      // Accept both successful responses (200-299) and redirects (300-399)
      // Some APIs return 404 at root but are still running
      if (response.ok || response.status === 404 || response.status === 405) {
        // Health check successful - server is responding
        consecutiveFailuresRef.current = 0;
        setState({
          isHealthy: true,
          isChecking: false,
          consecutiveFailures: 0,
          lastCheckTime: new Date(),
          error: null,
        });
      } else {
        // Server responded but with error status
        throw new Error(`Health check failed with status: ${response.status}`);
      }
    } catch (error) {
      // Health check failed - could be network error, timeout, or server down
      consecutiveFailuresRef.current += 1;
      const err = error instanceof Error ? error : new Error('Health check failed');
      
      const isServerDown = consecutiveFailuresRef.current >= mergedConfig.failureThreshold;
      
      setState({
        isHealthy: !isServerDown,
        isChecking: false,
        consecutiveFailures: consecutiveFailuresRef.current,
        lastCheckTime: new Date(),
        error: err,
      });

      console.warn(
        `Health check failed (${consecutiveFailuresRef.current}/${mergedConfig.failureThreshold}):`,
        err.message
      );
    }
  }, [mergedConfig.endpoint, mergedConfig.timeout, mergedConfig.failureThreshold]);

  // Set up periodic health checks
  useEffect(() => {
    // Perform initial check immediately on mount
    performHealthCheck();

    // Set up interval for periodic checks
    timeoutIdRef.current = setInterval(() => {
      performHealthCheck();
    }, mergedConfig.checkInterval);

    // Cleanup on unmount
    return () => {
      if (timeoutIdRef.current) {
        clearInterval(timeoutIdRef.current);
      }
    };
  }, [performHealthCheck, mergedConfig.checkInterval]);

  // Manual check function
  const checkNow = useCallback(() => {
    performHealthCheck();
  }, [performHealthCheck]);

  return {
    ...state,
    checkNow,
    config: mergedConfig,
  };
}
