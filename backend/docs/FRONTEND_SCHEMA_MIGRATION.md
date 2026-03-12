# Frontend Schema Migration Guide

This document details all changes made to the backend API to align with `core_schema.sql`. Frontend developers should update their code accordingly.

---

## 📋 Summary of Changes

| Component | Change Type | Impact Level |
|-----------|-------------|--------------|
| Users API | Schema Update | 🟡 Medium |
| Transactions API | **Breaking Change** | 🔴 High |
| Admins API | Schema Update | 🟡 Medium |
| Audit Logs API | Schema Update | 🟢 Low |

---

## 🔴 BREAKING CHANGES

### 1. Transaction Schema - Complete Restructure

The Transaction model has been completely rewritten from an aggregated statistics model to individual transaction records.

#### Before (Old Schema)
```json
{
  "user_id": 123,  // Was PRIMARY KEY
  "full_name": "John Doe",
  "total_amount_1h": 5000.0,
  "txn_count_1h": 10,
  "unique_cp_1h": 5,
  "avg_amount_1h": 500.0,
  "max_amount_1h": 1000.0,
  "min_amount_1h": 100.0,
  // ... similar fields for 24h, 7d, 30d windows
  "incoming_outgoing_ratio_7d": 1.5,
  "calculated_at": "2024-01-01T00:00:00Z"
}
```

#### After (New Schema - core_schema.sql)
```json
{
  "transaction_id": 1001,  // NEW PRIMARY KEY
  "user_id": 123,          // Now FOREIGN KEY
  "timestamp": "2024-01-01T12:30:00Z",
  "amount": 500.0,
  "currency": "USD",
  "txn_type": "TRANSFER",
  "counterparty_id": 456,
  "is_fraud": 0  // 0 = not fraud, 1 = fraud
}
```

#### API Endpoint Changes

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| `GET /transactions/{user_id}` | `GET /transactions/{transaction_id}` | Now uses transaction_id |
| `GET /transactions/user/{user_id}` | `GET /transactions/user/{user_id}` | Returns list of transactions |
| - | `GET /transactions/type/{txn_type}` | **NEW** - Filter by type |
| - | `GET /transactions/fraud/all` | **NEW** - Get fraud transactions |
| - | `GET /transactions/filter/amount` | **NEW** - Filter by amount range |
| - | `GET /transactions/filter/date` | **NEW** - Filter by date range |
| - | `GET /transactions/stats/user/{user_id}` | **NEW** - Get user stats |

#### Action Required
1. Update all transaction-related API calls
2. Replace aggregated data displays with individual transaction lists
3. Update transaction creation to use new fields
4. Implement new filtering capabilities

---

## 🟡 MEDIUM IMPACT CHANGES

### 2. User Schema Changes

#### Added Fields
| Field | Type | Description |
|-------|------|-------------|
| `profile_pic` | `string` (nullable) | URL/path to user's profile picture |

#### Renamed/Clarified Fields
| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `entity_id` | `user_id` | Now BIGINT primary key |
| `applicant_name` | `username` | Changed field name |
| `is_blacklisted` | `blacklisted` | Simplified field name |
| `blacklist_reason` | - | **Removed** - Not in core_schema |
| `i_not_score` | `current_rps_not` | Renamed for clarity |
| `i_360_score` | `current_rps_360` | Renamed for clarity |
| `suspicious_score` | - | **Removed** - Use risk_category instead |
| `risk_level` | `risk_category` | Renamed |
| `account_status` | - | **Removed** - Use blacklisted boolean |

#### New User Response Schema
```json
{
  "user_id": 123456789,
  "uin": "ABCD1234567890EFGH12",
  "uin_hash": "abc123def456...",
  "username": "john_doe",
  "profile_pic": "https://example.com/profile.jpg",
  "email": "john@example.com",
  "phone": "1234567890",
  "date_of_birth": "1990-01-15T00:00:00Z",
  "address": "123 Main St, City",
  "occupation": "Software Engineer",
  "annual_income": 75000.0,
  "kyc_status": "verified",
  "kyc_verified_at": "2024-01-01T00:00:00Z",
  "signature_hash": "def789...",
  "credit_score": 750,
  "current_rps_not": 0.25,
  "current_rps_360": 0.35,
  "last_rps_calculation": "2024-01-01T00:00:00Z",
  "risk_category": "low",
  "blacklisted": false,
  "blacklisted_at": null,
  "version": 1,
  "time": 1704067200000,
  "diff": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Action Required
1. Update user display components to use new field names
2. Add profile picture display support
3. Update risk scoring displays (multiply by 100 for percentage)
4. Remove references to removed fields

### 3. Admin Schema Changes

#### Removed Fields
| Field | Notes |
|-------|-------|
| `is_active` | **Removed** - Not in core_schema.sql |

#### Updated Fields
| Field | Change |
|-------|--------|
| `role` | Changed from Enum to String ('admin' or 'superadmin') |

#### New Admin Response Schema
```json
{
  "id": 1,
  "username": "admin_user",
  "email": "admin@example.com",
  "role": "admin",  // String, not enum
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-15T12:00:00Z"
}
```

#### Action Required
1. Remove any UI elements that check/set `is_active`
2. Update role handling to work with string values

---

## 🟢 LOW IMPACT CHANGES

### 4. Audit Log Schema Changes

#### Removed Fields
| Field | Notes |
|-------|-------|
| `user_agent` | **Removed** - Not in core_schema.sql |

#### Action Required
- Remove any display of `user_agent` in audit log views

### 5. Compliance Alert Schema Changes

#### Removed Fields
| Field | Notes |
|-------|-------|
| `is_true_positive` | **Removed** - Not in core_schema.sql |
| `classified_at` | **Removed** - Use `acknowledged_at` instead |
| `classified_by` | **Removed** - Use `acknowledged_by` instead |
| `reviewed_at` | **Removed** - Use `acknowledged_at` instead |
| `reviewed_by` | **Removed** - Use `acknowledged_by` instead |

#### Classification Logic Change
- **Before**: Alerts were classified as true/false positives using `is_true_positive` field
- **After**: Use `status` field instead:
  - `status = 'resolved'` → Equivalent to true positive
  - `status = 'dismissed'` → Equivalent to false positive
  - `status = 'active'` or `'investigating'` → Pending review

#### Removed API Endpoints
| Endpoint | Notes |
|----------|-------|
| `GET /dashboard/alerts/unclassified` | **Removed** - Use status filtering instead |
| `POST /alerts/{id}/classify` | **Removed** - Use status update instead |

#### Action Required
1. Remove any UI for classifying alerts as true/false positive
2. Use alert status (resolved/dismissed) for classification purposes
3. Update any metrics displays that relied on is_true_positive
4. Replace unclassified alerts view with filtering by status='active'

---

## 📊 New API Endpoints

### Transactions

```http
# Get all transactions
GET /transactions
GET /transactions/all

# Get single transaction
GET /transactions/{transaction_id}

# Get transactions by user
GET /transactions/user/{user_id}

# Get transactions by type
GET /transactions/type/{txn_type}

# Get fraud transactions
GET /transactions/fraud/all

# Filter by amount
GET /transactions/filter/amount?min_amount=100&max_amount=10000

# Filter by date
GET /transactions/filter/date?start_date=2024-01-01&end_date=2024-01-31

# Get user transaction stats
GET /transactions/stats/user/{user_id}

# Create transaction
POST /transactions/add
{
  "transaction_id": 1001,
  "user_id": 123,
  "timestamp": "2024-01-01T12:30:00Z",
  "amount": 500.0,
  "currency": "USD",
  "txn_type": "TRANSFER",
  "counterparty_id": 456,
  "is_fraud": 0
}

# Update transaction
PATCH /transactions/{transaction_id}

# Delete transaction
DELETE /transactions/{transaction_id}
```

### Users

```http
# Get users by risk category
GET /user/risk/{risk_category}

# Get blacklisted users
GET /user/blacklisted/all
```

---

## 🗄️ Database Schema Reference

### Users Table
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    uin CHAR(20),
    uin_hash CHAR(64),
    username VARCHAR(100),
    profile_pic TEXT,
    email VARCHAR(255),
    phone VARCHAR(15),
    date_of_birth TIMESTAMP,
    address TEXT,
    occupation VARCHAR(200),
    annual_income DOUBLE PRECISION,
    kyc_status VARCHAR(100),
    kyc_verified_at TIMESTAMP,
    signature_hash VARCHAR(64),
    credit_score INT,
    blacklisted BOOLEAN DEFAULT FALSE,
    blacklisted_at TIMESTAMP,
    current_rps_not DOUBLE PRECISION,
    current_rps_360 DOUBLE PRECISION,
    last_rps_calculation TIMESTAMP,
    risk_category VARCHAR(100),
    version INT DEFAULT 1,
    created_at TIMESTAMP,
    time BIGINT,
    diff INT,
    updated_at TIMESTAMP
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    timestamp TIMESTAMP,
    amount DOUBLE PRECISION,
    currency VARCHAR(10),
    txn_type VARCHAR(50),
    counterparty_id BIGINT,
    is_fraud INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

### Admins Table
```sql
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    CHECK (role IN ('admin', 'superadmin'))
);
```

### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_description TEXT NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    target_identifier VARCHAR(255),
    action_metadata JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
);
```

---

## 🔧 Migration Checklist

### High Priority
- [ ] Update Transaction API calls to use new endpoints
- [ ] Update Transaction data models/interfaces
- [ ] Replace aggregated transaction displays with individual transaction lists
- [ ] Update User field names in API calls and displays

### Medium Priority
- [ ] Add profile picture display support for users
- [ ] Update risk score displays (RPS scores are 0-1, multiply by 100 for %)
- [ ] Remove `is_active` from admin displays
- [ ] Update role handling for admins

### Low Priority
- [ ] Remove `user_agent` display from audit logs
- [ ] Implement new transaction filtering features
- [ ] Add new transaction statistics endpoints

---

## 📝 TypeScript Interface Updates

### User Interface
```typescript
interface User {
  user_id: number;
  uin?: string;
  uin_hash?: string;
  username?: string;
  profile_pic?: string;
  email?: string;
  phone?: string;
  date_of_birth?: string;
  address?: string;
  occupation?: string;
  annual_income?: number;
  kyc_status?: string;
  kyc_verified_at?: string;
  signature_hash?: string;
  credit_score?: number;
  current_rps_not?: number;
  current_rps_360?: number;
  last_rps_calculation?: string;
  risk_category?: string;
  blacklisted: boolean;
  blacklisted_at?: string;
  version?: number;
  time?: number;
  diff?: number;
  created_at?: string;
  updated_at?: string;
}
```

### Transaction Interface
```typescript
interface Transaction {
  transaction_id: number;
  user_id: number;
  timestamp?: string;
  amount?: number;
  currency?: string;
  txn_type?: string;
  counterparty_id?: number;
  is_fraud?: number;  // 0 or 1
}
```

### Admin Interface
```typescript
interface Admin {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'superadmin';
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}
```

### Audit Log Interface
```typescript
interface AuditLog {
  id: number;
  admin_id: number;
  admin_username?: string;
  admin_email?: string;
  action_type: string;
  action_description: string;
  target_type?: string;
  target_id?: number;
  target_identifier?: string;
  metadata?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}
```

---

## ⚠️ Important Notes

1. **Transaction Primary Key Change**: The transaction table now uses `transaction_id` as the primary key instead of `user_id`. This is a fundamental change that affects all transaction-related operations.

2. **RPS Scores**: Risk scores (`current_rps_not`, `current_rps_360`) are stored as floats between 0 and 1. Multiply by 100 to display as percentages.

3. **Fraud Detection**: Use `is_fraud` field (0 or 1) for fraud status instead of calculated scores.

4. **Pagination**: All list endpoints support `skip` and `limit` query parameters for pagination.

5. **Date Format**: All timestamps are in ISO 8601 format.

---

## 📞 Support

If you have questions about these changes, please contact the backend team.

**Last Updated**: $(date)
**Schema Version**: core_schema.sql v1.0

