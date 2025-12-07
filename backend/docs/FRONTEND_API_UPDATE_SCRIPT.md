# Frontend API Update Script

This document provides the exact changes needed for the frontend to work with the updated backend API.

---

## 🔴 Immediate Action Required

### Issue 1: `/dashboard/alerts/unclassified` returning 404

**Status**: ✅ Fixed in backend

The endpoint is now available at: `GET /dashboard/alerts/unclassified`

**Request:**
```
GET /dashboard/alerts/unclassified?limit=50&severity=all
```

**Response:**
```json
{
  "total": 10,
  "alerts": [
    {
      "id": 1,
      "user_id": 123,
      "user_name": "john_doe",
      "transaction_id": 456,
      "alert_type": "fraud_alert",
      "severity": "high",
      "title": "Suspicious Transaction",
      "description": "...",
      "entity_id": "...",
      "rps360": 0.75,
      "status": "active",
      "priority": "high",
      "triggered_at": "2024-01-15T12:00:00",
      "created_at": "2024-01-15T12:00:00"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

### Issue 2: `/compliance/alerts` returning 404

**Status**: ✅ Fixed in backend

The endpoint is now available at: `GET /compliance/alerts`

**Request:**
```
GET /compliance/alerts?limit=50&severity=all&status=active
```

**Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "alert_type": "fraud_alert",
      "severity": "high",
      "title": "Suspicious Transaction",
      "description": "...",
      "user_id": 123,
      "user_name": "john_doe",
      "transaction_id": 456,
      "entity_id": "...",
      "entity_type": "user",
      "rps360": 0.75,
      "priority": "high",
      "source": "system",
      "triggered_by": "rule_engine",
      "alert_metadata": null,
      "triggered_at": "2024-01-15T12:00:00",
      "status": "active",
      "is_acknowledged": false,
      "acknowledged_at": null,
      "acknowledged_by": null,
      "dismissal_reason": null,
      "created_at": "2024-01-15T12:00:00",
      "updated_at": "2024-01-15T12:00:00"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

---

## 📋 Complete Endpoint Mapping

### Compliance Alerts Endpoints

| Frontend Call | Backend Endpoint | Method | Notes |
|---------------|------------------|--------|-------|
| Get active alerts | `/compliance/alerts?status=active` | GET | Use status filter |
| Get all alerts | `/compliance/alerts` | GET | Supports pagination |
| Get single alert | `/compliance/alerts/{id}` | GET | - |
| Update alert | `/compliance/alerts/{id}` | PATCH | Admin auth required |
| Acknowledge alert | `/compliance/alerts/{id}/acknowledge` | POST | Admin auth required |
| Resolve alert (true positive) | `/compliance/alerts/{id}/resolve` | POST | Admin auth required |
| Dismiss alert (false positive) | `/compliance/alerts/{id}/dismiss` | POST | Admin auth required |
| Get alert stats | `/compliance/alerts/stats/summary` | GET | - |

### Dashboard Alerts Endpoints

| Frontend Call | Backend Endpoint | Method | Notes |
|---------------|------------------|--------|-------|
| Get unclassified/pending alerts | `/dashboard/alerts/unclassified` | GET | Returns active/investigating |
| Get critical alerts | `/dashboard/critical-alerts` | GET | - |
| Get live alerts | `/dashboard/live-alerts` | GET | - |
| Dismiss alert | `/dashboard/alerts/{id}/dismiss` | POST | Admin auth required |

---

## 🔧 Frontend Code Changes Required

### 1. Update API Hook for Unclassified Alerts

If your frontend has code like:
```typescript
// OLD
const response = await fetch('/compliance/alerts?status=unclassified');
```

Change to:
```typescript
// NEW - Use status='active' for pending/unclassified alerts
const response = await fetch('/compliance/alerts?status=active&limit=50&severity=all');
// OR use the dashboard endpoint
const response = await fetch('/dashboard/alerts/unclassified?limit=50&severity=all');
```

### 2. Update Alert Classification Logic

**Old approach (removed):**
```typescript
// This no longer works - is_true_positive field was removed
await fetch(`/alerts/${alertId}/classify`, {
  method: 'POST',
  body: JSON.stringify({ is_true_positive: true })
});
```

**New approach:**
```typescript
// For TRUE POSITIVE - mark as resolved
await fetch(`/compliance/alerts/${alertId}/resolve`, {
  method: 'POST',
  body: JSON.stringify({ notes: 'Confirmed as valid alert' })
});

// For FALSE POSITIVE - mark as dismissed
await fetch(`/compliance/alerts/${alertId}/dismiss`, {
  method: 'POST', 
  body: JSON.stringify({ reason: 'False positive - no fraud detected' })
});
```

### 3. Update Alert Status Display

**Mapping from old to new:**

| Old Field | New Approach |
|-----------|--------------|
| `is_true_positive: true` | `status === 'resolved'` |
| `is_true_positive: false` | `status === 'dismissed'` |
| `is_true_positive: null` | `status === 'active'` or `'investigating'` |

### 4. TypeScript Interface Updates

```typescript
// Updated ComplianceAlert interface
interface ComplianceAlert {
  id: number;
  alert_type: string;
  severity: string;  // 'low' | 'medium' | 'high' | 'critical'
  title: string;
  description?: string;
  user_id?: number;
  user_name?: string;
  transaction_id?: number;
  entity_id?: string;
  entity_type?: string;
  rps360?: number;
  priority: string;
  source?: string;
  triggered_by?: string;
  alert_metadata?: string;
  triggered_at: string;
  status: string;  // 'active' | 'investigating' | 'resolved' | 'dismissed' | 'escalated'
  is_acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  dismissal_reason?: string;
  created_at: string;
  updated_at: string;
  // REMOVED: is_true_positive, classified_at, classified_by, reviewed_at, reviewed_by
}

// Response for list endpoints
interface AlertListResponse {
  total: number;
  items: ComplianceAlert[];  // or 'alerts' for dashboard endpoints
  limit: number;
  offset: number;
}
```

---

## 🧪 Testing the Endpoints

You can test the endpoints using curl:

```bash
# Get unclassified alerts
curl -X GET "http://localhost:8000/dashboard/alerts/unclassified?limit=50&severity=all"

# Get compliance alerts with status filter
curl -X GET "http://localhost:8000/compliance/alerts?limit=50&severity=all&status=active"

# Get alert stats
curl -X GET "http://localhost:8000/compliance/alerts/stats/summary"
```

---

## ⚠️ Important Notes

1. **Authentication Required**: All POST/PATCH endpoints require admin authentication via JWT token
2. **Status Values**: Use lowercase ('active', 'resolved', 'dismissed') not uppercase
3. **Severity Values**: Use lowercase ('low', 'medium', 'high', 'critical') or 'all'
4. **Pagination**: Both endpoints support `limit` and `offset` parameters

---

## 📞 Backend Changes Made

The following files were created/modified:

1. **NEW**: `app/routes/compliance_routes.py` - Full CRUD for compliance alerts
2. **UPDATED**: `app/routes/dashboard_routes.py` - Added `/alerts/unclassified` endpoint
3. **UPDATED**: `app/main.py` - Included compliance_routes

No changes to `core_schema.sql` were made.

