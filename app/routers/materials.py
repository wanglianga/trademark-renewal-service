from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import User
from app.models.material_version import MaterialType
from app.schemas import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialUploadResponse,
    MaterialVersionHistoryItem,
    CorrectionMaterialSummary,
    PaginatedResponse,
)
from app.services import material_service

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("", response_model=PaginatedResponse[MaterialResponse])
def list_materials(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    material_type: Optional[MaterialType] = Query(None, description="材料类型"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    is_current: Optional[bool] = Query(None, description="是否为当前版本"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    skip = (page - 1) * page_size
    materials, total = material_service.list_materials(
        db,
        skip=skip,
        limit=page_size,
        material_type=material_type,
        customer_id=customer_id,
        trademark_id=trademark_id,
        is_current=is_current,
        keyword=keyword
    )
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=materials,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/correction-types")
def get_correction_material_types(
    current_user: User = Depends(get_current_active_user)
):
    return {
        "success": True,
        "types": [
            {
                "type": "power_of_attorney",
                "label": "委托书",
                "material_type": MaterialType.CORRECTION_POWER_OF_ATTORNEY.value,
                "description": "官方要求补正代理委托书（签字/盖章）"
            },
            {
                "type": "subject_qualification",
                "label": "主体资格证明",
                "material_type": MaterialType.CORRECTION_SUBJECT_QUALIFICATION.value,
                "description": "官方要求补正申请人主体资格证明（营业执照等）"
            },
            {
                "type": "category_description",
                "label": "类别说明",
                "material_type": MaterialType.CORRECTION_CATEGORY_DESCRIPTION.value,
                "description": "官方要求补正商品/服务类别说明或限定"
            },
            {
                "type": "chinese_translation",
                "label": "中文译名",
                "material_type": MaterialType.CORRECTION_CHINESE_TRANSLATION.value,
                "description": "官方要求补正外文商标的中文译名说明"
            },
            {
                "type": "other",
                "label": "其他补正材料",
                "material_type": MaterialType.CORRECTION_OTHER.value,
                "description": "其他官方要求的补正材料"
            },
        ]
    }


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return material_service.get_material(db, material_id)


@router.get("/current/{material_type}", response_model=Optional[MaterialResponse])
def get_current_version(
    material_type: MaterialType,
    customer_id: Optional[int] = Query(None, description="客户ID"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return material_service.get_current_version(
        db,
        material_type=material_type,
        customer_id=customer_id,
        trademark_id=trademark_id
    )


@router.get("/versions/{material_type}", response_model=List[MaterialResponse])
def list_versions(
    material_type: MaterialType,
    customer_id: Optional[int] = Query(None, description="客户ID"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return material_service.list_versions(
        db,
        material_type=material_type,
        customer_id=customer_id,
        trademark_id=trademark_id
    )


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_in: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return material_service.create_material(db, material_in)


@router.post("/upload", response_model=MaterialUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
    material_type: MaterialType = Form(..., description="材料类型"),
    customer_id: Optional[int] = Form(None, description="客户ID"),
    trademark_id: Optional[int] = Form(None, description="商标ID"),
    description: Optional[str] = Form(None, description="描述"),
    uploaded_by: Optional[str] = Form(None, description="上传人"),
    replaced_reason: Optional[str] = Form(None, description="替换上一版本的原因"),
    handled_by: Optional[str] = Form(None, description="处理人"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    material, replaced_prev, prev_version_id = await material_service.upload_file(
        db,
        file=file,
        material_type=material_type,
        customer_id=customer_id,
        trademark_id=trademark_id,
        description=description,
        uploaded_by=uploaded_by,
        replaced_reason=replaced_reason,
        handled_by=handled_by,
    )
    return MaterialUploadResponse(
        success=True,
        material_id=material.id,
        file_name=material.file_name,
        file_path=material.file_path,
        version=material.version,
        message="File uploaded successfully",
        replaced_previous=replaced_prev,
        replaced_previous_version=prev_version_id,
        replaced_reason_recorded=replaced_reason,
    )


@router.post("/upload-for-correction", status_code=status.HTTP_201_CREATED)
async def upload_correction_material(
    file: UploadFile = File(..., description="补正材料文件"),
    correction_id: int = Form(..., description="补正记录ID"),
    correction_type_required: Optional[str] = Form(
        None,
        description="官方要求补正类型：power_of_attorney/subject_qualification/category_description/chinese_translation/other"
    ),
    replaced_reason: Optional[str] = Form(None, description="替换上一版本的原因说明（必填，历史文件不可直接覆盖）"),
    handled_by: Optional[str] = Form(None, description="处理人"),
    uploaded_by: Optional[str] = Form(None, description="上传人"),
    description: Optional[str] = Form(None, description="备注说明"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        material, replaced_prev, prev_version_id = await material_service.upload_correction_material(
            db=db,
            file=file,
            correction_id=correction_id,
            correction_type_required=correction_type_required,
            replaced_reason=replaced_reason,
            handled_by=handled_by or current_user.full_name,
            uploaded_by=uploaded_by or current_user.full_name,
            description=description,
        )
        return {
            "success": True,
            "id": material.id,
            "material_id": material.id,
            "version": material.version,
            "material_type": material.material_type.value,
            "correction_id": material.correction_id,
            "correction_type_required": material.correction_type_required,
            "file_name": material.file_name,
            "file_path": material.file_path,
            "submitted_at": material.submitted_at,
            "handled_by": material.handled_by,
            "uploaded_by": material.uploaded_by,
            "is_current": material.is_current,
            "is_replaced": material.is_replaced,
            "replaced_at": material.replaced_at,
            "replaced_reason": material.replaced_reason,
            "is_approved": material.is_approved,
            "replaced_previous": replaced_prev,
            "replaced_previous_version": prev_version_id,
            "replaced_reason_recorded": replaced_reason,
            "message": "补正材料上传成功，历史版本已保留不会被覆盖"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"补正材料上传失败: {str(e)}"
        )


@router.get("/by-correction/{correction_id}", response_model=CorrectionMaterialSummary)
def get_correction_materials(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        return material_service.get_correction_material_summary(db, correction_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取补正材料列表失败: {str(e)}"
        )


@router.get("/{material_id}/history", response_model=List[MaterialVersionHistoryItem])
def get_material_history(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        versions = material_service.get_material_version_history(db, material_id)
        result: List[MaterialVersionHistoryItem] = []
        for m in versions:
            result.append(MaterialVersionHistoryItem(
                id=m.id,
                version=m.version,
                file_name=m.file_name,
                material_type=m.material_type.value if hasattr(m.material_type, 'value') else str(m.material_type),
                uploaded_by=m.uploaded_by,
                handled_by=m.handled_by,
                created_at=m.created_at,
                submitted_at=m.submitted_at,
                is_current=m.is_current,
                is_replaced=m.is_replaced,
                is_approved=m.is_approved,
                replaced_reason=m.replaced_reason,
                replaced_at=m.replaced_at,
                correction_id=m.correction_id,
                correction_type_required=m.correction_type_required,
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取材料版本历史失败: {str(e)}"
        )


@router.post("/{material_id}/approve")
def approve_material(
    material_id: int,
    body: Dict[str, Any] = Body(..., description="审核参数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        approved_by = body.get("approved_by", current_user.full_name)
        notes = body.get("notes") or body.get("approval_notes") or body.get("review_notes")
        mat = material_service.approve_material(
            db,
            material_id=material_id,
            approved_by=approved_by,
            review_notes=notes,
        )
        return {
            "id": mat.id,
            "material_id": mat.id,
            "is_approved": mat.is_approved,
            "approved_by": mat.approved_by,
            "approved_at": mat.approved_at,
            "approval_notes": mat.approval_notes or notes,
            "review_notes": mat.review_notes,
            "version": mat.version,
            "material_type": mat.material_type.value if hasattr(mat.material_type, 'value') else str(mat.material_type),
            "success": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"材料审核失败: {str(e)}"
        )


@router.post("/{material_id}/protect")
def protect_historical_version(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        protected = material_service.protect_historical_material(db, material_id)
        return {
            "protected": True,
            "material_id": material_id,
            "message": "历史版本已保护，不可被覆盖或删除",
            "success": True,
            "is_locked": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保护历史版本失败: {str(e)}"
        )


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_in: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return material_service.update_material(db, material_id, material_in)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    material_service.delete_material(db, material_id)
