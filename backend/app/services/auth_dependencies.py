from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.admin import Admin
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Admin:
    """Dependency to get the current authenticated admin."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = AuthService.verify_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception
    
    admin = db.query(Admin).filter(
        Admin.username == token_data.username
    ).first()
    
    if admin is None:
        raise credentials_exception
    
    return admin


async def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """Dependency to get the current active admin."""
    return current_admin


async def require_admin(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """Dependency to require admin role (both admin and superadmin allowed)."""
    if current_admin.role not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_admin


async def require_superadmin(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """Dependency to require superadmin role."""
    if current_admin.role != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required"
        )
    return current_admin


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "unknown")
