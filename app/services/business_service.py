from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from fastapi import HTTPException, status
from app.models.trademark import Trademark, TrademarkStatus
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.models.fee import Fee, FeeStatus
from app.models.material_version import MaterialVersion, MaterialType
from app.models.submission_record import SubmissionRecord
from app.models.agency_entrustment import AgencyEntrustment
from app.models.reminder import Reminder, ReminderType, ReminderStatus
from app.core.config import settings
from dateutil.relativedelta import relativedelta
from app.schemas.common import (
    TrademarkValidationResponse,
    ValidationIssue,
    BulkOperationResponse,
    RiskQueueItem,
    RiskMaterialItem,
    AgentRiskSummary,
    RiskQueueResponse,
    CustomerReminderItem,
    UrgencyLevel,
    RenewalStage
)


def check_expiring_trademarks(
    db: Session,
    days_threshold: int = 180
) -> List[Trademark]:
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)

    expiring_trademarks = db.query(Trademark).filter(
        Trademark.is_deleted == False,
        Trademark.expiry_date <= threshold_date,
        Trademark.expiry_date >= today
    ).order_by(Trademark.expiry_date.asc()).all()

    return expiring_trademarks


def check_materials_coverage(
    db: Session,
    trademark_ids: List[int]
) -> Tuple[bool, Dict[int, List[str]], List[int]]:
    required_materials = [
        MaterialType.BUSINESS_LICENSE.value,
        MaterialType.POWER_OF_ATTORNEY.value,
        MaterialType.TRADEMARK_LIST.value
    ]

    coverage_status: Dict[int, List[str]] = {}
    uncovered_trademarks: List[int] = []

    for trademark_id in trademark_ids:
        trademark = db.query(Trademark).filter(
            Trademark.id == trademark_id,
            Trademark.is_deleted == False
        ).first()

        if not trademark:
            coverage_status[trademark_id] = ["商标不存在"]
            uncovered_trademarks.append(trademark_id)
            continue

        materials = db.query(MaterialVersion).filter(
            MaterialVersion.trademark_id == trademark_id,
            MaterialVersion.is_deleted == False,
            MaterialVersion.is_current == True,
            MaterialVersion.is_approved == True
        ).all()

        available_types = {m.material_type.value for m in materials}
        missing_types = [mt for mt in required_materials if mt not in available_types]

        if missing_types:
            coverage_status[trademark_id] = [f"缺少材料: {', '.join(missing_types)}"]
            uncovered_trademarks.append(trademark_id)
        else:
            coverage_status[trademark_id] = []

    all_covered = len(uncovered_trademarks) == 0
    return all_covered, coverage_status, uncovered_trademarks


def check_duplicate_submissions(
    db: Session,
    trademark_ids: List[int],
    submission_date: Optional[date] = None,
    days_window: int = 30
) -> Tuple[bool, Dict[int, List[Dict[str, Any]]]]:
    if submission_date is None:
        submission_date = date.today()

    start_date = submission_date - timedelta(days=days_window)
    end_date = submission_date + timedelta(days=days_window)

    duplicates: Dict[int, List[Dict[str, Any]]] = {}

    for trademark_id in trademark_ids:
        existing = db.query(SubmissionRecord).filter(
            SubmissionRecord.trademark_id == trademark_id,
            SubmissionRecord.submission_date >= start_date,
            SubmissionRecord.submission_date <= end_date,
            SubmissionRecord.is_deleted == False
        ).all()

        if existing:
            duplicates[trademark_id] = [
                {
                    "id": sub.id,
                    "submission_number": sub.submission_number,
                    "submission_date": sub.submission_date,
                    "submission_channel": sub.submission_channel
                }
                for sub in existing
            ]

    has_duplicates = len(duplicates) > 0
    return has_duplicates, duplicates


def check_unpaid_fees(
    db: Session,
    trademark_ids: List[int]
) -> Tuple[bool, Dict[int, List[Dict[str, Any]]]]:
    unpaid_fees: Dict[int, List[Dict[str, Any]]] = {}

    for trademark_id in trademark_ids:
        fees = db.query(Fee).filter(
            Fee.trademark_id == trademark_id,
            Fee.is_deleted == False,
            Fee.status != FeeStatus.PAID
        ).all()

        if fees:
            unpaid_fees[trademark_id] = [
                {
                    "id": fee.id,
                    "fee_type": fee.fee_type.value,
                    "amount": float(fee.amount),
                    "status": fee.status.value,
                    "payment_deadline": fee.payment_deadline
                }
                for fee in fees
            ]

    has_unpaid = len(unpaid_fees) > 0
    return has_unpaid, unpaid_fees


def check_subject_changes(
    db: Session,
    trademark_ids: List[int]
) -> Tuple[bool, Dict[int, Dict[str, Any]]]:
    subject_changes: Dict[int, Dict[str, Any]] = {}

    for trademark_id in trademark_ids:
        trademark = db.query(Trademark).filter(
            Trademark.id == trademark_id,
            Trademark.is_deleted == False
        ).first()

        if not trademark:
            continue

        if trademark.has_subject_change == 1:
            subject_changes[trademark_id] = {
                "trademark_name": trademark.trademark_name,
                "registration_number": trademark.registration_number,
                "customer_id": trademark.customer_id,
                "has_subject_change": True,
                "notes": trademark.notes
            }

    has_changes = len(subject_changes) > 0
    return has_changes, subject_changes


def validate_trademark_for_submission(
    db: Session,
    trademark_id: int,
    check_materials: bool = True,
    check_fees: bool = True,
    check_duplicates: bool = True,
    check_subject: bool = True
) -> TrademarkValidationResponse:
    trademark = db.query(Trademark).filter(
        Trademark.id == trademark_id,
        Trademark.is_deleted == False
    ).first()

    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {trademark_id} 不存在"
        )

    issues: List[ValidationIssue] = []
    blocked_reasons: List[str] = []

    if check_materials:
        materials_ok, coverage_status, _ = check_materials_coverage(db, [trademark_id])
        if not materials_ok and coverage_status.get(trademark_id):
            for issue in coverage_status[trademark_id]:
                issues.append(ValidationIssue(
                    field="materials",
                    issue_type="missing_materials",
                    severity="error",
                    message=issue,
                    suggestion="请上传并审核所需材料"
                ))
                blocked_reasons.append(issue)

    if check_fees:
        fees_ok, unpaid_fees = check_unpaid_fees(db, [trademark_id])
        if fees_ok and unpaid_fees.get(trademark_id):
            for fee in unpaid_fees[trademark_id]:
                issues.append(ValidationIssue(
                    field="fees",
                    issue_type="unpaid_fee",
                    severity="error",
                    message=f"费用未付: {fee['fee_type']} - ¥{fee['amount']}",
                    suggestion="请确认费用已支付"
                ))
                blocked_reasons.append(f"费用未付: {fee['fee_type']}")

    if check_duplicates:
        dup_ok, duplicates = check_duplicate_submissions(db, [trademark_id])
        if dup_ok and duplicates.get(trademark_id):
            for sub in duplicates[trademark_id]:
                issues.append(ValidationIssue(
                    field="submissions",
                    issue_type="duplicate_submission",
                    severity="warning",
                    message=f"存在重复提交: {sub['submission_number']} ({sub['submission_date']})",
                    suggestion="请确认是否需要重复提交"
                ))

    if check_subject:
        subject_ok, changes = check_subject_changes(db, [trademark_id])
        if subject_ok and changes.get(trademark_id):
            issues.append(ValidationIssue(
                field="customer",
                issue_type="subject_change",
                severity="warning",
                message="客户主体已变更",
                suggestion="请确认主体变更是否已完成相关手续"
            ))
            blocked_reasons.append("客户主体已变更")

    can_proceed = len(blocked_reasons) == 0
    is_valid = len([i for i in issues if i.severity == "error"]) == 0

    return TrademarkValidationResponse(
        trademark_id=trademark_id,
        is_valid=is_valid,
        issues=issues,
        can_proceed=can_proceed,
        blocked_reasons=blocked_reasons
    )


def batch_renew_trademarks(
    db: Session,
    trademark_ids: List[int],
    submission_date: Optional[date] = None,
    submission_channel: str = "online",
    submitted_by_id: Optional[int] = None,
    skip_validation: bool = False
) -> BulkOperationResponse:
    if submission_date is None:
        submission_date = date.today()

    if not trademark_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择至少一个商标"
        )

    processed_count = 0
    failed_count = 0
    errors: List[str] = []
    results: List[Dict[str, Any]] = []

    for trademark_id in trademark_ids:
        try:
            trademark = db.query(Trademark).filter(
                Trademark.id == trademark_id,
                Trademark.is_deleted == False
            ).first()

            if not trademark:
                errors.append(f"商标 ID {trademark_id} 不存在")
                failed_count += 1
                continue

            if not skip_validation:
                validation = validate_trademark_for_submission(db, trademark_id)
                if not validation.can_proceed:
                    error_msg = f"商标「{trademark.trademark_name}」验证失败: {'; '.join(validation.blocked_reasons)}"
                    errors.append(error_msg)
                    failed_count += 1
                    results.append({
                        "trademark_id": trademark_id,
                        "success": False,
                        "error": error_msg
                    })
                    continue

            submission_number = f"RN{submission_date.strftime('%Y%m%d')}{trademark_id:06d}"

            submission = SubmissionRecord(
                submission_number=submission_number,
                submission_date=submission_date,
                submission_channel=submission_channel,
                submission_type="renewal",
                applicant=trademark.customer.name if trademark.customer else None,
                trademark_id=trademark_id,
                submitted_by_id=submitted_by_id
            )

            db.add(submission)

            trademark.status = TrademarkStatus.SUBMITTED
            trademark.current_stage = "提交申请"
            trademark.notes = (trademark.notes or "") + f"\n{submission_date} 批量续展提交，提交编号: {submission_number}"

            processed_count += 1
            results.append({
                "trademark_id": trademark_id,
                "success": True,
                "submission_number": submission_number,
                "trademark_name": trademark.trademark_name,
                "registration_number": trademark.registration_number
            })

        except Exception as e:
            error_msg = f"商标 ID {trademark_id} 处理失败: {str(e)}"
            errors.append(error_msg)
            failed_count += 1
            results.append({
                "trademark_id": trademark_id,
                "success": False,
                "error": str(e)
            })

    db.commit()

    return BulkOperationResponse(
        success=failed_count == 0,
        processed_count=processed_count,
        failed_count=failed_count,
        errors=errors,
        results=results
    )


def check_expiry_and_generate_reminders(
    db: Session,
    days_threshold: int = 180,
    auto_generate: bool = True
) -> Dict[str, Any]:
    expiring_trademarks = check_expiring_trademarks(db, days_threshold)

    result = {
        "total_expiring": len(expiring_trademarks),
        "expiring_trademarks": [],
        "reminders_generated": 0,
        "reminders": []
    }

    for trademark in expiring_trademarks:
        days_until_expiry = (trademark.expiry_date - date.today()).days
        result["expiring_trademarks"].append({
            "trademark_id": trademark.id,
            "trademark_name": trademark.trademark_name,
            "registration_number": trademark.registration_number,
            "expiry_date": trademark.expiry_date,
            "days_until_expiry": days_until_expiry,
            "customer_name": trademark.customer.name if trademark.customer else None
        })

    if auto_generate and expiring_trademarks:
        from app.services.reminder_service import generate_expiry_reminders
        count, reminders = generate_expiry_reminders(db, days_threshold, only_pending=True)
        result["reminders_generated"] = count
        result["reminders"] = [
            {
                "id": r.id,
                "title": r.title,
                "trademark_id": r.trademark_id,
                "days_remaining": r.days_remaining
            }
            for r in reminders
        ]

    return result


def batch_validate_trademarks(
    db: Session,
    trademark_ids: List[int]
) -> List[TrademarkValidationResponse]:
    results: List[TrademarkValidationResponse] = []

    for trademark_id in trademark_ids:
        try:
            validation = validate_trademark_for_submission(db, trademark_id)
            results.append(validation)
        except HTTPException as e:
            results.append(TrademarkValidationResponse(
                trademark_id=trademark_id,
                is_valid=False,
                issues=[
                    ValidationIssue(
                        field="general",
                        issue_type="not_found",
                        severity="error",
                        message=e.detail,
                        suggestion=None
                    )
                ],
                can_proceed=False,
                blocked_reasons=[e.detail]
            ))

    return results


def _calculate_renewal_stage(trademark: Trademark, today: date) -> str:
    expiry_date = trademark.expiry_date
    grace_period_end = trademark.grace_period_end or (expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS))
    renewal_start = expiry_date - relativedelta(months=settings.RENEWAL_PERIOD_MONTHS)

    if today > grace_period_end:
        return RenewalStage.MISSED_WINDOW
    elif expiry_date < today <= grace_period_end:
        return RenewalStage.GRACE_PERIOD
    elif renewal_start <= today <= expiry_date:
        return RenewalStage.RENEWAL_PERIOD
    else:
        return RenewalStage.PRE_RENEWAL


def _calculate_urgency(trademark: Trademark, today: date, renewal_stage: str) -> Tuple[str, int, int, Optional[int]]:
    expiry_date = trademark.expiry_date
    grace_period_end = trademark.grace_period_end or (expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS))

    days_until_expiry = (expiry_date - today).days
    days_until_grace_end = (grace_period_end - today).days

    if renewal_stage == RenewalStage.MISSED_WINDOW:
        urgency_level = UrgencyLevel.OVERDUE
        urgency_score = 100
        days_until_deadline = days_until_grace_end
    elif renewal_stage == RenewalStage.GRACE_PERIOD:
        days_until_deadline = days_until_grace_end
        if days_until_grace_end <= 7:
            urgency_level = UrgencyLevel.CRITICAL
            urgency_score = 90
        elif days_until_grace_end <= 30:
            urgency_level = UrgencyLevel.CRITICAL
            urgency_score = 80
        else:
            urgency_level = UrgencyLevel.WARNING
            urgency_score = 65
    elif renewal_stage == RenewalStage.RENEWAL_PERIOD:
        days_until_deadline = days_until_expiry
        if days_until_expiry <= 7:
            urgency_level = UrgencyLevel.CRITICAL
            urgency_score = 85
        elif days_until_expiry <= 30:
            urgency_level = UrgencyLevel.WARNING
            urgency_score = 60
        elif days_until_expiry <= 90:
            urgency_level = UrgencyLevel.WARNING
            urgency_score = 45
        else:
            urgency_level = UrgencyLevel.ATTENTION
            urgency_score = 30
    else:
        days_until_deadline = days_until_expiry
        if days_until_expiry <= 180:
            urgency_level = UrgencyLevel.ATTENTION
            urgency_score = 15
        else:
            urgency_level = UrgencyLevel.NORMAL
            urgency_score = 5

    return urgency_level, urgency_score, days_until_deadline, days_until_grace_end if renewal_stage in [RenewalStage.GRACE_PERIOD, RenewalStage.MISSED_WINDOW] else None


def _calculate_late_fee(renewal_stage: str, expiry_date: date, today: date) -> Tuple[float, str]:
    if renewal_stage == RenewalStage.GRACE_PERIOD:
        months_in_grace = relativedelta(today, expiry_date).months
        if months_in_grace < 1:
            months_in_grace = 1
        base_fee = settings.RENEWAL_OFFICIAL_FEE
        rate_fee = base_fee * settings.GRACE_PERIOD_LATE_FEE_RATE * months_in_grace
        late_fee = settings.GRACE_PERIOD_LATE_FEE_BASE + rate_fee
        return round(late_fee, 2), settings.FEE_CURRENCY
    elif renewal_stage == RenewalStage.MISSED_WINDOW:
        return round(settings.RENEWAL_OFFICIAL_FEE * 2, 2), settings.FEE_CURRENCY
    else:
        return 0.0, settings.FEE_CURRENCY


def _calculate_latest_submit_date(trademark: Trademark, renewal_stage: str, today: date) -> date:
    expiry_date = trademark.expiry_date
    grace_period_end = trademark.grace_period_end or (expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS))

    if renewal_stage in [RenewalStage.GRACE_PERIOD, RenewalStage.MISSED_WINDOW]:
        deadline = grace_period_end
    else:
        deadline = expiry_date

    buffer_days = settings.PROCESSING_BUFFER_DAYS
    latest = deadline - timedelta(days=buffer_days)

    if latest < today:
        latest = today + timedelta(days=1)

    return latest


def _get_required_materials(
    db: Session,
    trademark: Trademark,
    renewal_stage: str
) -> Tuple[List[RiskMaterialItem], List[str]]:
    materials_config = [
        (MaterialType.POWER_OF_ATTORNEY.value, "代理委托书", True, "需加盖公章的代理委托书原件"),
        (MaterialType.BUSINESS_LICENSE.value, "主体资格证明（营业执照）", True, "最新年检的营业执照副本复印件"),
        (MaterialType.TRADEMARK_LIST.value, "商标续展清单", True, "列明所有续展商标的清单"),
    ]

    if trademark.has_subject_change == 1:
        materials_config.append(("subject_change_proof", "主体变更证明", True, "工商变更证明文件原件"))

    if renewal_stage == RenewalStage.GRACE_PERIOD:
        materials_config.append(("grace_period_statement", "宽展期声明", True, "说明在宽展期内申请续展的书面声明"))

    current_materials = db.query(MaterialVersion).filter(
        MaterialVersion.trademark_id == trademark.id,
        MaterialVersion.is_deleted == False,
        MaterialVersion.is_current == True
    ).all()

    material_map = {m.material_type.value: m for m in current_materials}

    result_items: List[RiskMaterialItem] = []
    missing: List[str] = []

    for mat_type, mat_name, required, notes in materials_config:
        current = material_map.get(mat_type)
        has_current = current is not None and current.is_approved

        item = RiskMaterialItem(
            material_type=mat_type,
            material_name=mat_name,
            required=required,
            has_current=has_current,
            current_version=current.version if current else None,
            notes=notes if not has_current else None
        )
        result_items.append(item)

        if required and not has_current:
            missing.append(mat_name)

    return result_items, missing


def _assess_risk_factors(
    trademark: Trademark,
    renewal_stage: str,
    urgency_level: str,
    missing_materials: List[str],
    db: Session
) -> List[str]:
    factors: List[str] = []

    if renewal_stage == RenewalStage.MISSED_WINDOW:
        factors.append("已错过续展窗口，商标存在注销风险")
    elif renewal_stage == RenewalStage.GRACE_PERIOD:
        factors.append("已进入宽展期，需缴纳额外滞纳金")

    if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.OVERDUE]:
        factors.append("办理时间紧迫，需优先处理")

    if missing_materials:
        factors.append(f"缺少必要材料：{', '.join(missing_materials)}")

    unpaid_fees = db.query(Fee).filter(
        Fee.trademark_id == trademark.id,
        Fee.is_deleted == False,
        Fee.status != FeeStatus.PAID
    ).count()
    if unpaid_fees > 0:
        factors.append(f"存在 {unpaid_fees} 项未支付费用")

    if trademark.has_subject_change == 1:
        factors.append("客户主体已变更，需补充变更证明")

    no_agent = trademark.assigned_agent_id is None
    if no_agent:
        factors.append("尚未分配代理人")

    return factors


def _get_reminder_stats(db: Session, trademark_id: int) -> Tuple[int, Optional[date]]:
    reminders = db.query(Reminder).filter(
        Reminder.trademark_id == trademark_id,
        Reminder.is_deleted == False,
        Reminder.reminder_type.in_([ReminderType.EXPIRY.value, ReminderType.GRACE_PERIOD.value])
    ).all()

    count = len(reminders)
    last_date = None
    for r in reminders:
        if r.reminder_date:
            if last_date is None or r.reminder_date > last_date:
                last_date = r.reminder_date

    return count, last_date


def build_risk_queue_item(db: Session, trademark: Trademark, today: Optional[date] = None) -> RiskQueueItem:
    if today is None:
        today = date.today()

    if not trademark.grace_period_end:
        trademark.grace_period_end = trademark.expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS)

    renewal_stage = _calculate_renewal_stage(trademark, today)
    urgency_level, urgency_score, days_until_deadline, days_until_grace_end = _calculate_urgency(
        trademark, today, renewal_stage
    )
    late_fee_amount, late_fee_currency = _calculate_late_fee(renewal_stage, trademark.expiry_date, today)
    latest_submit_date = _calculate_latest_submit_date(trademark, renewal_stage, today)
    required_materials, missing_materials = _get_required_materials(db, trademark, renewal_stage)
    risk_factors = _assess_risk_factors(trademark, renewal_stage, urgency_level, missing_materials, db)
    reminder_count, last_reminder_date = _get_reminder_stats(db, trademark.id)

    customer_name = trademark.customer.name if trademark.customer else "未知客户"
    agent_name = trademark.assigned_agent.full_name if trademark.assigned_agent else None

    return RiskQueueItem(
        trademark_id=trademark.id,
        registration_number=trademark.registration_number,
        trademark_name=trademark.trademark_name,
        international_class=trademark.international_class,
        customer_id=trademark.customer_id,
        customer_name=customer_name,
        assigned_agent_id=trademark.assigned_agent_id,
        assigned_agent_name=agent_name,
        expiry_date=trademark.expiry_date,
        grace_period_end=trademark.grace_period_end,
        renewal_stage=renewal_stage,
        urgency_level=urgency_level,
        urgency_score=urgency_score,
        days_until_expiry=(trademark.expiry_date - today).days,
        days_until_grace_end=days_until_grace_end,
        days_until_deadline=days_until_deadline,
        latest_submit_date=latest_submit_date,
        late_fee_amount=late_fee_amount,
        late_fee_currency=late_fee_currency,
        required_materials=required_materials,
        missing_materials=missing_materials,
        risk_factors=risk_factors,
        reminder_count=reminder_count,
        last_reminder_date=last_reminder_date
    )


def get_risk_queue(
    db: Session,
    include_pre_renewal: bool = True,
    include_renewal_period: bool = True,
    include_grace_period: bool = True,
    include_missed_window: bool = True,
    min_urgency_level: Optional[str] = None,
    assigned_agent_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    keyword: Optional[str] = None,
    sort_by: str = "urgency_score",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50
) -> RiskQueueResponse:
    today = date.today()

    pre_renewal_start = today + timedelta(days=0)
    if include_pre_renewal:
        pre_renewal_start = today - timedelta(days=1)

    query = db.query(Trademark).filter(
        Trademark.is_deleted == False
    )

    stages_to_include = []
    if include_pre_renewal:
        stages_to_include.append(RenewalStage.PRE_RENEWAL)
    if include_renewal_period:
        stages_to_include.append(RenewalStage.RENEWAL_PERIOD)
    if include_grace_period:
        stages_to_include.append(RenewalStage.GRACE_PERIOD)
    if include_missed_window:
        stages_to_include.append(RenewalStage.MISSED_WINDOW)

    if assigned_agent_id is not None:
        query = query.filter(Trademark.assigned_agent_id == assigned_agent_id)
    if customer_id is not None:
        query = query.filter(Trademark.customer_id == customer_id)
    if keyword:
        kw_pattern = f"%{keyword}%"
        query = query.filter(
            (Trademark.trademark_name.ilike(kw_pattern)) |
            (Trademark.registration_number.ilike(kw_pattern))
        )

    all_trademarks = query.all()

    all_items: List[RiskQueueItem] = []
    for tm in all_trademarks:
        if not tm.grace_period_end:
            tm.grace_period_end = tm.expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS)
        stage = _calculate_renewal_stage(tm, today)
        if stage not in stages_to_include:
            continue

        try:
            item = build_risk_queue_item(db, tm, today)
        except Exception:
            continue

        if min_urgency_level:
            level_order = {
                UrgencyLevel.NORMAL: 0,
                UrgencyLevel.ATTENTION: 1,
                UrgencyLevel.WARNING: 2,
                UrgencyLevel.CRITICAL: 3,
                UrgencyLevel.OVERDUE: 4,
            }
            if level_order.get(item.urgency_level, 0) < level_order.get(min_urgency_level, 0):
                continue

        all_items.append(item)

    reverse = sort_order.lower() == "desc"
    if sort_by == "urgency_score":
        all_items.sort(key=lambda x: x.urgency_score, reverse=reverse)
    elif sort_by == "days_until_deadline":
        all_items.sort(key=lambda x: x.days_until_deadline, reverse=reverse)
    elif sort_by == "late_fee_amount":
        all_items.sort(key=lambda x: x.late_fee_amount, reverse=reverse)
    elif sort_by == "expiry_date":
        all_items.sort(key=lambda x: x.expiry_date, reverse=reverse)
    else:
        all_items.sort(key=lambda x: x.urgency_score, reverse=True)

    total = len(all_items)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = all_items[start_idx:end_idx]

    summary = {
        "total": total,
        "by_stage": {
            RenewalStage.PRE_RENEWAL: len([i for i in all_items if i.renewal_stage == RenewalStage.PRE_RENEWAL]),
            RenewalStage.RENEWAL_PERIOD: len([i for i in all_items if i.renewal_stage == RenewalStage.RENEWAL_PERIOD]),
            RenewalStage.GRACE_PERIOD: len([i for i in all_items if i.renewal_stage == RenewalStage.GRACE_PERIOD]),
            RenewalStage.MISSED_WINDOW: len([i for i in all_items if i.renewal_stage == RenewalStage.MISSED_WINDOW]),
        },
        "by_urgency": {
            UrgencyLevel.NORMAL: len([i for i in all_items if i.urgency_level == UrgencyLevel.NORMAL]),
            UrgencyLevel.ATTENTION: len([i for i in all_items if i.urgency_level == UrgencyLevel.ATTENTION]),
            UrgencyLevel.WARNING: len([i for i in all_items if i.urgency_level == UrgencyLevel.WARNING]),
            UrgencyLevel.CRITICAL: len([i for i in all_items if i.urgency_level == UrgencyLevel.CRITICAL]),
            UrgencyLevel.OVERDUE: len([i for i in all_items if i.urgency_level == UrgencyLevel.OVERDUE]),
        },
        "total_late_fee_potential": round(sum(i.late_fee_amount for i in all_items), 2),
        "trademarks_missing_materials": len([i for i in all_items if i.missing_materials]),
        "trademarks_with_risk_factors": len([i for i in all_items if i.risk_factors]),
    }

    agent_map: Dict[int, AgentRiskSummary] = {}
    agents = db.query(User).filter(
        User.is_deleted == False,
        User.role == UserRole.AGENT
    ).all()

    for agent in agents:
        agent_map[agent.id] = AgentRiskSummary(
            agent_id=agent.id,
            agent_name=agent.full_name,
            total_trademarks=0,
            critical_count=0,
            warning_count=0,
            attention_count=0,
            normal_count=0,
            overdue_count=0,
            total_risk_score=0,
            average_risk_score=0.0
        )

    for item in all_items:
        aid = item.assigned_agent_id
        if aid and aid in agent_map:
            a = agent_map[aid]
            a.total_trademarks += 1
            a.total_risk_score += item.urgency_score

            if item.urgency_level == UrgencyLevel.CRITICAL:
                a.critical_count += 1
            elif item.urgency_level == UrgencyLevel.WARNING:
                a.warning_count += 1
            elif item.urgency_level == UrgencyLevel.ATTENTION:
                a.attention_count += 1
            elif item.urgency_level == UrgencyLevel.NORMAL:
                a.normal_count += 1
            elif item.urgency_level == UrgencyLevel.OVERDUE:
                a.overdue_count += 1

    for aid, a in agent_map.items():
        if a.total_trademarks > 0:
            a.average_risk_score = round(a.total_risk_score / a.total_trademarks, 2)

    agent_rankings = sorted(
        agent_map.values(),
        key=lambda x: (x.critical_count * 1000 + x.overdue_count * 1000 + x.warning_count * 100 + x.total_risk_score),
        reverse=True
    )

    return RiskQueueResponse(
        items=paged_items,
        total=total,
        summary=summary,
        agent_rankings=agent_rankings
    )


def get_customer_risk_reminders(
    db: Session,
    customer_id: Optional[int] = None,
    min_urgency_level: str = UrgencyLevel.ATTENTION
) -> List[CustomerReminderItem]:
    today = date.today()
    level_order = {
        UrgencyLevel.NORMAL: 0,
        UrgencyLevel.ATTENTION: 1,
        UrgencyLevel.WARNING: 2,
        UrgencyLevel.CRITICAL: 3,
        UrgencyLevel.OVERDUE: 4,
    }

    customers_query = db.query(Customer).filter(Customer.is_deleted == False)
    if customer_id is not None:
        customers_query = customers_query.filter(Customer.id == customer_id)
    customers = customers_query.all()

    result: List[CustomerReminderItem] = []

    for customer in customers:
        trademarks = db.query(Trademark).filter(
            Trademark.customer_id == customer.id,
            Trademark.is_deleted == False
        ).all()

        customer_risk_items: List[RiskQueueItem] = []
        for tm in trademarks:
            if not tm.grace_period_end:
                tm.grace_period_end = tm.expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS)
            try:
                item = build_risk_queue_item(db, tm, today)
            except Exception:
                continue

            if level_order.get(item.urgency_level, 0) >= level_order.get(min_urgency_level, 1):
                customer_risk_items.append(item)

        if not customer_risk_items:
            continue

        customer_risk_items.sort(key=lambda x: x.urgency_score, reverse=True)

        critical_count = len([i for i in customer_risk_items if i.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.OVERDUE]])

        if critical_count > 0:
            summary_message = (
                f"紧急提醒：贵司有 {critical_count} 件商标需要立即处理续展手续，"
                f"共 {len(customer_risk_items)} 件商标存在临期风险，请尽快联系代理人。"
            )
        else:
            summary_message = (
                f"温馨提醒：贵司有 {len(customer_risk_items)} 件商标即将到期，"
                f"请及时办理续展手续，避免商标权利失效。"
            )

        result.append(CustomerReminderItem(
            customer_id=customer.id,
            customer_name=customer.name,
            customer_email=customer.email,
            customer_phone=customer.phone,
            trademarks=customer_risk_items,
            total_risk_count=len(customer_risk_items),
            critical_count=critical_count,
            summary_message=summary_message
        ))

    result.sort(key=lambda x: (x.critical_count, x.total_risk_count), reverse=True)
    return result


def auto_generate_risk_reminders(
    db: Session,
    include_customer_reminders: bool = True,
    min_urgency_for_customer: str = UrgencyLevel.WARNING
) -> Dict[str, Any]:
    today = date.today()
    queue_response = get_risk_queue(db, page=1, page_size=10000)

    high_risk_items = [
        i for i in queue_response.items
        if i.urgency_level in [UrgencyLevel.WARNING, UrgencyLevel.CRITICAL, UrgencyLevel.OVERDUE]
    ]

    existing_reminder_keys = set()
    existing = db.query(Reminder).filter(
        Reminder.is_deleted == False,
        Reminder.reminder_type.in_([ReminderType.EXPIRY.value, ReminderType.GRACE_PERIOD.value]),
        Reminder.status != ReminderStatus.RESOLVED.value
    ).all()
    for r in existing:
        existing_reminder_keys.add((r.trademark_id, r.reminder_type))

    created_reminders: List[Dict[str, Any]] = []

    for item in high_risk_items:
        reminder_type = (
            ReminderType.GRACE_PERIOD.value
            if item.renewal_stage == RenewalStage.GRACE_PERIOD
            else ReminderType.EXPIRY.value
        )

        if (item.trademark_id, reminder_type) in existing_reminder_keys:
            continue

        customer = db.query(Customer).filter(
            Customer.id == item.customer_id,
            Customer.is_deleted == False
        ).first()

        if item.urgency_level == UrgencyLevel.OVERDUE:
            priority = 3
            escalation_level = 3
        elif item.urgency_level == UrgencyLevel.CRITICAL:
            priority = 3
            escalation_level = 3
        else:
            priority = 2
            escalation_level = 2

        if item.missing_materials:
            materials_note = f"\n需要补齐的材料：{', '.join(item.missing_materials)}"
        else:
            materials_note = ""

        if item.late_fee_amount > 0:
            fee_note = f"\n预计滞纳金：¥{item.late_fee_amount}"
        else:
            fee_note = ""

        reminder_data = {
            "reminder_type": reminder_type,
            "reminder_date": today,
            "deadline_date": item.latest_submit_date,
            "days_remaining": item.days_until_deadline,
            "title": f"[{'紧急' if priority == 3 else '重要'}] 商标续展风险提醒 - {item.trademark_name}",
            "content": (
                f"商标「{item.trademark_name}」（注册号: {item.registration_number}，类别: 第{item.international_class}类）"
                f"当前处于「{item.renewal_stage}」，风险等级：{item.urgency_level}。\n"
                f"有效期至：{item.expiry_date}\n"
                f"最晚提交日：{item.latest_submit_date}\n"
                f"剩余天数：{item.days_until_deadline} 天"
                f"{fee_note}"
                f"{materials_note}"
            ),
            "recipient": item.assigned_agent_name or (customer.name if customer else None),
            "recipient_email": (
                trademark.assigned_agent.email
                if (trademark := db.query(Trademark).filter(Trademark.id == item.trademark_id).first()) and trademark.assigned_agent
                else (customer.email if customer else None)
            ),
            "recipient_phone": customer.phone if customer else None,
            "status": ReminderStatus.PENDING.value,
            "priority": priority,
            "escalation_level": escalation_level,
            "trademark_id": item.trademark_id,
            "notes": (
                f"风险因素：{'; '.join(item.risk_factors)}\n"
                f"紧急程度评分：{item.urgency_score}"
            )
        }

        reminder = Reminder(**reminder_data)
        db.add(reminder)
        created_reminders.append({
            "id": reminder.id,
            "trademark_id": item.trademark_id,
            "trademark_name": item.trademark_name,
            "reminder_type": reminder_type,
            "urgency_level": item.urgency_level
        })

    db.commit()

    customer_reminders: List[Dict[str, Any]] = []
    if include_customer_reminders:
        customer_items = get_customer_risk_reminders(db, min_urgency_level=min_urgency_for_customer)
        for ci in customer_items:
            if not ci.customer_email:
                continue

            existing_customer = db.query(Reminder).filter(
                Reminder.is_deleted == False,
                Reminder.status != ReminderStatus.RESOLVED.value,
                Reminder.reminder_type == ReminderType.EXPIRY.value,
                Reminder.recipient_email == ci.customer_email
            ).first()

            if existing_customer:
                continue

            critical_tms = [t for t in ci.trademarks if t.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.OVERDUE]]
            priority = 3 if critical_tms else 2
            escalation_level = 3 if critical_tms else 2

            first_trademark_id = ci.trademarks[0].trademark_id if ci.trademarks else None

            details = "\n".join([
                f"- {t.trademark_name}（{t.registration_number}）：{t.urgency_level}，最晚提交 {t.latest_submit_date}"
                for t in ci.trademarks[:5]
            ])
            if len(ci.trademarks) > 5:
                details += f"\n... 另有 {len(ci.trademarks) - 5} 件商标"

            reminder_data = {
                "reminder_type": ReminderType.EXPIRY.value,
                "reminder_date": today,
                "deadline_date": min((t.latest_submit_date for t in ci.trademarks), default=today),
                "days_remaining": min((t.days_until_deadline for t in ci.trademarks), default=0),
                "title": f"[客户提醒] 商标续展风险汇总 - {ci.customer_name}",
                "content": (
                    f"尊敬的 {ci.customer_name}：\n\n"
                    f"{ci.summary_message}\n\n"
                    f"商标明细：\n{details}\n\n"
                    f"请尽快与我司代理人联系办理续展手续，以避免商标权利受损。"
                ),
                "recipient": ci.customer_name,
                "recipient_email": ci.customer_email,
                "recipient_phone": ci.customer_phone,
                "status": ReminderStatus.PENDING.value,
                "priority": priority,
                "escalation_level": escalation_level,
                "trademark_id": first_trademark_id,
                "notes": (
                    f"客户提醒：共 {ci.total_risk_count} 件商标存在风险，"
                    f"其中 {ci.critical_count} 件需要紧急处理"
                )
            }

            reminder = Reminder(**reminder_data)
            db.add(reminder)
            customer_reminders.append({
                "customer_id": ci.customer_id,
                "customer_name": ci.customer_name,
                "trademark_count": ci.total_risk_count,
                "critical_count": ci.critical_count
            })

    db.commit()

    return {
        "total_risk_items": queue_response.total,
        "high_risk_count": len(high_risk_items),
        "agent_reminders_created": len(created_reminders),
        "agent_reminders": created_reminders,
        "customer_reminders_created": len(customer_reminders),
        "customer_reminders": customer_reminders,
        "summary": queue_response.summary
    }
