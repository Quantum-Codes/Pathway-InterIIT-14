# Backend - Fraud Detection & Compliance API

A FastAPI-based backend for intelligent fraud detection and KYC compliance monitoring. This service provides REST APIs for user management, transaction monitoring, compliance checking, and alerts management.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Setup & Installation](#setup--installation)
4. [Environment Configuration](#environment-configuration)
5. [Running the Backend](#running-the-backend)
6. [API Endpoints](#api-endpoints)
7. [Database](#database)
8. [Models & Schemas](#models--schemas)
9. [Authentication](#authentication)
10. [Testing](#testing)

---


## Project Structure

```
backend/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── db.py                        # Database connection & configuration
│   │
│   ├── models/                      # SQLAlchemy ORM Models
│   │   ├── __init__.py
│   │   ├── user.py                  # User model
│   │   ├── transaction.py           # Transaction model
│   │   ├── alert.py                 # Alert model
│   │   ├── admin.py                 # Admin/SuperAdmin model
│   │   ├── audit_log.py             # Audit logging model
│   │   ├── toxicity_history.py      # Toxicity score history
│   │   ├── user_sanction_match.py   # Sanctions matching records
│   │   ├── system_metrics.py        # System performance metrics
│   │   └── system_health.py         # System health status
│   │
│   ├── routes/                      # API Route Handlers
│   │   ├── auth_routes.py           # Authentication endpoints
│   │   ├── user_routes.py           # User management endpoints
│   │   ├── transaction_routes.py    # Transaction endpoints
│   │   ├── compliance_routes.py     # Compliance checking endpoints
│   │   ├── dashboard_routes.py      # Dashboard endpoints
│   │   ├── superadmin_routes.py     # SuperAdmin endpoints
│   │   └── export_routes.py         # Data export endpoints
│   │
│   ├── schemas/                     # Pydantic Schemas (Request/Response models)
│   │   └── (schema files for validation)
│   │
│   ├── services/                    # Business Logic Layer
│   │   └── (service modules)
│   │
│   └── db/                          # Database Migrations & Setup
│       ├── core_schema.sql          # Core database schema
│       ├── create_tables_postgres.sql
│       ├── migrate_*.py             # Migration scripts
│       ├── populate_*.sql           # Sample data scripts
│       └── init-db.sql              # Docker initialization
│
├── docs/                            # Documentation
│   ├── FRONTEND_API_REFERENCE.md    # Complete API documentation
│   ├── SUPERADMIN_API_DOCS.md       # SuperAdmin specific docs
│   ├── UPLOAD_FORM_API.md           # Form upload specifications
│   ├── FRONTEND_SCHEMA_MIGRATION.md # Schema migration guide
│   └── SUPERADMIN_MONITORING.md     # Monitoring guide
│
├── tests/                           # Test Suite
│   ├── __init__.py
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   ├── e2e/                         # End-to-end tests
│   ├── load/                        # Load/performance tests
│   └── README.md                    # Testing guide
│
├── scripts/                         # Utility Scripts
│   ├── populate_all_tables.py       # Populate database
│   ├── seed_database.py             # Seed sample data
│   └── show_all_data.py             # Display all data
│
├── legacy/                          # Legacy Code (deprecated)
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   └── services/
│
├── requirements.txt                 # Python dependencies
├── setup_load_test_db.sh            # Load test setup
├── generate_password_hash.py        # Utility: Hash generation
├── verify_quick.py                  # Quick verification script
└── test_password.py                 # Password testing utility
```

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis (optional, for caching)
- pip or conda

### Installation Steps

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment configuration
touch .env

# 5. Initialize database
python scripts/seed_database.py

# 6. Start the server
python -m uvicorn app.main:app --reload
```

---

## Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/values_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=values_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT/Security Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]


# AWS Configuration (Optional)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket


```

---

## Running the Backend

### Development Server

```bash
# Basic (with auto-reload)
python -m uvicorn app.main:app --reload --port 8001

# With custom host
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# With multiple workers (production-like)
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8001
```




---

## API Endpoints

### Base URL
`http://localhost:8001`

### Documentation
- **Interactive Docs**: `http://localhost:8001/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8001/redoc` (ReDoc)

### Main Routes

#### Authentication (`/auth`)
```
POST   /auth/login              - Login user
POST   /auth/register           - Register new user
POST   /auth/logout             - Logout user
POST   /auth/refresh-token      - Refresh access token
GET    /auth/me                 - Get current user info
```

#### Users (`/users`)
```
GET    /users/                  - List all users (paginated)
GET    /users/{user_id}         - Get user by ID
POST   /users/                  - Create new user
PUT    /users/{user_id}         - Update user
DELETE /users/{user_id}         - Delete user
GET    /users/{user_id}/history - Get user activity history
```

#### Transactions (`/transactions`)
```
GET    /transactions/           - List transactions (paginated, filterable)
GET    /transactions/{id}       - Get transaction details
POST   /transactions/           - Create new transaction
PUT    /transactions/{id}       - Update transaction
DELETE /transactions/{id}       - Delete transaction
GET    /transactions/risk       - Get transaction risk analysis
```

#### Compliance (`/compliance`)
```
GET    /compliance/check        - Check compliance status
POST   /compliance/scan         - Scan entity against compliance databases
GET    /compliance/sanctions    - Check against sanctions lists
GET    /compliance/alerts       - Get compliance alerts
POST   /compliance/alerts       - Create compliance alert
PUT    /compliance/alerts/{id}  - Update alert status
```

#### Dashboard (`/dashboard`)
```
GET    /dashboard/overview      - System overview metrics
GET    /dashboard/alerts        - Recent alerts summary
GET    /dashboard/transactions  - Transaction statistics
GET    /dashboard/users         - User statistics
```

#### SuperAdmin (`/superadmin`)
```
GET    /superadmin/monitoring   - Monitoring dashboard
GET    /superadmin/metrics      - System metrics
GET    /superadmin/health       - System health status
GET    /superadmin/audit-logs   - Audit logs
POST   /superadmin/config       - Update system config
```

#### Export (`/export`)
```
POST   /export/users            - Export users data
POST   /export/transactions     - Export transactions data
POST   /export/alerts           - Export alerts data
GET    /export/status/{job_id}  - Check export job status
```

**Full API Documentation**: See `docs/FRONTEND_API_REFERENCE.md`

---

## Database

### Connection
The backend uses SQLAlchemy ORM with PostgreSQL.

```python
# Connection string format
postgresql://username:password@host:port/database_name
```

### Database Setup

```bash
# Create tables (runs automatically on app startup)
python scripts/seed_database.py

# Populate sample data
python -m app.db create_tables

# Reset database
python scripts/reset_database.py
```

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# View migration status
alembic current
```

### Database Models

All models are in `app/models/`:

- **User** - User accounts and authentication
- **Transaction** - Financial transactions
- **Alert** - Compliance and fraud alerts
- **Admin** - Admin and SuperAdmin accounts
- **AuditLog** - All system actions for compliance
- **ToxicityHistory** - Historical toxicity scores
- **UserSanctionMatch** - Sanctions matching records
- **SystemMetrics** - Performance metrics
- **SystemHealth** - System health status

---

## Models & Schemas

### Models (Database)

Models are SQLAlchemy ORM classes in `app/models/`. They define database tables and relationships.

```python
# Example structure
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transactions = relationship("Transaction", back_populates="user")
```

### Schemas (Validation)

Pydantic schemas in `app/schemas/` define request/response validation.

```python
# Example structure
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepassword"
            }
        }

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
```

---

## Authentication

The backend uses JWT (JSON Web Token) for authentication.

### Authentication Flow

1. User calls `POST /auth/login` with credentials
2. Server validates and returns `access_token` and `refresh_token`
3. Client includes token in `Authorization: Bearer <token>` header
4. Server validates token on protected routes
5. Token expires after `ACCESS_TOKEN_EXPIRE_MINUTES`
6. Client uses `refresh_token` to get new access token

### Protected Routes

```python
from fastapi import Depends, HTTPException
from app.routes.auth_routes import get_current_user

@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user)):
    return {"user": current_user}
```

### Password Security

Passwords are hashed using bcrypt:

```bash
# Generate password hash
python generate_password_hash.py

# Test password
python test_password.py
```


---

## Development Tools

### Utility Scripts

```bash
# Generate password hash
python generate_password_hash.py

# Seed database with sample data
python scripts/seed_database.py

# Show all database data
python scripts/show_all_data.py

# Verify configuration
python verify_quick.py

# Test password
python test_password.py
```

### Database Tools

```bash
# Connect to PostgreSQL
psql -U user -d values_db -h localhost

# Load test database setup
bash setup_load_test_db.sh
```

---

## Documentation

### API Documentation

- **Full Reference**: `docs/FRONTEND_API_REFERENCE.md`
- **SuperAdmin APIs**: `docs/SUPERADMIN_API_DOCS.md`
- **Upload Forms**: `docs/UPLOAD_FORM_API.md`
- **Schema Migration**: `docs/FRONTEND_SCHEMA_MIGRATION.md`
- **Monitoring**: `docs/SUPERADMIN_MONITORING.md`

### Code Documentation

All modules, classes, and functions include docstrings. View in IDE or API docs.

---

## Debugging

### Enable Debug Mode

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### View Application Logs

```bash
# View logs
tail -f app.log

# Or run with logging
python -m uvicorn app.main:app --log-level debug
```

### Database Query Logging

```python
# In .env
SQLALCHEMY_ECHO=True  # Log all SQL queries
```

### Debug with IDE

1. Set breakpoints in code
2. Run with debugger:
   ```bash
   python -m debugpy --listen 5678 -m uvicorn app.main:app --reload
   ```


---


**Version**: 2.0  
**Last Updated**: December 2025
