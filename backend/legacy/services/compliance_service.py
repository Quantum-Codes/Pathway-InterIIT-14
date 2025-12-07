from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.transaction import Transaction
from app.models.alert import ComplianceAlert
from app.models.settings import OrganizationSettings, NotificationSettings
from app.schemas.compliance import (
    OrganizationSettingsUpdate, 
    NotificationSettingsUpdate,
    ThresholdAlerts
)
from datetime import datetime, timedelta
import random


def get_compliance_status(db: Session):
    """Get overall compliance status and metrics"""
    # Total users and screening stats
    total_users = db.query(User).count()
    blacklisted_users = db.query(User).filter(User.is_blacklisted == True).count()
    high_risk_users = db.query(User).filter(User.i_360_score >= 60).count()
    
    # Alert statistics
    flagged_users = db.query(ComplianceAlert).filter(
        ComplianceAlert.severity.in_(["high", "critical"])
    ).distinct(ComplianceAlert.user_id).count()
    
    pending_reviews = db.query(ComplianceAlert).filter(
        ComplianceAlert.status == "active"
    ).count()
    
    # Calculate screening rates (mock calculation - in production, track actual screening)
    kyc_verification_rate = min(98.5, (total_users / max(total_users + 10, 1)) * 100)
    aml_screening_rate = min(97.2, (total_users / max(total_users + 15, 1)) * 100)
    
    # Last 24 hours stats
    yesterday = datetime.utcnow() - timedelta(days=1)
    last_week = datetime.utcnow() - timedelta(days=7)
    
    users_24h = db.query(User).filter(User.created_at >= yesterday).count()
    alerts_24h = db.query(ComplianceAlert).filter(ComplianceAlert.created_at >= yesterday).count()
    transactions_24h = db.query(Transaction).filter(Transaction.created_at >= yesterday).count()
    
    users_7d = db.query(User).filter(User.created_at >= last_week).count()
    alerts_7d = db.query(ComplianceAlert).filter(ComplianceAlert.created_at >= last_week).count()
    transactions_7d = db.query(Transaction).filter(Transaction.created_at >= last_week).count()
    
    return {
        "kyc_verification_rate": round(kyc_verification_rate, 1),
        "aml_screening_rate": round(aml_screening_rate, 1),
        "sanctions_check_status": "ACTIVE",
        "total_users_screened": total_users,
        "flagged_users": flagged_users,
        "pending_reviews": pending_reviews,
        "high_risk_users": high_risk_users,
        "blacklisted_users": blacklisted_users,
        "last_updated": datetime.utcnow(),
        "screening_stats": {
            "last_24h": {
                "users_screened": users_24h,
                "alerts_generated": alerts_24h,
                "transactions_reviewed": transactions_24h
            },
            "last_7d": {
                "users_screened": users_7d,
                "alerts_generated": alerts_7d,
                "transactions_reviewed": transactions_7d
            }
        }
    }


def get_organization_settings(db: Session):
    """Get organization settings"""
    settings = db.query(OrganizationSettings).first()
    if not settings:
        # Create default settings
        settings = OrganizationSettings(
            organization_name="Argus Financial",
            email="admin@argus.com",
            phone="+91-22-12345678",
            address="Mumbai, India",
            timezone="Asia/Kolkata",
            language="en"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_organization_settings(db: Session, updates: OrganizationSettingsUpdate):
    """Update organization settings"""
    settings = get_organization_settings(db)
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings


def get_notification_settings(db: Session):
    """Get notification settings"""
    settings = db.query(NotificationSettings).first()
    if not settings:
        # Create default settings
        settings = NotificationSettings(
            email_notifications=True,
            transaction_alerts=True,
            risk_alerts=True,
            compliance_alerts=False,
            weekly_reports=True,
            threshold_alerts_enabled=True,
            suspicious_score_threshold=70.0,
            transaction_amount_threshold=100000.0
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Format response with threshold_alerts object
    return {
        "email_notifications": settings.email_notifications,
        "transaction_alerts": settings.transaction_alerts,
        "risk_alerts": settings.risk_alerts,
        "compliance_alerts": settings.compliance_alerts,
        "weekly_reports": settings.weekly_reports,
        "threshold_alerts": {
            "enabled": settings.threshold_alerts_enabled,
            "suspicious_score_threshold": settings.suspicious_score_threshold,
            "transaction_amount_threshold": settings.transaction_amount_threshold
        }
    }


def update_notification_settings(db: Session, updates: NotificationSettingsUpdate):
    """Update notification settings"""
    settings = db.query(NotificationSettings).first()
    if not settings:
        settings = NotificationSettings()
        db.add(settings)
    
    update_data = updates.model_dump(exclude_unset=True)
    
    # Handle threshold_alerts separately
    if "threshold_alerts" in update_data:
        threshold_data = update_data.pop("threshold_alerts")
        if threshold_data:
            if "enabled" in threshold_data:
                settings.threshold_alerts_enabled = threshold_data["enabled"]
            if "suspicious_score_threshold" in threshold_data:
                settings.suspicious_score_threshold = threshold_data["suspicious_score_threshold"]
            if "transaction_amount_threshold" in threshold_data:
                settings.transaction_amount_threshold = threshold_data["transaction_amount_threshold"]
    
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings


def recalculate_user_risk(db: Session, user_id: int):
    """Recalculate user risk scores based on transaction history and alerts"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Store previous values
    previous_i_not = user.i_not_score
    previous_i_360 = user.i_360_score
    
    # Get user's transactions
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    
    # Calculate new scores based on suspicious transactions
    if transactions:
        avg_suspicious = sum(t.suspicious_score for t in transactions) / len(transactions)
        high_risk_count = len([t for t in transactions if t.suspicious_score > 70])
        
        # Adjust i_not_score slightly based on transaction patterns
        new_i_not = min(100, previous_i_not + (high_risk_count * 2))
        
        # Calculate new i_360_score
        new_i_360 = min(100, (previous_i_not * 0.3) + (avg_suspicious * 0.5) + (high_risk_count * 3))
    else:
        new_i_not = previous_i_not
        new_i_360 = previous_i_not * 0.5  # If no transactions, base on initial score
    
    # Update user scores
    user.i_not_score = round(new_i_not, 2)
    user.i_360_score = round(new_i_360, 2)
    
    # Determine risk categories
    def get_category(score):
        if score < 30:
            return "LOW"
        elif score < 60:
            return "MEDIUM"
        elif score < 80:
            return "HIGH"
        else:
            return "CRITICAL"
    
    prev_category = get_category(previous_i_360)
    new_category = get_category(new_i_360)
    
    db.commit()
    db.refresh(user)
    
    return {
        "user_id": user_id,
        "previous_i_not_score": round(previous_i_not, 2),
        "new_i_not_score": round(new_i_not, 2),
        "previous_i_360_score": round(previous_i_360, 2),
        "new_i_360_score": round(new_i_360, 2),
        "risk_category_changed": prev_category != new_category,
        "previous_category": prev_category,
        "new_category": new_category,
        "recalculated_at": datetime.utcnow()
    }
