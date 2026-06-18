from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.trademark import Trademark, TrademarkStatus
from app.models.customer import Customer
from app.models.fee import Fee, FeeStatus
from app.models.material_version import MaterialVersion, MaterialType
from app.models.submission_record import SubmissionRecord
from app.models.agency_entrustment import AgencyEntrustment
from app.models.reminder import Reminder, ReminderType, ReminderStatus
from app.schemas.common import (
    TrademarkValidationResponse,
    ValidationIssue,
    BulkOperationResponse
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
