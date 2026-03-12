// Custom hooks for API data fetching
import { useState, useEffect, useCallback } from 'react';
import { 
  userApi, 
  transactionApi, 
  dashboardApi,
  User as ApiUser,
  Transaction as ApiTransaction,
  DashboardSummary,
  RiskDistribution,
  FlaggedTransaction
} from '../lib/api';
import { 
  transformApiUserToComponent, 
  transformApiTransactionToComponent,
  generateUserEventsFromTransactions,
  ComponentUser,
  ComponentTransaction
} from '../lib/transformers';

// ==================== TYPE DEFINITIONS ====================

export interface UseApiStateOptions {
  autoFetch?: boolean;
  onError?: (error: Error) => void;
}

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

// ==================== GENERIC API STATE HOOK ====================

export function useApiState<T>(
  initialData: T | null = null
): [ApiState<T>, (asyncFn: () => Promise<T>) => Promise<void>, () => void] {
  const [state, setState] = useState<ApiState<T>>({
    data: initialData,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (asyncFn: () => Promise<T>) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await asyncFn();
      setState({ data: result, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('An error occurred');
      setState({ data: null, loading: false, error: err });
      console.error('API Error:', err);
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: initialData, loading: false, error: null });
  }, [initialData]);

  return [state, execute, reset];
}

// ==================== USER HOOKS ====================

/**
 * Hook to fetch and manage list of users with client-side filtering
 */
export function useUsers(params?: { 
  q?: string;
  kyc_status?: string;
  riskCategory?: string;
  blacklisted?: boolean;
  skip?: number; 
  limit?: number;
}) {
  const [state, setState] = useState<ApiState<ComponentUser[]>>({
    data: null,
    loading: true,
    error: null,
  });

  // Stringify params for stable dependency tracking
  const paramsKey = JSON.stringify(params || {});

  const fetchUsers = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // Fetch all users (backend only supports skip/limit)
      const users = await userApi.getUsers({ skip: params?.skip, limit: params?.limit || 1000 });
      let transformedUsers = users.map(user => transformApiUserToComponent(user));
      
      // Apply client-side filters
      if (params?.q) {
        const searchLower = params.q.toLowerCase();
        transformedUsers = transformedUsers.filter(user => 
          user.name.toLowerCase().includes(searchLower) ||
          user.email.toLowerCase().includes(searchLower)
        );
      }
      
      if (params?.kyc_status && params.kyc_status !== 'all') {
        const kycStatus = params.kyc_status.charAt(0).toUpperCase() + params.kyc_status.slice(1).toLowerCase();
        transformedUsers = transformedUsers.filter(user => user.kycStatus === kycStatus);
      }
      
      if (params?.riskCategory && params.riskCategory !== 'all') {
        const riskLevel = params.riskCategory.charAt(0).toUpperCase() + params.riskCategory.slice(1).toLowerCase();
        transformedUsers = transformedUsers.filter(user => user.riskLevel === riskLevel);
      }
      
      if (params?.blacklisted !== undefined) {
        transformedUsers = transformedUsers.filter(user => 
          params.blacklisted ? user.accountStatus === 'Suspended' : user.accountStatus === 'Active'
        );
      }
      
      setState({ data: transformedUsers, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch users');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]); // Use stringified params for stable comparison

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return {
    users: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchUsers,
  };
}

/**
 * Hook to fetch single user with transaction statistics
 */
export function useUser(userId: number | null) {
  const [state, setState] = useState<ApiState<ComponentUser>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchUser = useCallback(async () => {
    if (!userId) {
      setState({ data: null, loading: false, error: null });
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // Fetch user data and their transaction statistics
      const user = await userApi.getUser(userId);
      
      let events: ReturnType<typeof generateUserEventsFromTransactions> = [];
      try {
        const transactionResponse = await transactionApi.getUserTransactions(userId, { limit: 20 });
        const transactions = transactionResponse.items || [];
        events = generateUserEventsFromTransactions(transactions, userId);
      } catch (txError) {
        // If transactions fail, continue with empty events
        console.warn('Failed to fetch transactions for user:', txError);
      }
      
      const transformedUser = transformApiUserToComponent(user, events);
      
      setState({ data: transformedUser, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch user');
      setState({ data: null, loading: false, error: err });
    }
  }, [userId]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return {
    user: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchUser,
  };
}

/**
 * Hook for user management actions (suspend, update, delete)
 */
export function useUserActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const suspendUser = useCallback(async (userId: number, reason: string = 'Account suspended by admin') => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await userApi.suspendUser(userId, reason);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to suspend user');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const unsuspendUser = useCallback(async (userId: number, reason: string = 'Account restored by admin') => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await userApi.unsuspendUser(userId, reason);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to unsuspend user');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const updateUser = useCallback(async (userId: number, data: Partial<ApiUser>) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await userApi.updateUser(userId, data);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to update user');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const deleteUser = useCallback(async (userId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await userApi.deleteUser(userId);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to delete user');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const createUser = useCallback(async (data: Partial<ApiUser>) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await userApi.createUser(data);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create user');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    suspendUser,
    unsuspendUser,
    updateUser,
    deleteUser,
    createUser,
    loading,
    error,
  };
}

// ==================== TRANSACTION HOOKS ====================

/**
 * Hook to fetch individual transactions (updated for new backend schema)
 * Returns individual transaction records, not aggregations
 */
export function useTransactions(params?: { 
  skip?: number; 
  limit?: number;
  user_id?: number; // Optional filter by user
}) {
  const [state, setState] = useState<ApiState<ApiTransaction[]>>({
    data: null,
    loading: true,
    error: null,
  });

  // Stringify params for stable dependency tracking
  const paramsKey = JSON.stringify(params || {});

  const fetchTransactions = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // Fetch individual transactions from new API
      const response = await transactionApi.getTransactions({ 
        skip: params?.skip, 
        limit: params?.limit || 100 
      });
      
      // Extract items from response
      const transactions = response.items || [];
      
      setState({ data: transactions, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch transactions');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  return {
    transactions: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchTransactions,
  };
}

/**
 * Hook to fetch transactions for a specific user
 * Returns individual transaction records for the user
 */
export function useUserTransactionStats(userId: number | null) {
  const [state, setState] = useState<ApiState<ApiTransaction[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchTransactionStats = useCallback(async () => {
    if (!userId) {
      setState({ data: null, loading: false, error: null });
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await transactionApi.getUserTransactions(userId, { limit: 100 });
      const transactions = response.items || [];
      setState({ data: transactions, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch user transactions');
      setState({ data: null, loading: false, error: err });
    }
  }, [userId]);

  useEffect(() => {
    fetchTransactionStats();
  }, [fetchTransactionStats]);

  return {
    transactionStats: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchTransactionStats,
  };
}

/**
 * @deprecated Use useUserTransactionStats instead
 * Maintained for backward compatibility
 */
export function useTransaction(transactionId: number | null) {
  console.warn('useTransaction is deprecated. Use useUserTransactionStats with user_id instead.');
  return useUserTransactionStats(transactionId);
}

/**
 * Hook for transaction actions
 * Note: Transaction creation endpoint may not be available in the new schema
 * Transactions are typically created by the backend transaction processing system
 */
export function useTransactionActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // ❌ Transaction creation is typically handled by the backend, not frontend
  // This is kept for backward compatibility but may not work with new schema
  const createTransaction = useCallback(async (data: Partial<ApiTransaction>) => {
    console.warn('Transaction creation endpoint may not be available. Transactions are typically created by backend systems.');
    setLoading(true);
    setError(null);
    
    try {
      // Note: This endpoint likely doesn't exist in the new backend
      throw new Error('Transaction creation not supported in new schema');
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create transaction');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    createTransaction,
    loading,
    error,
  };
}

// ==================== DASHBOARD HOOKS ====================

/**
 * Hook to fetch dashboard summary data
 */
export function useDashboard() {
  const [state, setState] = useState<ApiState<{
    summary: DashboardSummary;
    riskDistribution: RiskDistribution;
    flaggedTransactions: FlaggedTransaction[];
  }>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchDashboard = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const [summary, riskDistribution, flaggedTransactions] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getRiskDistribution(),
        dashboardApi.getFlaggedTransactions(10),
      ]);
      
      setState({
        data: { summary, riskDistribution, flaggedTransactions },
        loading: false,
        error: null,
      });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch dashboard data');
      setState({ data: null, loading: false, error: err });
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    summary: state.data?.summary || null,
    riskDistribution: state.data?.riskDistribution || null,
    flaggedTransactions: state.data?.flaggedTransactions || null,
    loading: state.loading,
    error: state.error,
    refetch: fetchDashboard,
  };
}

/**
 * Hook to fetch risk distribution
 */
export function useRiskDistribution() {
  const [state, setState] = useState<ApiState<RiskDistribution>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchRiskDistribution = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await dashboardApi.getRiskDistribution();
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch risk distribution');
      setState({ data: null, loading: false, error: err });
    }
  }, []);

  useEffect(() => {
    fetchRiskDistribution();
  }, [fetchRiskDistribution]);

  return {
    riskDistribution: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchRiskDistribution,
  };
}

/**
 * Hook to fetch flagged transactions
 */
export function useFlaggedTransactions(limit: number = 10) {
  const [state, setState] = useState<ApiState<FlaggedTransaction[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchFlaggedTransactions = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const data = await dashboardApi.getFlaggedTransactions(limit);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch flagged transactions');
      setState({ data: null, loading: false, error: err });
    }
  }, [limit]);

  useEffect(() => {
    fetchFlaggedTransactions();
  }, [fetchFlaggedTransactions]);

  return {
    flaggedTransactions: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchFlaggedTransactions,
  };
}

// ==================== ALERT HOOKS ====================

/**
 * Hook to fetch critical alerts
 */
export function useCriticalAlerts(params?: {
  limit?: number;
  severity?: string;
  hours?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').CriticalAlert[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchAlerts = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { alertApi } = await import('../lib/api');
      const data = await alertApi.getCriticalAlerts(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch critical alerts');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return {
    alerts: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchAlerts,
  };
}

/**
 * Hook to fetch live alerts with polling support
 */
export function useLiveAlerts(params?: {
  limit?: number;
  since?: string;
}, pollInterval?: number) {
  const [state, setState] = useState<ApiState<import('../lib/api').LiveAlert[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchAlerts = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { alertApi } = await import('../lib/api');
      const data = await alertApi.getLiveAlerts(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch live alerts');
      
      // In development, provide helpful hints
      if (process.env.NODE_ENV === 'development') {
        console.warn(
          '[useLiveAlerts] Failed to fetch alerts. '
          + 'If backend is not running, check DASHBOARD_BACKEND_REQUIREMENTS.md for setup instructions.'
        );
      }
      
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchAlerts();
    
    if (pollInterval && pollInterval > 0) {
      const interval = setInterval(fetchAlerts, pollInterval);
      return () => clearInterval(interval);
    }
  }, [fetchAlerts, pollInterval]);

  return {
    alerts: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchAlerts,
  };
}

/**
 * Hook to fetch alert trend data
 */
export function useAlertTrend(params?: {
  period?: string;
  interval?: string;
  severity?: string;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').AlertTrendResponse>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchTrend = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { alertApi } = await import('../lib/api');
      const data = await alertApi.getAlertTrend(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch alert trend');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchTrend();
  }, [fetchTrend]);

  return {
    trend: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchTrend,
  };
}

/**
 * Hook to fetch compliance alerts with filtering
 */
export function useComplianceAlerts(params?: {
  limit?: number;
  severity?: string;
  status?: string;
  skip?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').ComplianceAlertListResponse>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchAlerts = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { alertApi } = await import('../lib/api');
      const data = await alertApi.getComplianceAlerts(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch compliance alerts');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return {
    alerts: state.data?.items || null,
    total: state.data?.total || 0,
    loading: state.loading,
    error: state.error,
    refetch: fetchAlerts,
  };
}

/**
 * Hook to fetch unclassified alerts (alerts pending review)
 * Uses GET /dashboard/alerts/unclassified endpoint
 * Returns active/investigating alerts
 * 
 * Classification logic:
 * - status = 'resolved' → Equivalent to true positive
 * - status = 'dismissed' → Equivalent to false positive
 * - status = 'active' or 'investigating' → Pending review
 */
export function useUnclassifiedAlerts(params?: {
  limit?: number;
  skip?: number;
  severity?: string;
  status?: string;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').UnclassifiedAlertsResponse>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchAlerts = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { alertApi } = await import('../lib/api');
      const data = await alertApi.getUnclassifiedAlerts(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch unclassified alerts');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return {
    alerts: state.data?.alerts || null,
    total: state.data?.total || 0,
    loading: state.loading,
    error: state.error,
    refetch: fetchAlerts,
  };
}

/**
 * Hook for alert actions (dismiss, resolve, acknowledge, update)
 */
export function useAlertActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const dismissAlert = useCallback(async (alertId: string, request?: import('../lib/api').AlertDismissRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const { alertApi } = await import('../lib/api');
      const result = await alertApi.dismissAlert(alertId, request);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to dismiss alert');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const updateComplianceAlert = useCallback(async (alertId: number, update: import('../lib/api').ComplianceAlertUpdate) => {
    setLoading(true);
    setError(null);
    
    try {
      const { alertApi } = await import('../lib/api');
      const result = await alertApi.updateComplianceAlert(alertId, update);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to update alert');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const acknowledgeComplianceAlert = useCallback(async (alertId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const { alertApi } = await import('../lib/api');
      const result = await alertApi.acknowledgeComplianceAlert(alertId);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to acknowledge alert');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const resolveComplianceAlert = useCallback(async (alertId: number, notes?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const { alertApi } = await import('../lib/api');
      const result = await alertApi.resolveComplianceAlert(alertId, notes);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to resolve alert');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  const dismissComplianceAlert = useCallback(async (alertId: number, reason?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const { alertApi } = await import('../lib/api');
      const result = await alertApi.dismissComplianceAlert(alertId, reason);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to dismiss alert');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  // ❌ REMOVED: Alert classification is no longer supported in backend
  // const markAlert = useCallback(async (alertId: number, isPositive: boolean, notes?: string) => {
  //   setLoading(true);
  //   setError(null);
  //   
  //   try {
  //     const { alertApi } = await import('../lib/api');
  //     const result = await alertApi.markAlert(alertId, {
  //       is_true_positive: isPositive,
  //       notes,
  //     });
  //     setLoading(false);
  //     return result;
  //   } catch (err) {
  //     const error = err instanceof Error ? err : new Error('Failed to mark alert');
  //     setError(error);
  //     setLoading(false);
  //     throw error;
  //   }
  // }, []);

  return {
    dismissAlert,
    updateComplianceAlert,
    acknowledgeComplianceAlert,
    resolveComplianceAlert,
    dismissComplianceAlert,
    loading,
    error,
  };
}

// ==================== TOXICITY HISTORY HOOKS ====================

/**
 * Hook to fetch toxicity history for a user
 */
export function useToxicityHistory(userId: number | null, params?: {
  skip?: number;
  limit?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').ToxicityHistory[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchToxicityHistory = useCallback(async () => {
    if (!userId) {
      setState({ data: null, loading: false, error: null });
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { toxicityHistoryApi } = await import('../lib/api');
      const data = await toxicityHistoryApi.getToxicityHistory(userId, params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch toxicity history');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, paramsKey]);

  useEffect(() => {
    fetchToxicityHistory();
  }, [fetchToxicityHistory]);

  return {
    toxicityHistory: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchToxicityHistory,
  };
}

/**
 * Hook for toxicity history actions (create)
 */
export function useToxicityHistoryActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createToxicityHistory = useCallback(async (
    userId: number, 
    data: import('../lib/api').CreateToxicityHistoryRequest
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const { toxicityHistoryApi } = await import('../lib/api');
      const result = await toxicityHistoryApi.createToxicityHistory(userId, data);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create toxicity history');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    createToxicityHistory,
    loading,
    error,
  };
}

// ==================== USER SANCTION MATCHES HOOKS ====================

/**
 * Hook to fetch sanction matches for a user
 */
export function useUserSanctionMatches(userId: number | null, params?: {
  skip?: number;
  limit?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').UserSanctionMatch[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchSanctionMatches = useCallback(async () => {
    if (!userId) {
      setState({ data: null, loading: false, error: null });
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { userSanctionMatchApi } = await import('../lib/api');
      const data = await userSanctionMatchApi.getSanctionMatches(userId, params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch sanction matches');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, paramsKey]);

  useEffect(() => {
    fetchSanctionMatches();
  }, [fetchSanctionMatches]);

  return {
    sanctionMatches: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchSanctionMatches,
  };
}

/**
 * Hook for sanction match actions (create)
 */
export function useUserSanctionMatchActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createSanctionMatch = useCallback(async (
    userId: number, 
    data: import('../lib/api').CreateUserSanctionMatchRequest
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const { userSanctionMatchApi } = await import('../lib/api');
      const result = await userSanctionMatchApi.createSanctionMatch(userId, data);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create sanction match');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    createSanctionMatch,
    loading,
    error,
  };
}

// ==================== SUPERADMIN MONITORING HOOKS ====================

/**
 * Hook to fetch superadmin dashboard
 */
export function useSuperadminDashboard(days: number = 7) {
  const [state, setState] = useState<ApiState<import('../lib/api').SuperadminDashboard>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchDashboard = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getDashboard(days);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch superadmin dashboard');
      setState({ data: null, loading: false, error: err });
    }
  }, [days]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    dashboard: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchDashboard,
  };
}

/**
 * Hook to fetch superadmin audit logs
 */
export function useSuperadminAuditLogs(params?: {
  admin_id?: number;
  action_type?: string;
  target_type?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').AuditLog[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchAuditLogs = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getMonitoringAuditLogs(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch audit logs');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  return {
    auditLogs: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchAuditLogs,
  };
}

/**
 * Hook to fetch metrics summary
 */
export function useMetricsSummary(days: number = 7) {
  const [state, setState] = useState<ApiState<import('../lib/api').MetricsSummary>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchMetrics = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getMetricsSummary(days);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch metrics summary');
      setState({ data: null, loading: false, error: err });
    }
  }, [days]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return {
    metrics: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchMetrics,
  };
}

/**
 * Hook to fetch metrics history
 */
export function useMetricsHistory(params?: {
  metric_type?: string;
  metric_category?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').MetricHistory[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchHistory = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getMetricsHistory(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch metrics history');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return {
    history: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchHistory,
  };
}

/**
 * Hook to fetch alert resolution statistics
 */
export function useAlertResolutions(days: number = 30) {
  const [state, setState] = useState<ApiState<import('../lib/api').AlertResolutionStats>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchResolutions = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getAlertResolutions(days);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch alert resolutions');
      setState({ data: null, loading: false, error: err });
    }
  }, [days]);

  useEffect(() => {
    fetchResolutions();
  }, [fetchResolutions]);

  return {
    resolutions: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchResolutions,
  };
}

/**
 * Hook to fetch admin activity
 */
export function useAdminActivity(days: number = 30) {
  const [state, setState] = useState<ApiState<import('../lib/api').AdminActivity[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchActivity = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getAdminActivity(days);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch admin activity');
      setState({ data: null, loading: false, error: err });
    }
  }, [days]);

  useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  return {
    activity: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchActivity,
  };
}

/**
 * Hook to fetch health checks
 */
export function useHealthChecks(params?: {
  check_type?: string;
  component_name?: string;
  status?: string;
  severity?: string;
  is_resolved?: boolean;
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').HealthCheck[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchHealthChecks = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getHealthChecks(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch health checks');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchHealthChecks();
  }, [fetchHealthChecks]);

  return {
    healthChecks: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchHealthChecks,
  };
}

/**
 * Hook for health check actions
 */
export function useHealthCheckActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateHealthCheck = useCallback(async (
    healthId: number,
    data: import('../lib/api').UpdateHealthCheckRequest
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const { superadminApi } = await import('../lib/api');
      const result = await superadminApi.updateHealthCheck(healthId, data);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to update health check');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    updateHealthCheck,
    loading,
    error,
  };
}

/**
 * Hook to fetch system alerts
 */
export function useSystemAlerts(params?: {
  alert_type?: string;
  status?: string;
  severity?: string;
  component?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  const [state, setState] = useState<ApiState<import('../lib/api').SystemAlert[]>>({
    data: null,
    loading: true,
    error: null,
  });

  const paramsKey = JSON.stringify(params || {});

  const fetchSystemAlerts = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getSystemAlerts(params);
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch system alerts');
      setState({ data: null, loading: false, error: err });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  useEffect(() => {
    fetchSystemAlerts();
  }, [fetchSystemAlerts]);

  return {
    systemAlerts: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchSystemAlerts,
  };
}

/**
 * Hook for system alert actions
 */
export function useSystemAlertActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateSystemAlert = useCallback(async (
    alertId: number,
    data: import('../lib/api').UpdateSystemAlertRequest
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const { superadminApi } = await import('../lib/api');
      const result = await superadminApi.updateSystemAlert(alertId, data);
      setLoading(false);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to update system alert');
      setError(error);
      setLoading(false);
      throw error;
    }
  }, []);

  return {
    updateSystemAlert,
    loading,
    error,
  };
}

/**
 * Hook to fetch system status
 */
export function useSystemStatus() {
  const [state, setState] = useState<ApiState<import('../lib/api').SystemStatus>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchStatus = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const { superadminApi } = await import('../lib/api');
      const data = await superadminApi.getSystemStatus();
      setState({ data, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to fetch system status');
      setState({ data: null, loading: false, error: err });
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    status: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchStatus,
  };
}
