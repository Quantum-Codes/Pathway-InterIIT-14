// API service for Intelligent Fraud Detection & KYC System
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

// ==================== TYPE DEFINITIONS ====================

export interface User {
  user_id: number; // Primary key (changed from id)
  uin?: string; // User Identification Number (max 20 chars)
  uin_hash?: string; // Hashed UIN (max 64 chars)
  username?: string; // Username (max 100 chars)
  profile_pic?: string; // URL/path to user's profile picture (nullable)
  email?: string;
  phone?: string; // Max 15 chars (changed from 20)
  date_of_birth?: string;
  address?: string; // TEXT type (unlimited length)
  occupation?: string; // Max 200 chars
  annual_income?: number; // Changed from string to number (Float)
  kyc_status?: string; // Max 100 chars (changed from 20)
  kyc_verified_at?: string;
  signature_hash?: string; // Max 64 chars
  credit_score?: number; // Integer, range: 300-900
  blacklisted: boolean; // Replaces is_blacklisted
  blacklisted_at?: string | null;
  current_rps_not?: number; // Current RPS (Not) score in 0-1 format (display as-is)
  current_rps_360?: number; // Current RPS 360 score in 0-1 format (display as-is)
  last_rps_calculation?: string; // Last RPS calculation timestamp
  risk_category?: string; // Max 100 chars
  version?: number; // Version control field
  time?: number; // Pathway timestamp (BigInteger)
  diff?: number; // Pathway diff field
  created_at?: string;
  updated_at?: string;
}

// Individual transaction record - matches backend schema
export interface Transaction {
  transaction_id: number;       // BIGINT primary key
  user_id: number;              // BIGINT, references users.user_id
  timestamp: string;            // TIMESTAMP - when transaction occurred
  amount: number;               // DOUBLE PRECISION - transaction amount
  currency: string;             // VARCHAR(10) - currency code (e.g., 'INR')
  txn_type: string;            // VARCHAR(50) - transaction type (e.g., 'TRANSFER', 'DEPOSIT')
  counterparty_id: number | null; // BIGINT - other party in transaction
  is_fraud: number;            // INT (0 or 1) - fraud flag (use is_fraud === 1 to check)
}

// Transaction aggregation data (legacy interface, may be deprecated)
export interface TransactionAggregation {
  user_id: number; // Primary key (changed from id)
  full_name?: string; // User's full name (max 255 chars)
  
  // 1-Hour Window Aggregations
  total_amount_1h?: number;
  txn_count_1h?: number;
  unique_cp_1h?: number; // Unique counterparties
  avg_amount_1h?: number;
  max_amount_1h?: number;
  min_amount_1h?: number;
  
  // 24-Hour Window Aggregations
  total_amount_24h?: number;
  txn_count_24h?: number;
  unique_cp_24h?: number;
  avg_amount_24h?: number;
  max_amount_24h?: number;
  min_amount_24h?: number;
  
  // 7-Day Window Aggregations
  total_amount_7d?: number;
  txn_count_7d?: number;
  unique_cp_7d?: number;
  avg_amount_7d?: number;
  max_amount_7d?: number;
  min_amount_7d?: number;
  
  // 30-Day Window Aggregations
  total_amount_30d?: number;
  txn_count_30d?: number;
  unique_cp_30d?: number;
  avg_amount_30d?: number;
  max_amount_30d?: number;
  min_amount_30d?: number;
  
  // Ratio Features
  incoming_outgoing_ratio_7d?: number; // Ratio of incoming to outgoing transactions
  
  // Metadata
  calculated_at?: string; // When aggregations were last calculated
}

export interface DashboardSummary {
  total_users: number;
  total_transactions: number; // Sum of all transactions in last 30 days (changed from 7 days)
  fraudulent_transactions: number; // Changed from flagged_transactions - transactions where is_fraud = 1
  blacklisted_users: number;
  high_risk_users: number; // Users with risk_category = 'high'
  critical_risk_users: number; // Users with risk_category = 'critical'
  pending_kyc: number; // Users with kyc_status = 'pending'
  average_i360_score: number; // RPS 360 score in 0-1 format (display as-is)
  total_volume: number; // Total transaction volume in last 30 days
  average_i_not_score: number; // RPS NOT score in 0-1 format (display as-is)
}

export interface RiskDistribution {
  low_risk: number;
  medium_risk: number;
  high_risk: number;
  critical_risk: number;
}

// Fraudulent transaction (where is_fraud = 1)
export interface FlaggedTransaction {
  transaction_id: number;       // BIGINT
  user_id: number;              // BIGINT
  user_name: string;            // From joined user data
  timestamp: string;            // Transaction timestamp
  amount: number;
  currency: string;
  txn_type: string;            // Changed from transaction_type
  is_fraud: number;            // Will be 1 for flagged transactions
}

// ==================== ALERT TYPE DEFINITIONS ====================

export type AlertType = 
  | 'kyc_alert' 
  | 'transaction_alert' 
  | 'fraud_alert' 
  | 'aml_alert' 
  | 'sanction_alert' 
  | 'behavioral_alert' 
  | 'system_alert';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type AlertStatus = 
  | 'active' 
  | 'investigating' 
  | 'resolved' 
  | 'dismissed' 
  | 'escalated';

export type Priority = 'low' | 'medium' | 'high' | 'critical';

export interface CriticalAlert {
  id: number | string; // Backend returns number, but some code expects string
  alert_id: number;
  alert_type: AlertType;
  severity: Severity;
  title?: string;
  description: string | null;
  user_id: number;
  user_name: string | null;
  entity_id?: string | null;
  entity_type?: string | null;
  transaction_id: number | null;
  amount: number | null;
  rps360?: number; // RPS 360 score in 0-1 format (display as-is)
  status?: AlertStatus;
  priority?: Priority;
  triggered_at: string;
  time_ago_seconds?: number; // May not be in backend response
  is_acknowledged?: boolean;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  assigned_to?: string | null;
  dismissal_reason?: string | null;
  source?: string | null;
  triggered_by?: string | null;
  alert_metadata?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface LiveAlert {
  id: string;
  severity: Severity;
  triggered_at: string;
  time_display: string;
}

export interface AlertTrendDataPoint {
  timestamp: string;
  count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface AlertTrendResponse {
  period: string;
  interval: string;
  data_points: AlertTrendDataPoint[];
  total_alerts: number;
  avg_per_interval: number;
}

// Full compliance alert response (matches ComplianceAlertRead from backend)
export interface ComplianceAlert {
  id: number;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string | null;
  user_id: number | null;
  user_name: string | null;
  transaction_id: number | null;
  entity_id: string | null;
  entity_type: string | null;
  rps360: number | null;           // Risk score 0-1
  priority: string | null;
  source: string | null;
  triggered_by: string | null;
  alert_metadata: string | null;   // JSON string
  triggered_at: string;            // ISO datetime
  status: 'active' | 'investigating' | 'resolved' | 'dismissed' | 'escalated';
  is_acknowledged: boolean;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  dismissal_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplianceAlertListResponse {
  total: number;
  items: ComplianceAlert[];
  limit: number;
  offset: number;
}

// Top alerts response
export interface TopAlertsResponse {
  total_returned: number;
  k: number;
  status_filter: string;
  alerts: ComplianceAlertSummaryItem[];
}

export interface ComplianceAlertSummaryItem {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  description: string | null;
  user_id: number | null;
  user_name: string | null;
  transaction_id: number | null;
  entity_id: string | null;
  rps360: number | null;
  status: string;
  priority: string | null;
  triggered_at: string | null;
  created_at: string | null;
  is_acknowledged: boolean;
}

// Alerts summary statistics
export interface AlertsSummaryResponse {
  total: number;
  pending_review: number;
  active: number;
  investigating: number;
  resolved: number;
  dismissed: number;
  escalated: number;
  by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
}

export interface AlertDismissRequest {
  reason?: string;
  notes?: string;
}

export interface AlertDismissResponse {
  success: boolean;
  alert_id: string;
  dismissed_at: string;
  dismissed_by: string;
}

export interface ComplianceAlertUpdate {
  status?: 'active' | 'investigating' | 'resolved' | 'dismissed' | 'escalated';
  priority?: 'low' | 'medium' | 'high';
  is_acknowledged?: boolean;
  acknowledged_by?: string;
  dismissal_reason?: string;
}

export interface UnclassifiedAlertsResponse {
  total: number;
  alerts: CriticalAlert[];
  limit: number;
  offset: number;
}

// ❌ REMOVED: Alert classification is no longer supported in backend
// export interface MarkAlertRequest {
//   is_true_positive: boolean;
//   notes?: string;
// }
// export interface MarkAlertResponse {
//   success: boolean;
//   message: string;
//   alert_id: number;
//   is_true_positive: boolean;
//   reviewed_at: string;
//   reviewed_by: string;
// }

// ==================== TOXICITY HISTORY TYPE DEFINITIONS ====================

export interface ToxicityHistory {
  history_id: number;
  user_id: number;
  rps_not?: number; // RPS (Not) risk score in 0-1 format (display as-is)
  rps_360?: number; // RPS 360 risk score in 0-1 format (display as-is)
  sanction_score?: number; // Sanction list match score
  news_score?: number; // Negative news sentiment score
  transaction_score?: number; // Transaction pattern risk score
  portfolio_score?: number; // Portfolio composition risk score
  calculated_at: string; // Timestamp when scores were calculated
  calculation_trigger?: string; // What triggered the calculation
  time?: number; // Pathway timestamp
  diff?: number; // Pathway diff field
}

export interface CreateToxicityHistoryRequest {
  user_id: number;
  rps_not?: number; // RPS (Not) score in 0-1 format (backend expects 0-1, not percentage)
  rps_360?: number; // RPS 360 score in 0-1 format (backend expects 0-1, not percentage)
  sanction_score?: number;
  news_score?: number;
  transaction_score?: number;
  portfolio_score?: number;
  calculation_trigger?: string;
  time?: number;
  diff?: number;
}

// ==================== USER SANCTION MATCHES TYPE DEFINITIONS ====================

export interface UserSanctionMatch {
  match_id: number;
  user_id: number;
  match_found: boolean; // Boolean indicating if a match was found
  match_confidence?: number; // Confidence score of the match (0.0 to 1.0)
  matched_entity_name?: string | null; // Name of the matched entity from sanction list
  checked_at: string; // Timestamp when check was performed
  time?: number; // Pathway timestamp
  diff?: number; // Pathway diff field
}

export interface CreateUserSanctionMatchRequest {
  user_id: number;
  match_found: boolean;
  match_confidence?: number;
  matched_entity_name?: string | null;
  time?: number;
  diff?: number;
}

// ==================== API REQUEST HANDLER ====================

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log(`[API] Requesting: ${url}`);
  
  // Get authentication token from localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    console.log(`[API] Response status for ${endpoint}:`, response.status);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      
      // Provide helpful context for common error scenarios
      let errorMessage = errorData.detail || `API Error: ${response.status} ${response.statusText}`;
      
      if (response.status === 404) {
        errorMessage = `Endpoint not found: ${endpoint}. Backend may not be fully implemented yet.`;
        // Use console.warn for 404s (expected during development)
        console.warn(`[API] ${errorMessage}`);
      } else if (response.status >= 500) {
        errorMessage = `Server error (${response.status}). Please check backend logs.`;
        console.error(`[API] Error response for ${endpoint}:`, errorData);
      } else {
        // For other errors (400, 401, 403, etc.), log as error
        console.error(`[API] Error response for ${endpoint}:`, errorData);
      }
      
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    console.log(`[API] Success for ${endpoint}:`, data);
    return data;
  } catch (error) {
    // Check if it's a network error (fetch failed)
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      const networkError = new Error(
        `Network error: Cannot connect to backend at ${API_BASE_URL}. ` +
        `Please ensure the backend server is running and CORS is configured properly.`
      );
      console.error(`[API] Network error for ${endpoint}:`, networkError.message);
      throw networkError;
    }
    console.error(`[API] Request failed for ${endpoint}:`, error);
    throw error;
  }
}

// ==================== USER API ====================

export const userApi = {
  /**
   * Get all users with pagination
   * Endpoints: GET /users or GET /user/all
   * Note: Backend only supports skip and limit. Other filtering is done client-side.
   */
  getUsers: async (params?: {
    skip?: number;
    limit?: number;
  }): Promise<User[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/users${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<User[]>(endpoint);
  },

  /**
   * Get single user by ID
   * Endpoint: GET /users/{user_id}
   */
  getUser: async (userId: number): Promise<User> => {
    return apiRequest<User>(`/users/${userId}`);
  },

  /**
   * Create new user
   * Endpoint: POST /users
   */
  createUser: async (userData: Partial<User>): Promise<User> => {
    return apiRequest<User>('/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  /**
   * Update user (partial update)
   * Endpoint: PATCH /users/{user_id}
   */
  updateUser: async (userId: number, userData: Partial<User>): Promise<User> => {
    return apiRequest<User>(`/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(userData),
    });
  },

  /**
   * Delete user
   * Endpoint: DELETE /users/{user_id}
   */
  deleteUser: async (userId: number): Promise<{ ok: boolean }> => {
    return apiRequest<{ ok: boolean }>(`/users/${userId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Suspend user (blacklist)
   * Endpoint: POST /user/{user_id}/blacklist
   * Requires: Admin authentication and reason parameter
   */
  suspendUser: async (userId: number, reason: string = 'Account suspended by admin'): Promise<User> => {
    const encodedReason = encodeURIComponent(reason);
    return apiRequest<User>(`/user/${userId}/blacklist?reason=${encodedReason}`, {
      method: 'POST',
    });
  },

  /**
   * Unsuspend user (remove from blacklist)
   * Endpoint: POST /user/{user_id}/whitelist
   * Requires: Admin authentication and reason parameter
   */
  unsuspendUser: async (userId: number, reason: string = 'Account restored by admin'): Promise<User> => {
    const encodedReason = encodeURIComponent(reason);
    return apiRequest<User>(`/user/${userId}/whitelist?reason=${encodedReason}`, {
      method: 'POST',
    });
  },

  /**
   * Upload PDF KYC form with automatic data extraction
   * Endpoint: POST /user/upload-form
   * Requires: Admin authentication (require_admin)
   */
  uploadPdfForm: async (file: File): Promise<{
    success: boolean;
    user_id: number;
    extracted_data: Partial<User>;
    message: string;
  }> => {
    const formData = new FormData();
    formData.append('file', file);

    // Get authentication token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

    const response = await fetch(`${API_BASE_URL}/user/upload-form`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
      // Note: Don't set Content-Type header - browser will set it with boundary for multipart/form-data
    });

    // Try to parse the response body for logging and error handling.
    // If parsing fails (no JSON body), responseBody will be null.
    const responseBody = await response.json().catch(() => null);

    // Log the raw response for debugging/inspection.
    console.log('[API] uploadPdfForm response status:', response.status, 'body:', responseBody);

    if (!response.ok) {
      const errorData = responseBody || {};
      throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
    }

    return responseBody as {
      success: boolean;
      user_id: number;
      extracted_data: Partial<User>;
      message: string;
    };
  },

  /**
   * Get users by risk category
   * Endpoint: GET /user/risk/{risk_category}
   */
  getUsersByRiskCategory: async (riskCategory: string, params?: {
    skip?: number;
    limit?: number;
  }): Promise<User[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/user/risk/${riskCategory}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<User[]>(endpoint);
  },

  /**
   * Get blacklisted users
   * Endpoint: GET /user/blacklisted/all
   */
  getBlacklistedUsers: async (params?: {
    skip?: number;
    limit?: number;
  }): Promise<User[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/user/blacklisted/all${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<User[]>(endpoint);
  },
};

// ==================== TRANSACTION API ====================

export const transactionApi = {
  /**
   * Get all transactions with pagination
   * Endpoint: GET /transactions
   * Returns: Individual transaction records
   */
  getTransactions: async (params?: {
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Transaction[] }> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/transactions${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<{ total: number; items: Transaction[] }>(endpoint);
  },

  /**
   * Get transactions for a specific user
   * Endpoint: GET /transactions/user/{user_id}
   */
  getUserTransactions: async (userId: number, params?: {
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Transaction[] }> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/transactions/user/${userId}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<{ total: number; items: Transaction[] }>(endpoint);
  },

  /**
   * Get single transaction by ID
   * Endpoint: GET /transactions/{transaction_id}
   */
  getTransaction: async (transactionId: number): Promise<Transaction> => {
    return apiRequest<Transaction>(`/transactions/${transactionId}`);
  },

  /**
   * Get transactions by type
   * Endpoint: GET /transactions/type/{txn_type}
   */
  getTransactionsByType: async (txnType: string, params?: {
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Transaction[] }> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/transactions/type/${txnType}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<{ total: number; items: Transaction[] }>(endpoint);
  },

  /**
   * Get fraud transactions
   * Endpoint: GET /transactions/fraud/all
   */
  getFraudTransactions: async (params?: {
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Transaction[] }> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/transactions/fraud/all${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<{ total: number; items: Transaction[] }>(endpoint);
  },

  /**
   * Filter transactions by amount range
   * Endpoint: GET /transactions/filter/amount?min_amount=100&max_amount=10000
   */
  filterTransactionsByAmount: async (params: {
    min_amount: number;
    max_amount: number;
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Transaction[] }> => {
    const searchParams = new URLSearchParams({
      min_amount: params.min_amount.toString(),
      max_amount: params.max_amount.toString(),
    });
    
    if (params.skip !== undefined) {
      searchParams.append('skip', params.skip.toString());
    }
    if (params.limit !== undefined) {
      searchParams.append('limit', params.limit.toString());
    }
    
    return apiRequest<{ total: number; items: Transaction[] }>(`/transactions/filter/amount?${searchParams.toString()}`);
  },

  /**
   * Filter transactions by date range
   * Endpoint: GET /transactions/filter/date?start_date=2024-01-01&end_date=2024-01-31
   */
  filterTransactionsByDate: async (params: {
    start_date: string;
    end_date: string;
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; items: Transaction[] }> => {
    const searchParams = new URLSearchParams({
      start_date: params.start_date,
      end_date: params.end_date,
    });
    
    if (params.skip !== undefined) {
      searchParams.append('skip', params.skip.toString());
    }
    if (params.limit !== undefined) {
      searchParams.append('limit', params.limit.toString());
    }
    
    return apiRequest<{ total: number; items: Transaction[] }>(`/transactions/filter/date?${searchParams.toString()}`);
  },

  /**
   * Get user transaction statistics
   * Endpoint: GET /transactions/stats/user/{user_id}
   */
  getUserTransactionStats: async (userId: number): Promise<{
    total_transactions: number;
    total_amount: number;
    fraud_count: number;
    fraud_amount: number;
    avg_amount: number;
    max_amount: number;
    min_amount: number;
  }> => {
    return apiRequest(`/transactions/stats/user/${userId}`);
  },

  /**
   * Create a new transaction
   * Endpoint: POST /transactions/add
   */
  createTransaction: async (transaction: Partial<Transaction>): Promise<Transaction> => {
    return apiRequest<Transaction>('/transactions/add', {
      method: 'POST',
      body: JSON.stringify(transaction),
    });
  },

  /**
   * Update a transaction
   * Endpoint: PATCH /transactions/{transaction_id}
   */
  updateTransaction: async (transactionId: number, updates: Partial<Transaction>): Promise<Transaction> => {
    return apiRequest<Transaction>(`/transactions/${transactionId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  /**
   * Delete a transaction
   * Endpoint: DELETE /transactions/{transaction_id}
   */
  deleteTransaction: async (transactionId: number): Promise<{ ok: boolean }> => {
    return apiRequest<{ ok: boolean }>(`/transactions/${transactionId}`, {
      method: 'DELETE',
    });
  },
};

// ==================== DASHBOARD API ====================

export const dashboardApi = {
  /**
   * Get dashboard summary statistics
   * Endpoint: GET /dashboard/summary
   * Note: total_transactions now uses a 30-day window (changed from 7-day)
   * RPS scores (average_i360_score, average_i_not_score) are returned in 0-1 format (display as-is)
   */
  getSummary: async (): Promise<DashboardSummary> => {
    return apiRequest<DashboardSummary>('/dashboard/summary');
  },

  /**
   * Get risk distribution across user base
   * Endpoint: GET /dashboard/risk-distribution
   */
  getRiskDistribution: async (): Promise<RiskDistribution> => {
    return apiRequest<RiskDistribution>('/dashboard/risk-distribution');
  },

  /**
   * Get flagged transactions (suspicious_score > 50)
   * Endpoint: GET /dashboard/flagged-transactions
   */
  getFlaggedTransactions: async (limit?: number): Promise<FlaggedTransaction[]> => {
    const params = limit ? `?limit=${limit}` : '';
    return apiRequest<FlaggedTransaction[]>(`/dashboard/flagged-transactions${params}`);
  },
};

// ==================== ALERT API ====================

export const alertApi = {
  /**
   * Get critical alerts for dashboard
   * Endpoint: GET /dashboard/critical-alerts
   */
  getCriticalAlerts: async (params?: {
    limit?: number;
    severity?: string;
    hours?: number;
  }): Promise<CriticalAlert[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/dashboard/critical-alerts${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<CriticalAlert[]>(endpoint);
  },

  /**
   * Get live alerts for real-time monitoring
   * Endpoint: GET /dashboard/live-alerts
   */
  getLiveAlerts: async (params?: {
    limit?: number;
    since?: string;
  }): Promise<LiveAlert[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/dashboard/live-alerts${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<LiveAlert[]>(endpoint);
  },

  /**
   * Get alert trend data for visualization
   * Endpoint: GET /dashboard/alert-trend
   */
  getAlertTrend: async (params?: {
    period?: string;
    interval?: string;
    severity?: string;
  }): Promise<AlertTrendResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/dashboard/alert-trend${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<AlertTrendResponse>(endpoint);
  },

  /**
   * Dismiss an alert
   * Endpoint: POST /dashboard/alerts/{alert_id}/dismiss
   */
  dismissAlert: async (alertId: string, request?: AlertDismissRequest): Promise<AlertDismissResponse> => {
    return apiRequest<AlertDismissResponse>(`/dashboard/alerts/${alertId}/dismiss`, {
      method: 'POST',
      body: JSON.stringify(request || {}),
    });
  },

  /**
   * Get compliance alerts with filtering
   * Endpoint: GET /compliance/alerts
   */
  getComplianceAlerts: async (params?: {
    limit?: number;
    offset?: number;
    severity?: string;
    status?: string;
    alert_type?: string;
    user_id?: number;
  }): Promise<ComplianceAlertListResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/compliance/alerts${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<ComplianceAlertListResponse>(endpoint);
  },

  /**
   * Get single compliance alert
   * Endpoint: GET /compliance/alerts/{alert_id}
   */
  getComplianceAlert: async (alertId: number): Promise<ComplianceAlert> => {
    return apiRequest<ComplianceAlert>(`/compliance/alerts/${alertId}`);
  },

  /**
   * Get top K most critical alerts
   * Endpoint: GET /compliance/alerts/top
   */
  getTopAlerts: async (params?: {
    k?: number;
    status?: string;
  }): Promise<TopAlertsResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.k) searchParams.append('k', params.k.toString());
    if (params?.status) searchParams.append('status', params.status);
    
    const endpoint = `/compliance/alerts/top${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<TopAlertsResponse>(endpoint);
  },

  /**
   * Update compliance alert
   * Endpoint: PATCH /compliance/alerts/{alert_id}
   */
  updateComplianceAlert: async (alertId: number, update: ComplianceAlertUpdate): Promise<ComplianceAlert> => {
    return apiRequest<ComplianceAlert>(`/compliance/alerts/${alertId}`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    });
  },

  /**
   * Acknowledge a compliance alert
   * Endpoint: POST /compliance/alerts/{alert_id}/acknowledge
   */
  acknowledgeComplianceAlert: async (alertId: number): Promise<{
    success: boolean;
    alert_id: number;
    acknowledged_at: string;
    acknowledged_by: string;
  }> => {
    return apiRequest(`/compliance/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  },

  /**
   * Resolve a compliance alert (confirmed issue addressed)
   * Endpoint: POST /compliance/alerts/{alert_id}/resolve
   */
  resolveComplianceAlert: async (alertId: number, notes?: string): Promise<{
    success: boolean;
    message: string;
    alert_id: number;
    status: string;
    resolved_at: string;
    resolved_by: string;
  }> => {
    const params = notes ? `?notes=${encodeURIComponent(notes)}` : '';
    return apiRequest(`/compliance/alerts/${alertId}/resolve${params}`, {
      method: 'POST',
    });
  },

  /**
   * Dismiss a compliance alert (false positive / not actionable)
   * Endpoint: POST /compliance/alerts/{alert_id}/dismiss
   */
  dismissComplianceAlert: async (alertId: number, reason?: string): Promise<{
    success: boolean;
    message: string;
    alert_id: number;
    status: string;
    dismissed_at: string;
    dismissed_by: string;
    reason: string;
  }> => {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    return apiRequest(`/compliance/alerts/${alertId}/dismiss${params}`, {
      method: 'POST',
    });
  },

  /**
   * Get compliance alert statistics
   * Endpoint: GET /compliance/alerts/stats/summary
   */
  getComplianceAlertStats: async (): Promise<AlertsSummaryResponse> => {
    return apiRequest<AlertsSummaryResponse>('/compliance/alerts/stats/summary');
  },

  /**
   * Get unclassified alerts (alerts pending review)
   * Endpoint: GET /dashboard/alerts/unclassified
   * Returns active/investigating alerts
   */
  getUnclassifiedAlerts: async (params?: {
    limit?: number;
    skip?: number;
    severity?: string;
    status?: string;
  }): Promise<UnclassifiedAlertsResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/dashboard/alerts/unclassified${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<UnclassifiedAlertsResponse>(endpoint);
  },
};

// ==================== TOXICITY HISTORY API ====================

export const toxicityHistoryApi = {
  /**
   * Get toxicity history for a specific user
   * Endpoint: GET /users/{user_id}/toxicity-history
   */
  getToxicityHistory: async (userId: number, params?: {
    skip?: number;
    limit?: number;
  }): Promise<ToxicityHistory[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/users/${userId}/toxicity-history${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<ToxicityHistory[]>(endpoint);
  },

  /**
   * Create a new toxicity history record
   * Endpoint: POST /users/{user_id}/toxicity-history
   */
  createToxicityHistory: async (userId: number, data: CreateToxicityHistoryRequest): Promise<ToxicityHistory> => {
    return apiRequest<ToxicityHistory>(`/users/${userId}/toxicity-history`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// ==================== USER SANCTION MATCHES API ====================

export const userSanctionMatchApi = {
  /**
   * Get sanction match history for a specific user
   * Endpoint: GET /users/{user_id}/sanction-matches
   */
  getSanctionMatches: async (userId: number, params?: {
    skip?: number;
    limit?: number;
  }): Promise<UserSanctionMatch[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/users/${userId}/sanction-matches${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<UserSanctionMatch[]>(endpoint);
  },

  /**
   * Create a new sanction match record
   * Endpoint: POST /users/{user_id}/sanction-matches
   */
  createSanctionMatch: async (userId: number, data: CreateUserSanctionMatchRequest): Promise<UserSanctionMatch> => {
    return apiRequest<UserSanctionMatch>(`/users/${userId}/sanction-matches`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// ==================== UTILITY FUNCTIONS ====================

/**
 * Calculate risk category based on current_rps_360 score
 */
export function getRiskCategory(rps360Score?: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
  // DB now provides rps360 as a value between 0 and 1.
  // If score is missing (undefined/null) treat as LOW. A score of 0 is valid and LOW.
  if (rps360Score === undefined || rps360Score === null) return 'LOW';
  if (rps360Score < 0.3) return 'LOW';
  if (rps360Score < 0.6) return 'MEDIUM';
  if (rps360Score < 0.8) return 'HIGH';
  return 'CRITICAL';
}

/**
 * Get color class for risk category
 */
export function getRiskColor(category: string): string {
  const colors = {
    LOW: 'text-green-600 bg-green-100',
    MEDIUM: 'text-yellow-600 bg-yellow-100',
    HIGH: 'text-orange-600 bg-orange-100',
    CRITICAL: 'text-red-600 bg-red-100',
  };
  return colors[category as keyof typeof colors] || 'text-gray-600 bg-gray-100';
}

/**
 * Format currency amount
 */
export function formatCurrency(amount: number, currency: string = 'INR'): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format date to readable string
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

// ==================== AUTHENTICATION API ====================

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: 'admin' | 'superadmin';
  username: string;
}

export interface AdminInfo {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'superadmin';
  created_at: string;
  updated_at?: string;
  last_login_at: string | null;
}

export const authApi = {
  /**
   * Login with username and password
   * Endpoint: POST /api/auth/login
   */
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Invalid credentials');
    }
    
    const data = await response.json();
    
    // Store token and user info in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user_role', data.role);
      localStorage.setItem('username', data.username);
    }
    
    return data;
  },

  /**
   * Logout and clear stored credentials
   * Endpoint: POST /api/auth/logout
   */
  logout: async (): Promise<void> => {
    try {
      await apiRequest('/api/auth/logout', { method: 'POST' });
    } finally {
      // Clear localStorage even if API call fails
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('username');
      }
    }
  },

  /**
   * Get current admin information
   * Endpoint: GET /api/auth/me
   */
  getCurrentAdmin: async (): Promise<AdminInfo> => {
    return apiRequest<AdminInfo>('/api/auth/me');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem('access_token');
    return !!token;
  },

  /**
   * Get stored token
   */
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  /**
   * Get stored user role
   */
  getRole: (): 'admin' | 'superadmin' | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('user_role') as 'admin' | 'superadmin' | null;
  },

  /**
   * Get stored username
   */
  getUsername: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('username');
  },

  /**
   * Check if current user is superadmin
   */
  isSuperadmin: (): boolean => {
    return authApi.getRole() === 'superadmin';
  },
};

// ==================== SUPERADMIN API ====================

export interface CreateAdminRequest {
  username: string;
  email: string;
  password: string;
  role: 'admin' | 'superadmin';
}

export interface CreateAdminResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
  updated_at?: string;
}

export interface AuditLog {
  id: number;
  admin_id: number;
  admin_username: string | null;
  action_type: string;
  action_description: string;
  target_type: string | null;
  target_id: number | null;
  target_identifier: string | null;
  action_metadata: Record<string, any> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogsResponse {
  total: number;
  logs: AuditLog[];
  limit: number;
  offset: number;
}

export interface AdminListItem {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
  updated_at?: string;
  last_login_at: string | null;
}

// ==================== SUPERADMIN MONITORING API ====================

export interface MetricsSummary {
  resolution_rate: number;       // 0-100 (percentage of resolved alerts)
  avg_response_time_ms: number;  // >= 0 (milliseconds)
  api_error_rate: number;        // 0-100 (percentage)
  total_alerts: number;          // >= 0
  resolved: number;              // >= 0 (acknowledged alerts)
  unresolved: number;            // >= 0 (pending alerts)
  period_start: string;          // ISO datetime
  period_end: string;            // ISO datetime
}

export interface SystemAlert {
  id: number;
  alert_type: string;
  title: string;
  description: string;
  severity: 'critical' | 'error' | 'warning' | 'info';
  component: string | null;
  metric_type: string | null;
  threshold_value: string | null;
  actual_value: string | null;
  alert_data: Record<string, any> | null;
  status: 'active' | 'acknowledged' | 'resolved';
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  triggered_at: string;
  last_updated: string;
  notifications_sent: number;
}

export interface HealthCheck {
  id: number;
  check_type: string;
  component_name: string;
  status: 'healthy' | 'degraded' | 'failed' | 'recovering';
  severity: 'info' | 'warning' | 'error' | 'critical';
  error_type: string | null;
  error_message: string | null;
  request_context: Record<string, any> | null;
  response_context: Record<string, any> | null;
  response_time_ms: number | null;
  retry_count: number;
  affected_operations: string[] | null;
  user_impact: string | null;
  is_resolved: boolean;
  resolved_at: string | null;
  resolution_notes: string | null;
  auto_recovered: boolean;
  detected_at: string;
  last_occurrence: string;
  alert_sent: boolean;
}

// Compliance alert summary (fraud/AML alerts) for superadmin dashboard
export interface ComplianceAlertSummary {
  id: number;
  alert_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string | null;
  user_id: number | null;
  user_name: string | null;
  status: 'active' | 'investigating' | 'resolved' | 'dismissed' | 'escalated';
  priority: string | null;
  is_acknowledged: boolean;
  created_at: string;
  triggered_at: string | null;
}

export interface SuperadminDashboard {
  metrics_summary: MetricsSummary;
  unresolved_compliance_alerts: ComplianceAlertSummary[];
  active_system_alerts: SystemAlert[];
  recent_health_issues: HealthCheck[];
  recent_audit_logs: AuditLog[];
  system_status: 'healthy' | 'degraded' | 'critical';
}

export interface MetricHistory {
  id: number;
  metric_type: string;
  metric_category: string;
  metric_value: number;
  metric_unit: string;
  time_window: string;
  aggregation_period_start: string;
  aggregation_period_end: string;
  details: Record<string, any> | null;
  total_count: number | null;
  positive_count: number | null;
  negative_count: number | null;
  recorded_at: string;
  is_anomaly: boolean;
  anomaly_threshold: number | null;
}

export interface AlertResolutionStats {
  total_alerts: number;              // >= 0
  resolved: number;                  // >= 0 (acknowledged alerts)
  unresolved: number;                // >= 0 (pending alerts)
  escalated: number;                 // >= 0
  avg_resolution_time_hours: number; // >= 0
}

export interface AdminActivity {
  admin_id: number;
  admin_username: string;
  total_actions: number;
  alerts_reviewed: number;
  users_flagged: number;
  decisions_made: number;
  last_active: string;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'critical';
  critical_alerts: number;
  unresolved_errors: number;
  checked_at: string;
}

export interface UpdateHealthCheckRequest {
  status?: 'healthy' | 'degraded' | 'failed' | 'recovering';
  is_resolved?: boolean;
  resolution_notes?: string;
}

export interface UpdateSystemAlertRequest {
  status?: 'active' | 'acknowledged' | 'resolved';
  acknowledged_by?: string;
  resolution_notes?: string;
}

export const superadminApi = {
  /**
   * Create a new admin account (Superadmin only)
   * Endpoint: POST /api/auth/superadmin/create-admin
   */
  createAdmin: async (data: CreateAdminRequest): Promise<CreateAdminResponse> => {
    return apiRequest<CreateAdminResponse>('/api/auth/superadmin/create-admin', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get audit logs (Superadmin only)
   * Endpoint: GET /api/auth/superadmin/logs
   */
  getAuditLogs: async (params?: {
    admin_id?: number;
    action_type?: string;
    target_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditLogsResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/auth/superadmin/logs${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<AuditLogsResponse>(endpoint);
  },

  /**
   * List all admin accounts (Superadmin only)
   * Endpoint: GET /api/auth/superadmin/admins
   */
  listAdmins: async (): Promise<AdminListItem[]> => {
    const response = await apiRequest<{ admins: AdminListItem[] }>('/api/auth/superadmin/admins');
    return response.admins;
  },

  // ==================== MONITORING API ====================

  /**
   * Get complete superadmin dashboard
   * Endpoint: GET /api/superadmin/dashboard
   */
  getDashboard: async (days: number = 7): Promise<SuperadminDashboard> => {
    return apiRequest<SuperadminDashboard>(`/api/superadmin/dashboard?days=${days}`);
  },

  /**
   * Get superadmin audit logs with filters
   * Endpoint: GET /api/superadmin/audit-logs
   */
  getMonitoringAuditLogs: async (params?: {
    admin_id?: number;
    action_type?: string;
    target_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditLog[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/superadmin/audit-logs${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<AuditLog[]>(endpoint);
  },

  /**
   * Get specific audit log
   * Endpoint: GET /api/superadmin/audit-logs/{audit_id}
   */
  getAuditLog: async (auditId: number): Promise<AuditLog> => {
    return apiRequest<AuditLog>(`/api/superadmin/audit-logs/${auditId}`);
  },

  /**
   * Get metrics summary
   * Endpoint: GET /api/superadmin/metrics/summary
   */
  getMetricsSummary: async (days: number = 7): Promise<MetricsSummary> => {
    return apiRequest<MetricsSummary>(`/api/superadmin/metrics/summary?days=${days}`);
  },

  /**
   * Get metrics history
   * Endpoint: GET /api/superadmin/metrics/history
   */
  getMetricsHistory: async (params?: {
    metric_type?: string;
    metric_category?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<MetricHistory[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/superadmin/metrics/history${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<MetricHistory[]>(endpoint);
  },

  /**
   * Get alert resolution statistics
   * Endpoint: GET /api/superadmin/metrics/alert-resolutions
   */
  getAlertResolutions: async (days: number = 30): Promise<AlertResolutionStats> => {
    return apiRequest<AlertResolutionStats>(`/api/superadmin/metrics/alert-resolutions?days=${days}`);
  },

  /**
   * Get admin activity statistics
   * Endpoint: GET /api/superadmin/metrics/admin-activity
   */
  getAdminActivity: async (days: number = 30): Promise<AdminActivity[]> => {
    return apiRequest<AdminActivity[]>(`/api/superadmin/metrics/admin-activity?days=${days}`);
  },

  /**
   * Get health checks
   * Endpoint: GET /api/superadmin/health/checks
   */
  getHealthChecks: async (params?: {
    check_type?: string;
    component_name?: string;
    status?: string;
    severity?: string;
    is_resolved?: boolean;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<HealthCheck[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/superadmin/health/checks${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<HealthCheck[]>(endpoint);
  },

  /**
   * Update health check
   * Endpoint: PATCH /api/superadmin/health/checks/{health_id}
   */
  updateHealthCheck: async (healthId: number, data: UpdateHealthCheckRequest): Promise<HealthCheck> => {
    return apiRequest<HealthCheck>(`/api/superadmin/health/checks/${healthId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get system alerts
   * Endpoint: GET /api/superadmin/alerts
   */
  getSystemAlerts: async (params?: {
    alert_type?: string;
    status?: string;
    severity?: string;
    component?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<SystemAlert[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/superadmin/alerts${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiRequest<SystemAlert[]>(endpoint);
  },

  /**
   * Update system alert
   * Endpoint: PATCH /api/superadmin/alerts/{alert_id}
   */
  updateSystemAlert: async (alertId: number, data: UpdateSystemAlertRequest): Promise<SystemAlert> => {
    return apiRequest<SystemAlert>(`/api/superadmin/alerts/${alertId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get system status
   * Endpoint: GET /api/superadmin/system-status
   */
  getSystemStatus: async (): Promise<SystemStatus> => {
    return apiRequest<SystemStatus>('/api/superadmin/system-status');
  },
};
