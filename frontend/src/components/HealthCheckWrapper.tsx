// Client component wrapper for health check functionality
'use client';

import { useHealthCheck } from '@/hooks/useHealthCheck';
import { ServerDown } from '@/components/ServerDown';

export function HealthCheckWrapper({ children }: { children: React.ReactNode }) {
  // Health check with configurable thresholds
  const { isHealthy, consecutiveFailures, lastCheckTime, error, checkNow } = useHealthCheck({
    checkInterval: 10000,      // Check every 10 seconds
    failureThreshold: 2,       // Mark as down after 2 consecutive failures (20 seconds total)
    timeout: 3000,             // 3 second timeout per check
    endpoint: '/'              // Check root endpoint for server availability
  });

  // Show ServerDown component if backend is unhealthy
  if (!isHealthy) {
    return (
      <ServerDown 
        onRetry={checkNow}
        consecutiveFailures={consecutiveFailures}
        lastCheckTime={lastCheckTime}
        error={error}
      />
    );
  }

  return <>{children}</>;
}
