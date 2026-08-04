from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# --- Notification Schemas ---

class NotificationTemplateCreate(BaseModel):
    name: str = Field(..., description="Unique template name")
    subject: str = Field(..., description="Subject pattern")
    body_template: str = Field(..., description="Body pattern with format variables")


class NotificationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template_id: int
    name: str
    subject: str
    body_template: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    status: str
    created_at: Optional[datetime]
    read_at: Optional[datetime]


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    categories: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    preference_id: int
    user_id: int
    email_enabled: bool
    in_app_enabled: bool
    categories: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# --- Audit Schemas ---

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_log_id: int
    timestamp: datetime
    user_id: Optional[int]
    user_email: Optional[str]
    ip_address: Optional[str]
    action: str
    module: str
    record_id: Optional[str]
    previous_value: Optional[str]
    new_value: Optional[str]


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_log_id: int
    timestamp: datetime
    user_id: int
    activity_type: str
    description: str
    module: Optional[str]
    record_id: Optional[str]


# --- Report Schemas ---

class ReportCreate(BaseModel):
    name: str = Field(..., description="User-defined report name")
    description: Optional[str] = Field(None, description="Optional description of the report purpose")
    report_type: str = Field(..., description="Type of report (e.g., PR, PO, VendorSpend)")
    file_type: str = Field(..., description="Export format: PDF, Excel, CSV")


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: int
    name: str
    description: Optional[str]
    report_type: str
    created_by: int
    file_path: Optional[str]
    file_type: Optional[str]
    status: str
    created_at: Optional[datetime]
    completed_at: Optional[datetime]


class ScheduledReportCreate(BaseModel):
    name: str = Field(..., description="Report name pattern")
    report_type: str = Field(..., description="Type of report (e.g. PR, PO)")
    frequency: str = Field(..., description="Daily, Weekly, Monthly")
    recipients: str = Field(..., description="Comma-separated emails")
    format: str = Field(..., description="PDF, Excel, CSV")


class ScheduledReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scheduled_report_id: int
    name: str
    report_type: str
    frequency: str
    recipients: str
    format: str
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    is_active: bool
    created_by: int
    created_at: Optional[datetime]


# --- Dashboard Schemas ---

class DashboardWidgetCreate(BaseModel):
    name: str
    widget_type: str
    role: str
    configuration: Optional[str] = None


class DashboardWidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    widget_id: int
    name: str
    widget_type: str
    role: str
    configuration: Optional[str]
    is_active: bool


class SavedFilterCreate(BaseModel):
    module: str
    name: str
    filter_query: str


class SavedFilterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filter_id: int
    user_id: int
    module: str
    name: str
    filter_query: str
    created_at: Optional[datetime]


# --- Search Schemas ---

class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    index_id: int
    entity_type: str
    entity_id: str
    title: str
    content: str
    meta_data: Optional[str] = None
    created_at: Optional[datetime] = None


# --- Attachment Schemas ---

class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attachment_id: int
    entity_type: str
    entity_id: str
    category: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_by: Optional[int]
    created_at: Optional[datetime]


class AttachmentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: int
    attachment_id: int
    version_number: int
    file_name: str
    file_path: str
    file_size: int
    uploaded_by: Optional[int]
    created_at: Optional[datetime]


# --- Job Schemas ---

class JobHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    job_id: int
    run_at: datetime
    duration_seconds: Optional[float]
    status: str
    logs: Optional[str]
    error_message: Optional[str]


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    name: str
    job_type: str
    frequency: Optional[str]
    status: str
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: Optional[datetime]


# --- System Setting Schemas ---

class SystemSettingUpdate(BaseModel):
    value: str = Field(..., description="System setting value")
    description: Optional[str] = None


class SystemSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    setting_id: int
    key: str
    value: str
    description: Optional[str]
    category: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# --- Monitoring Schemas ---

class SystemHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    health_id: int
    component: str
    status: str
    details: Optional[str]
    checked_at: datetime


class SystemMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_id: int
    metric_name: str
    metric_value: float
    timestamp: datetime
    labels: Optional[str]
