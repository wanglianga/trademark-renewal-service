from app.schemas.customer import CustomerBase, CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.trademark import TrademarkBase, TrademarkCreate, TrademarkUpdate, TrademarkResponse, TrademarkStatusUpdate
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, Token, TokenData, LoginRequest
from app.schemas.fee import FeeBase, FeeCreate, FeeUpdate, FeeResponse
from app.schemas.material import MaterialBase, MaterialCreate, MaterialUpdate, MaterialResponse, MaterialUploadResponse
from app.schemas.submission import SubmissionBase, SubmissionCreate, SubmissionUpdate, SubmissionResponse
from app.schemas.acceptance import AcceptanceBase, AcceptanceCreate, AcceptanceUpdate, AcceptanceResponse
from app.schemas.correction import CorrectionBase, CorrectionCreate, CorrectionUpdate, CorrectionResponse
from app.schemas.rejection import RejectionBase, RejectionCreate, RejectionUpdate, RejectionResponse
from app.schemas.certificate import CertificateBase, CertificateCreate, CertificateUpdate, CertificateResponse
from app.schemas.reminder import ReminderBase, ReminderCreate, ReminderUpdate, ReminderResponse
from app.schemas.agency import AgencyBase, AgencyCreate, AgencyUpdate, AgencyResponse
from app.schemas.common import (
    PaginatedResponse,
    BulkOperationRequest,
    BulkOperationResponse,
    StageInfo,
    ProgressBoardResponse,
    ValidationIssue,
    TrademarkValidationResponse,
)

__all__ = [
    "CustomerBase", "CustomerCreate", "CustomerUpdate", "CustomerResponse",
    "TrademarkBase", "TrademarkCreate", "TrademarkUpdate", "TrademarkResponse", "TrademarkStatusUpdate",
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "Token", "TokenData", "LoginRequest",
    "FeeBase", "FeeCreate", "FeeUpdate", "FeeResponse",
    "MaterialBase", "MaterialCreate", "MaterialUpdate", "MaterialResponse", "MaterialUploadResponse",
    "SubmissionBase", "SubmissionCreate", "SubmissionUpdate", "SubmissionResponse",
    "AcceptanceBase", "AcceptanceCreate", "AcceptanceUpdate", "AcceptanceResponse",
    "CorrectionBase", "CorrectionCreate", "CorrectionUpdate", "CorrectionResponse",
    "RejectionBase", "RejectionCreate", "RejectionUpdate", "RejectionResponse",
    "CertificateBase", "CertificateCreate", "CertificateUpdate", "CertificateResponse",
    "ReminderBase", "ReminderCreate", "ReminderUpdate", "ReminderResponse",
    "AgencyBase", "AgencyCreate", "AgencyUpdate", "AgencyResponse",
    "PaginatedResponse",
    "BulkOperationRequest", "BulkOperationResponse",
    "StageInfo", "ProgressBoardResponse",
    "ValidationIssue", "TrademarkValidationResponse",
]
