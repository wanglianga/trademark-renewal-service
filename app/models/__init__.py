from app.models.base import Base
from app.models.customer import Customer
from app.models.trademark import Trademark
from app.models.user import User
from app.models.agency_entrustment import AgencyEntrustment
from app.models.fee import Fee
from app.models.material_version import MaterialVersion
from app.models.submission_record import SubmissionRecord
from app.models.acceptance_receipt import AcceptanceReceipt
from app.models.correction import Correction
from app.models.rejection import Rejection
from app.models.certificate_archive import CertificateArchive
from app.models.reminder import Reminder

__all__ = [
    "Base",
    "Customer",
    "Trademark",
    "User",
    "AgencyEntrustment",
    "Fee",
    "MaterialVersion",
    "SubmissionRecord",
    "AcceptanceReceipt",
    "Correction",
    "Rejection",
    "CertificateArchive",
    "Reminder",
]
