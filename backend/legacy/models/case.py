from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(String(50), primary_key=True, index=True)  # e.g., "CASE-2025-00123"
    title = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="OPEN")  # OPEN, IN_PROGRESS, CLOSED
    assigned_to = Column(String(100))
    
    # Related entities (stored as JSON arrays)
    transaction_ids = Column(JSON, default=list)
    alert_ids = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="investigation_cases")


class AccountHold(Base):
    __tablename__ = "account_holds"

    id = Column(String(50), primary_key=True, index=True)  # e.g., "HOLD-2025-00456"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    hold_type = Column(String(20), default="TRANSACTION_ONLY")  # FULL, TRANSACTION_ONLY
    status = Column(String(20), default="ACTIVE")  # ACTIVE, EXPIRED, RELEASED
    notes = Column(Text)
    
    hold_placed_at = Column(DateTime(timezone=True), server_default=func.now())
    hold_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    placed_by = Column(String(100))
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(String(100))
    
    # Relationships
    user = relationship("User", backref="account_holds")
