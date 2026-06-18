from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.trademark import Trademark, TrademarkStatus
from app.models.customer import Customer
from app.models.user import User
from app.models.material_version import MaterialVersion
from app.models.fee import Fee, FeeStatus
from app.models.submission_record import SubmissionRecord
from app.models.acceptance_receipt import AcceptanceReceipt
from app.models.correction import Correction
from app.models.certificate_archive import CertificateArchive
from app.models.agency_entrustment import AgencyEntrustment
from app.schemas.common import ProgressBoardResponse, StageInfo


STAGES = [
    {"code": "materials_preparation", "name": "材料准备"},
    {"code": "agent_review", "name": "代理人审核"},
    {"code": "fee_confirmation", "name": "费用确认"},
    {"code": "submission", "name": "提交申请"},
    {"code": "official_acceptance", "name": "官方受理"},
    {"code": "correction", "name": "补正处理"},
    {"code": "approval", "name": "审核通过"},
    {"code": "certificate_archive", "name": "证书归档"}
]

STAGE_STATUS_NOT_STARTED = "not_started"
STAGE_STATUS_IN_PROGRESS = "in_progress"
STAGE_STATUS_COMPLETED = "completed"
STAGE_STATUS_BLOCKED = "blocked"


def _get_stage_datetime(
    stage_code: str,
    trademark: Trademark,
    related_records: Dict[str, Any]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    entered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    if stage_code == "materials_preparation":
        materials = related_records.get("materials", [])
        if materials:
            entered_at = materials[0].created_at
            approved_materials = [m for m in materials if m.is_approved]
            if approved_materials:
                completed_at = approved_materials[-1].updated_at

    elif stage_code == "agent_review":
        entrustment = related_records.get("entrustment")
        if entrustment:
            entered_at = entrustment.created_at
            if entrustment.is_active:
                completed_at = entrustment.updated_at

    elif stage_code == "fee_confirmation":
        fees = related_records.get("fees", [])
        if fees:
            entered_at = fees[0].created_at
            confirmed_fees = [f for f in fees if f.is_confirmed]
            if confirmed_fees:
                completed_at = confirmed_fees[-1].confirmed_at if confirmed_fees[-1].confirmed_at else confirmed_fees[-1].updated_at

    elif stage_code == "submission":
        submissions = related_records.get("submissions", [])
        if submissions:
            entered_at = submissions[0].created_at
            completed_at = submissions[-1].submission_date

    elif stage_code == "official_acceptance":
        acceptance = related_records.get("acceptance")
        if acceptance:
            entered_at = acceptance.created_at
            completed_at = acceptance.acceptance_date

    elif stage_code == "correction":
        corrections = related_records.get("corrections", [])
        if corrections:
            entered_at = corrections[0].created_at
            completed_corrections = [c for c in corrections if c.correction_status == "completed"]
            if completed_corrections:
                completed_at = completed_corrections[-1].correction_complete_date

    elif stage_code == "approval":
        if trademark.status in [TrademarkStatus.APPROVED, TrademarkStatus.CERTIFIED, TrademarkStatus.ARCHIVED]:
            entered_at = trademark.updated_at
            completed_at = trademark.updated_at

    elif stage_code == "certificate_archive":
        certificate = related_records.get("certificate")
        if certificate:
            entered_at = certificate.created_at
            completed_at = certificate.archive_date

    return entered_at, completed_at


def _get_stage_status(
    stage_code: str,
    trademark: Trademark,
    entered_at: Optional[datetime],
    completed_at: Optional[datetime],
    related_records: Dict[str, Any]
) -> Tuple[str, Optional[str]]:
    if completed_at:
        return STAGE_STATUS_COMPLETED, None

    if not entered_at:
        return STAGE_STATUS_NOT_STARTED, None

    blocked_reason: Optional[str] = None

    if stage_code == "materials_preparation":
        materials = related_records.get("materials", [])
        if not materials:
            return STAGE_STATUS_NOT_STARTED, None
        unapproved = [m for m in materials if not m.is_approved]
        if unapproved:
            blocked_reason = f"{len(unapproved)} 份材料待审核"
            return STAGE_STATUS_BLOCKED, blocked_reason
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "agent_review":
        entrustment = related_records.get("entrustment")
        if not entrustment:
            return STAGE_STATUS_NOT_STARTED, None
        if not entrustment.is_active:
            blocked_reason = "代理委托书待签署或已失效"
            return STAGE_STATUS_BLOCKED, blocked_reason
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "fee_confirmation":
        fees = related_records.get("fees", [])
        if not fees:
            return STAGE_STATUS_NOT_STARTED, None
        unpaid = [f for f in fees if f.status != FeeStatus.PAID]
        if unpaid:
            blocked_reason = f"{len(unpaid)} 项费用待支付"
            return STAGE_STATUS_BLOCKED, blocked_reason
        unconfirmed = [f for f in fees if not f.is_confirmed]
        if unconfirmed:
            blocked_reason = f"{len(unconfirmed)} 项费用待确认"
            return STAGE_STATUS_BLOCKED, blocked_reason
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "submission":
        submissions = related_records.get("submissions", [])
        if not submissions:
            return STAGE_STATUS_NOT_STARTED, None
        duplicates = [s for s in submissions if s.is_duplicate == 1]
        if duplicates:
            blocked_reason = f"存在 {len(duplicates)} 条重复提交记录"
            return STAGE_STATUS_BLOCKED, blocked_reason
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "official_acceptance":
        acceptance = related_records.get("acceptance")
        if not acceptance:
            return STAGE_STATUS_NOT_STARTED, None
        if acceptance.has_correction_deadline == 1 and acceptance.is_correction_overdue == 1:
            blocked_reason = "补正期限已超期"
            return STAGE_STATUS_BLOCKED, blocked_reason
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "correction":
        corrections = related_records.get("corrections", [])
        if not corrections:
            return STAGE_STATUS_NOT_STARTED, None
        overdue = [c for c in corrections if c.is_overdue]
        if overdue:
            blocked_reason = f"{len(overdue)} 项补正已超期"
            return STAGE_STATUS_BLOCKED, blocked_reason
        pending = [c for c in corrections if c.correction_status == "pending"]
        if pending:
            return STAGE_STATUS_IN_PROGRESS, None
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "approval":
        if trademark.status == TrademarkStatus.REJECTED:
            blocked_reason = "商标申请被驳回"
            return STAGE_STATUS_BLOCKED, blocked_reason
        if trademark.status in [TrademarkStatus.CORRECTION_REQUIRED, TrademarkStatus.CORRECTION_SUBMITTED]:
            return STAGE_STATUS_NOT_STARTED, None
        return STAGE_STATUS_IN_PROGRESS, None

    elif stage_code == "certificate_archive":
        certificate = related_records.get("certificate")
        if not certificate:
            return STAGE_STATUS_NOT_STARTED, None
        if not certificate.archive_date:
            blocked_reason = "证书待归档"
            return STAGE_STATUS_BLOCKED, blocked_reason
        return STAGE_STATUS_IN_PROGRESS, None

    return STAGE_STATUS_IN_PROGRESS, None


def _calculate_duration(
    entered_at: Optional[datetime],
    completed_at: Optional[datetime],
    status: str
) -> Optional[int]:
    if not entered_at:
        return None

    end_date = completed_at or datetime.now()

    if isinstance(entered_at, date) and not isinstance(entered_at, datetime):
        entered_at = datetime.combine(entered_at, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())

    if status == STAGE_STATUS_COMPLETED and completed_at:
        duration = (end_date - entered_at).days
        return max(0, duration)
    elif status in [STAGE_STATUS_IN_PROGRESS, STAGE_STATUS_BLOCKED]:
        duration = (datetime.now() - entered_at).days
        return max(0, duration)

    return None


def _get_trademark_progress(
    db: Session,
    trademark: Trademark
) -> ProgressBoardResponse:
    materials = db.query(MaterialVersion).filter(
        MaterialVersion.trademark_id == trademark.id,
        MaterialVersion.is_deleted == False
    ).order_by(MaterialVersion.created_at.asc()).all()

    fees = db.query(Fee).filter(
        Fee.trademark_id == trademark.id,
        Fee.is_deleted == False
    ).order_by(Fee.created_at.asc()).all()

    submissions = db.query(SubmissionRecord).filter(
        SubmissionRecord.trademark_id == trademark.id,
        SubmissionRecord.is_deleted == False
    ).order_by(SubmissionRecord.submission_date.asc()).all()

    corrections = db.query(Correction).filter(
        Correction.trademark_id == trademark.id,
        Correction.is_deleted == False
    ).order_by(Correction.created_at.asc()).all()

    entrustment = db.query(AgencyEntrustment).filter(
        AgencyEntrustment.trademark_id == trademark.id,
        AgencyEntrustment.is_deleted == False
    ).first()

    acceptance = db.query(AcceptanceReceipt).filter(
        AcceptanceReceipt.trademark_id == trademark.id,
        AcceptanceReceipt.is_deleted == False
    ).first()

    certificate = db.query(CertificateArchive).filter(
        CertificateArchive.trademark_id == trademark.id,
        CertificateArchive.is_deleted == False
    ).first()

    customer = db.query(Customer).filter(
        Customer.id == trademark.customer_id,
        Customer.is_deleted == False
    ).first()

    agent = None
    if trademark.assigned_agent_id:
        agent = db.query(User).filter(
            User.id == trademark.assigned_agent_id,
            User.is_deleted == False
        ).first()

    related_records = {
        "materials": materials,
        "fees": fees,
        "submissions": submissions,
        "corrections": corrections,
        "entrustment": entrustment,
        "acceptance": acceptance,
        "certificate": certificate
    }

    stages: List[StageInfo] = []
    current_stage_code: Optional[str] = None
    blocked_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None

    for stage in STAGES:
        stage_code = stage["code"]
        stage_name = stage["name"]

        entered_at, completed_at = _get_stage_datetime(stage_code, trademark, related_records)
        status, stage_blocked_reason = _get_stage_status(
            stage_code, trademark, entered_at, completed_at, related_records
        )
        duration = _calculate_duration(entered_at, completed_at, status)

        is_current = False
        if status in [STAGE_STATUS_IN_PROGRESS, STAGE_STATUS_BLOCKED] and current_stage_code is None:
            current_stage_code = stage_code
            is_current = True

        if status == STAGE_STATUS_BLOCKED and stage_blocked_reason and blocked_reason is None:
            blocked_reason = stage_blocked_reason
            blocked_at = entered_at

        stage_notes: Optional[str] = None
        if stage_blocked_reason:
            stage_notes = stage_blocked_reason

        stages.append(StageInfo(
            stage_code=stage_code,
            stage_name=stage_name,
            is_current=is_current,
            is_completed=status == STAGE_STATUS_COMPLETED,
            entered_at=entered_at,
            completed_at=completed_at,
            duration_days=duration,
            notes=stage_notes
        ))

    days_until_expiry: Optional[int] = None
    if trademark.expiry_date:
        days_until_expiry = (trademark.expiry_date - date.today()).days

    current_stage_name = "未开始"
    if current_stage_code:
        for s in STAGES:
            if s["code"] == current_stage_code:
                current_stage_name = s["name"]
                break

    return ProgressBoardResponse(
        trademark_id=trademark.id,
        registration_number=trademark.registration_number,
        trademark_name=trademark.trademark_name,
        customer_name=customer.name if customer else "未知客户",
        current_status=trademark.status.value if hasattr(trademark.status, 'value') else str(trademark.status),
        current_stage=current_stage_name,
        expiry_date=trademark.expiry_date,
        days_until_expiry=days_until_expiry,
        is_expiring_soon=trademark.is_expiring_soon,
        is_in_grace_period=trademark.is_in_grace_period,
        is_overdue=trademark.is_overdue,
        stages=stages,
        blocked_reason=blocked_reason,
        blocked_at=blocked_at,
        assigned_agent=agent.username if agent else None,
        last_updated=trademark.updated_at
    )


def get_progress_board(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    assigned_agent_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    current_stage: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    keyword: Optional[str] = None
) -> Tuple[List[ProgressBoardResponse], int]:
    query = db.query(Trademark).filter(Trademark.is_deleted == False)

    if assigned_agent_id is not None:
        query = query.filter(Trademark.assigned_agent_id == assigned_agent_id)
    if customer_id is not None:
        query = query.filter(Trademark.customer_id == customer_id)
    if status:
        try:
            status_enum = TrademarkStatus(status)
            query = query.filter(Trademark.status == status_enum)
        except ValueError:
            pass
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.join(Customer, Trademark.customer_id == Customer.id).filter(
            (Trademark.trademark_name.ilike(search_pattern)) |
            (Trademark.registration_number.ilike(search_pattern)) |
            (Customer.name.ilike(search_pattern))
        )

    total = query.count()
    trademarks = query.order_by(
        Trademark.updated_at.desc(),
        Trademark.expiry_date.asc()
    ).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    progress_list: List[ProgressBoardResponse] = []
    for trademark in trademarks:
        try:
            progress = _get_trademark_progress(db, trademark)

            if current_stage and progress.current_stage != current_stage:
                continue

            if is_blocked is not None:
                has_blocked = any(s.notes and s.is_current for s in progress.stages)
                if is_blocked != has_blocked:
                    continue

            progress_list.append(progress)
        except Exception as e:
            continue

    return progress_list, total


def get_trademark_progress(
    db: Session,
    trademark_id: int
) -> ProgressBoardResponse:
    trademark = db.query(Trademark).filter(
        Trademark.id == trademark_id,
        Trademark.is_deleted == False
    ).first()

    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {trademark_id} 不存在"
        )

    return _get_trademark_progress(db, trademark)


def get_progress_statistics(
    db: Session,
    assigned_agent_id: Optional[int] = None,
    customer_id: Optional[int] = None
) -> Dict[str, Any]:
    query = db.query(Trademark).filter(Trademark.is_deleted == False)

    if assigned_agent_id is not None:
        query = query.filter(Trademark.assigned_agent_id == assigned_agent_id)
    if customer_id is not None:
        query = query.filter(Trademark.customer_id == customer_id)

    trademarks = query.all()

    stats = {
        "total": len(trademarks),
        "by_stage": {stage["name"]: 0 for stage in STAGES},
        "by_status": {},
        "blocked_count": 0,
        "expiring_soon_count": 0,
        "in_grace_period_count": 0,
        "overdue_count": 0,
        "avg_duration_per_stage": {},
        "stuck_trademarks": []
    }

    stage_durations: Dict[str, List[int]] = {stage["code"]: [] for stage in STAGES}

    for trademark in trademarks:
        try:
            progress = _get_trademark_progress(db, trademark)

            stats["by_stage"][progress.current_stage] = stats["by_stage"].get(progress.current_stage, 0) + 1

            status_str = progress.current_status
            stats["by_status"][status_str] = stats["by_status"].get(status_str, 0) + 1

            if progress.blocked_reason:
                stats["blocked_count"] += 1
                stats["stuck_trademarks"].append({
                    "trademark_id": trademark.id,
                    "trademark_name": trademark.trademark_name,
                    "registration_number": trademark.registration_number,
                    "current_stage": progress.current_stage,
                    "blocked_reason": progress.blocked_reason,
                    "blocked_days": progress.stages[0].duration_days
                })

            if progress.is_expiring_soon:
                stats["expiring_soon_count"] += 1
            if progress.is_in_grace_period:
                stats["in_grace_period_count"] += 1
            if progress.is_overdue:
                stats["overdue_count"] += 1

            for stage in progress.stages:
                if stage.duration_days is not None:
                    stage_durations[stage.stage_code].append(stage.duration_days)

        except Exception:
            continue

    for stage_code, durations in stage_durations.items():
        if durations:
            stage_name = next((s["name"] for s in STAGES if s["code"] == stage_code), stage_code)
            stats["avg_duration_per_stage"][stage_name] = round(sum(durations) / len(durations), 1)

    stats["stuck_trademarks"] = sorted(
        stats["stuck_trademarks"],
        key=lambda x: x.get("blocked_days", 0),
        reverse=True
    )[:10]

    return stats
