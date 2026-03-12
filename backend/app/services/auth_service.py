from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.schemas.auth import TokenData, AuditLogCreate, AdminRole
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-use-openssl-rand-hex-32")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


class AuthService:
    """Service for handling authentication, authorization, and audit logging."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def authenticate_admin(db: Session, username: str, password: str) -> Optional[Admin]:
        """Authenticate an admin by username and password."""
        admin = db.query(Admin).filter(Admin.username == username).first()
        if not admin:
            return None
        if not AuthService.verify_password(password, admin.hashed_password):
            return None
        return admin
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify a JWT token and return token data."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if username is None or role is None:
                return None
            return TokenData(username=username, role=AdminRole(role))
        except JWTError:
            return None
    
    @staticmethod
    def update_last_login(db: Session, admin_id: int):
        """Update the last login timestamp for an admin."""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if admin:
            admin.last_login_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def create_audit_log(
        db: Session,
        admin_id: int,
        action_type: str,
        action_description: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None  # Kept for backward compatibility, but not stored
    ) -> AuditLog:
        """Create an audit log entry. Note: user_agent is ignored per core_schema.sql."""
        audit_log = AuditLog(
            admin_id=admin_id,
            action_type=action_type,
            action_description=action_description,
            target_type=target_type,
            target_id=target_id,
            target_identifier=target_identifier,
            action_metadata=metadata,
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        admin_id: Optional[int] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """Retrieve audit logs with optional filters."""
        query = db.query(AuditLog).join(Admin, AuditLog.admin_id == Admin.id)
        
        if admin_id:
            query = query.filter(AuditLog.admin_id == admin_id)
        if action_type:
            query = query.filter(AuditLog.action_type == action_type)
        if target_type:
            query = query.filter(AuditLog.target_type == target_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        
        # Enrich with admin details
        enriched_logs = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_username": log.admin.username,
                "admin_email": log.admin.email,
                "action_type": log.action_type,
                "action_description": log.action_description,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "target_identifier": log.target_identifier,
                "metadata": log.action_metadata,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            enriched_logs.append(log_dict)
        
        return {
            "total": total,
            "logs": enriched_logs,
            "limit": limit,
            "offset": offset
        }
    
    @staticmethod
    def create_admin(
        db: Session,
        username: str,
        email: str,
        password: str,
        role: AdminRole = AdminRole.ADMIN
    ) -> Admin:
        """Create a new admin user."""
        hashed_password = AuthService.get_password_hash(password)
        admin = Admin(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
