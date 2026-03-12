from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.alert import (
    ComplianceAlertRead,
    ComplianceAlertUpdate,
    ComplianceAlertListResponse,
    UploadFormResponse
)
from app.schemas.compliance import (
    ComplianceStatusResponse,
    OrganizationSettingsRead,
    OrganizationSettingsUpdate,
    NotificationSettingsUpdate,
    SettingsUpdateResponse,
    RiskRecalculationResponse
)
from app.services import alert_service, compliance_service, pdf_service
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/compliance", tags=["compliance"])
settings_router = APIRouter(prefix="/settings", tags=["settings"])
user_upload_router = APIRouter(prefix="/user", tags=["user"])


# Compliance Alerts Endpoints
@router.get("/alerts", response_model=ComplianceAlertListResponse)
def get_compliance_alerts(
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get compliance alerts with optional filters
    
    - **limit**: Maximum number of alerts to return (1-100)
    - **severity**: Filter by severity (LOW/MEDIUM/HIGH/CRITICAL) or 'all'
    - **status**: Filter by status (PENDING/IN_PROGRESS/RESOLVED/DISMISSED) or 'all'
    - **skip**: Pagination offset
    """
    result = alert_service.get_alerts(db, skip, limit, severity, status)
    return result


@router.patch("/alerts/{alert_id}")
def update_alert(
    alert_id: int,
    alert_update: ComplianceAlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Update alert status, assignee, or notes
    
    - **alert_id**: ID of the alert to update
    - **status**: New status (PENDING/IN_PROGRESS/RESOLVED/DISMISSED)
    - **assigned_to**: Email of person assigned
    - **notes**: Additional notes
    """
    updated_alert = alert_service.update_alert(db, alert_id, alert_update)
    if not updated_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "alert_id": updated_alert.id,
        "status": updated_alert.status,
        "assigned_to": updated_alert.assigned_to,
        "updated_at": updated_alert.updated_at
    }


@router.get("/status", response_model=ComplianceStatusResponse)
def get_compliance_status(db: Session = Depends(get_db)):
    """
    Get overall compliance metrics and screening rates
    
    Returns:
    - KYC verification rate
    - AML screening rate
    - Sanctions check status
    - User statistics
    - Screening statistics for last 24h and 7d
    """
    return compliance_service.get_compliance_status(db)


# Settings Endpoints
@settings_router.get("/organization", response_model=OrganizationSettingsRead)
def get_organization_settings(db: Session = Depends(get_db)):
    """Get organization settings"""
    return compliance_service.get_organization_settings(db)


@settings_router.put("/organization", response_model=SettingsUpdateResponse)
def update_organization_settings(
    settings: OrganizationSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update organization settings"""
    updated = compliance_service.update_organization_settings(db, settings)
    return {
        "success": True,
        "message": "Settings updated successfully",
        "updated_at": updated.updated_at
    }


@settings_router.get("/notifications")
def get_notification_settings(db: Session = Depends(get_db)):
    """Get notification preferences"""
    return compliance_service.get_notification_settings(db)


@settings_router.put("/notifications", response_model=SettingsUpdateResponse)
def update_notification_settings(
    settings: NotificationSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update notification preferences"""
    updated = compliance_service.update_notification_settings(db, settings)
    return {
        "success": True,
        "message": "Notification settings updated successfully",
        "updated_at": updated.updated_at
    }


# PDF Upload Endpoint (added to user routes)
@user_upload_router.post("/upload-form", response_model=UploadFormResponse)
async def upload_kyc_form(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload PDF KYC form with automatic data extraction
    
    - **file**: PDF file containing KYC form
    
    Returns:
    - success: Boolean indicating success
    - user_id: ID of created user
    - extracted_data: Parsed KYC data
    - message: Success message
    
    Errors:
    - 400: Invalid file format or OCR extraction failed
    - 422: Validation errors on extracted data
    """
    try:
        result = await pdf_service.process_kyc_pdf(db, file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
