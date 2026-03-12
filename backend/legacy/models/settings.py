from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, DateTime
from datetime import datetime
from app.db import Base


class OrganizationSettings(Base):
    __tablename__ = "organization_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_name = Column(String, default="Argus Financial")
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    timezone = Column(String, default="Asia/Kolkata")
    language = Column(String, default="en")
    logo_url = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    email_notifications = Column(Boolean, default=True)
    transaction_alerts = Column(Boolean, default=True)
    risk_alerts = Column(Boolean, default=True)
    compliance_alerts = Column(Boolean, default=False)
    weekly_reports = Column(Boolean, default=True)
    
    # Threshold alerts
    threshold_alerts_enabled = Column(Boolean, default=True)
    suspicious_score_threshold = Column(Float, default=70.0)
    transaction_amount_threshold = Column(Float, default=100000.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
