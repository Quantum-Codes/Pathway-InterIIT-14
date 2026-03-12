from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScreeningStats(BaseModel):
    users_screened: int
    alerts_generated: int
    transactions_reviewed: int


class ComplianceStatusResponse(BaseModel):
    kyc_verification_rate: float
    aml_screening_rate: float
    sanctions_check_status: str
    total_users_screened: int
    flagged_users: int
    pending_reviews: int
    high_risk_users: int
    blacklisted_users: int
    last_updated: datetime
    screening_stats: dict


class OrganizationSettingsBase(BaseModel):
    organization_name: str = "Argus Financial"
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    language: str = "en"
    logo_url: Optional[str] = None


class OrganizationSettingsRead(OrganizationSettingsBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationSettingsUpdate(BaseModel):
    organization_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    logo_url: Optional[str] = None


class ThresholdAlerts(BaseModel):
    enabled: bool
    suspicious_score_threshold: float
    transaction_amount_threshold: float


class NotificationSettingsBase(BaseModel):
    email_notifications: bool = True
    transaction_alerts: bool = True
    risk_alerts: bool = True
    compliance_alerts: bool = False
    weekly_reports: bool = True
    threshold_alerts: ThresholdAlerts


class NotificationSettingsRead(NotificationSettingsBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    transaction_alerts: Optional[bool] = None
    risk_alerts: Optional[bool] = None
    compliance_alerts: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    threshold_alerts: Optional[ThresholdAlerts] = None


class SettingsUpdateResponse(BaseModel):
    success: bool
    message: str
    updated_at: datetime


class RiskRecalculationResponse(BaseModel):
    user_id: int
    previous_i_not_score: float
    new_i_not_score: float
    previous_i_360_score: float
    new_i_360_score: float
    risk_category_changed: bool
    previous_category: str
    new_category: str
    recalculated_at: datetime
