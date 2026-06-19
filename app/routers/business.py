from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import (
    BulkOperationResponse,
    TrademarkValidationResponse,
    BulkOperationRequest
)
from app.services import business_service

router = APIRouter(prefix="/api/business", tags=["核心业务"])


@router.get("/expiring-trademarks")
@router.get("/expiring")
def get_expiring_trademarks(
    days_threshold: int = Query(180, ge=1, le=365, description="临期天数阈值"),
    auto_generate_reminders: bool = Query(False, description="是否自动生成提醒"),
    db: Session = Depends(get_db)
):
    try:
        result = business_service.check_expiry_and_generate_reminders(
            db=db,
            days_threshold=days_threshold,
            auto_generate=auto_generate_reminders
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取临期商标失败: {str(e)}"
        )


@router.post("/check-materials-coverage")
def check_materials_coverage(
    trademark_ids: List[int] = Body(..., description="商标ID列表"),
    db: Session = Depends(get_db)
):
    try:
        if not trademark_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供商标ID列表"
            )
        all_covered, coverage_status, uncovered = business_service.check_materials_coverage(
            db=db,
            trademark_ids=trademark_ids
        )
        return {
            "all_covered": all_covered,
            "uncovered_count": len(uncovered),
            "coverage_status": coverage_status,
            "uncovered_trademark_ids": uncovered
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"材料覆盖检测失败: {str(e)}"
        )


@router.post("/check-duplicate-submissions")
def check_duplicate_submissions(
    trademark_ids: List[int] = Body(..., description="商标ID列表"),
    submission_date: Optional[date] = Body(None, description="提交日期"),
    days_window: int = Body(30, ge=1, le=365, description="检测时间窗口（天）"),
    db: Session = Depends(get_db)
):
    try:
        if not trademark_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供商标ID列表"
            )
        has_duplicates, duplicates = business_service.check_duplicate_submissions(
            db=db,
            trademark_ids=trademark_ids,
            submission_date=submission_date,
            days_window=days_window
        )
        return {
            "has_duplicates": has_duplicates,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重复提交检测失败: {str(e)}"
        )


@router.post("/check-unpaid-fees")
def check_unpaid_fees(
    trademark_ids: List[int] = Body(..., description="商标ID列表"),
    db: Session = Depends(get_db)
):
    try:
        if not trademark_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供商标ID列表"
            )
        has_unpaid, unpaid_fees = business_service.check_unpaid_fees(
            db=db,
            trademark_ids=trademark_ids
        )
        return {
            "has_unpaid": has_unpaid,
            "unpaid_count": len(unpaid_fees),
            "unpaid_fees": unpaid_fees
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"费用未付检测失败: {str(e)}"
        )


@router.post("/check-subject-changes")
def check_subject_changes(
    trademark_ids: List[int] = Body(..., description="商标ID列表"),
    db: Session = Depends(get_db)
):
    try:
        if not trademark_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供商标ID列表"
            )
        has_changes, changes = business_service.check_subject_changes(
            db=db,
            trademark_ids=trademark_ids
        )
        return {
            "has_changes": has_changes,
            "changed_count": len(changes),
            "changes": changes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"主体变更检测失败: {str(e)}"
        )


@router.get("/validate/{trademark_id}", response_model=TrademarkValidationResponse)
def validate_trademark(
    trademark_id: int,
    check_materials: bool = Query(True, description="是否检测材料"),
    check_fees: bool = Query(True, description="是否检测费用"),
    check_duplicates: bool = Query(True, description="是否检测重复提交"),
    check_subject: bool = Query(True, description="是否检测主体变更"),
    db: Session = Depends(get_db)
):
    try:
        return business_service.validate_trademark_for_submission(
            db=db,
            trademark_id=trademark_id,
            check_materials=check_materials,
            check_fees=check_fees,
            check_duplicates=check_duplicates,
            check_subject=check_subject
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"商标验证失败: {str(e)}"
        )


@router.post("/batch-validate", response_model=List[TrademarkValidationResponse])
def batch_validate_trademarks(
    trademark_ids: List[int] = Body(..., description="商标ID列表"),
    db: Session = Depends(get_db)
):
    try:
        if not trademark_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供商标ID列表"
            )
        return business_service.batch_validate_trademarks(
            db=db,
            trademark_ids=trademark_ids
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量验证失败: {str(e)}"
        )


@router.post("/batch-renew", response_model=BulkOperationResponse)
def batch_renew_trademarks(
    trademark_ids: List[int] = Body(..., description="商标ID列表"),
    submission_date: Optional[date] = Body(None, description="提交日期"),
    submission_channel: str = Body("online", description="提交渠道"),
    submitted_by_id: Optional[int] = Body(None, description="提交人ID"),
    skip_validation: bool = Body(False, description="是否跳过验证"),
    db: Session = Depends(get_db)
):
    try:
        return business_service.batch_renew_trademarks(
            db=db,
            trademark_ids=trademark_ids,
            submission_date=submission_date,
            submission_channel=submission_channel,
            submitted_by_id=submitted_by_id,
            skip_validation=skip_validation
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量续展失败: {str(e)}"
        )


@router.post("/pre-submission-check")
def pre_submission_check(
    request: BulkOperationRequest,
    db: Session = Depends(get_db)
):
    try:
        if not request.ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择至少一个商标"
            )

        materials_ok, coverage_status, uncovered = business_service.check_materials_coverage(
            db, request.ids
        )
        fees_ok, unpaid_fees = business_service.check_unpaid_fees(
            db, request.ids
        )
        duplicates_ok, duplicates = business_service.check_duplicate_submissions(
            db, request.ids
        )
        subject_ok, changes = business_service.check_subject_changes(
            db, request.ids
        )

        can_proceed = materials_ok and fees_ok

        issues: List[Dict[str, Any]] = []

        if not materials_ok:
            for tid, problems in coverage_status.items():
                if problems:
                    issues.append({
                        "trademark_id": tid,
                        "type": "materials",
                        "severity": "error",
                        "issues": problems
                    })

        if not fees_ok:
            for tid, fees in unpaid_fees.items():
                issues.append({
                    "trademark_id": tid,
                    "type": "fees",
                    "severity": "error",
                    "issues": [f"{len(fees)} 项费用未支付"]
                })

        if duplicates_ok:
            for tid, subs in duplicates.items():
                issues.append({
                    "trademark_id": tid,
                    "type": "duplicates",
                    "severity": "warning",
                    "issues": [f"存在 {len(subs)} 条重复提交记录"]
                })

        if subject_ok:
            for tid, info in changes.items():
                issues.append({
                    "trademark_id": tid,
                    "type": "subject_change",
                    "severity": "warning",
                    "issues": ["客户主体已变更"]
                })

        return {
            "can_proceed": can_proceed,
            "total_checked": len(request.ids),
            "issues_count": len(issues),
            "issues": issues,
            "materials_ok": materials_ok,
            "fees_ok": not fees_ok,
            "has_duplicates": duplicates_ok,
            "has_subject_changes": subject_ok
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交前检查失败: {str(e)}"
        )
