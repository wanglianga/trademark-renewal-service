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
