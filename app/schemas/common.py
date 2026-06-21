from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar, Dict, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkOperationRequest(BaseModel):
    ids: List[int]
    action: str
    params: Optional[Dict[str, Any]] = None


class BulkOperationResponse(BaseModel):
    success: bool
    processed_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)


class StageInfo(BaseModel):
    stage_code: str
    stage_name: str
    is_current: bool
    is_completed: bool
    entered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_days: Optional[int] = None
    notes: Optional[str] = None


class ProgressBoardResponse(BaseModel):
    trademark_id: int
    registration_number: str
    trademark_name: str
    customer_name: str
    current_status: str
    current_stage: str
    expiry_date: Optional[date] = None
    days_until_expiry: Optional[int] = None
    is_expiring_soon: bool = False
    is_in_grace_period: bool = False
    is_overdue: bool = False
    stages: List[StageInfo]
    blocked_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    last_updated: Optional[datetime] = None


class ValidationIssue(BaseModel):
    field: str
    issue_type: str
    severity: str
    message: str
    suggestion: Optional[str] = None


class TrademarkValidationResponse(BaseModel):
    trademark_id: int
    is_valid: bool
    issues: List[ValidationIssue]
    can_proceed: bool
    blocked_reasons: List[str] = Field(default_factory=list)


class UrgencyLevel(str):
    NORMAL = "normal"
    ATTENTION = "attention"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERDUE = "overdue"


class RenewalStage(str):
    PRE_RENEWAL = "pre_renewal"
    RENEWAL_PERIOD = "renewal_period"
    GRACE_PERIOD = "grace_period"
    MISSED_WINDOW = "missed_window"


class RiskMaterialItem(BaseModel):
    material_type: str
    material_name: str
    required: bool
    has_current: bool
    current_version: Optional[int] = None
    notes: Optional[str] = None


class RiskQueueItem(BaseModel):
    trademark_id: int
    registration_number: str
    trademark_name: str
    international_class: int
    customer_id: int
    customer_name: str
    assigned_agent_id: Optional[int] = None
    assigned_agent_name: Optional[str] = None
    expiry_date: date
    grace_period_end: Optional[date] = None
    renewal_stage: str
    urgency_level: str
    urgency_score: int
    days_until_expiry: int
    days_until_grace_end: Optional[int] = None
    days_until_deadline: int
    latest_submit_date: date
    late_fee_amount: float
    late_fee_currency: str
    required_materials: List[RiskMaterialItem]
    missing_materials: List[str]
    risk_factors: List[str]
    reminder_count: int
    last_reminder_date: Optional[date] = None


class AgentRiskSummary(BaseModel):
    agent_id: int
    agent_name: str
    total_trademarks: int
    critical_count: int
    warning_count: int
    attention_count: int
    normal_count: int
    overdue_count: int
    total_risk_score: int
    average_risk_score: float


class RiskQueueResponse(BaseModel):
    items: List[RiskQueueItem]
    total: int
    summary: Dict[str, Any]
    agent_rankings: List[AgentRiskSummary]


class CustomerReminderItem(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    trademarks: List[RiskQueueItem]
    total_risk_count: int
    critical_count: int
    summary_message: str
