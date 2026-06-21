from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.models import MaterialVersion
from app.models.material_version import (
    MaterialType,
    CORRECTION_MATERIAL_TYPES,
    CORRECTION_TYPE_MATERIAL_MAP,
)
from app.models.correction import Correction
from app.schemas import MaterialCreate, MaterialUpdate
from app.utils.file_utils import save_upload_file


def list_materials(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    material_type: Optional[MaterialType] = None,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None,
    is_current: Optional[bool] = None,
    keyword: Optional[str] = None
) -> Tuple[List[MaterialVersion], int]:
    query = db.query(MaterialVersion).filter(MaterialVersion.is_deleted == False)
    
    if material_type:
        query = query.filter(MaterialVersion.material_type == material_type)
    if customer_id:
        query = query.filter(MaterialVersion.customer_id == customer_id)
    if trademark_id:
        query = query.filter(MaterialVersion.trademark_id == trademark_id)
    if is_current is not None:
        query = query.filter(MaterialVersion.is_current == is_current)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (MaterialVersion.file_name.ilike(search_pattern)) |
            (MaterialVersion.description.ilike(search_pattern))
        )
    
    total = query.count()
    materials = query.order_by(MaterialVersion.id.desc()).offset(skip).limit(limit).all()
    return materials, total


def get_material(db: Session, material_id: int) -> MaterialVersion:
    material = db.query(MaterialVersion).filter(
        MaterialVersion.id == material_id,
        MaterialVersion.is_deleted == False
    ).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    return material


def get_current_version(
    db: Session,
    material_type: MaterialType,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None
) -> Optional[MaterialVersion]:
    query = db.query(MaterialVersion).filter(
        MaterialVersion.material_type == material_type,
        MaterialVersion.is_current == True,
        MaterialVersion.is_deleted == False
    )
    
    if customer_id:
        query = query.filter(MaterialVersion.customer_id == customer_id)
    if trademark_id:
        query = query.filter(MaterialVersion.trademark_id == trademark_id)
    
    return query.first()


def list_versions(
    db: Session,
    material_type: MaterialType,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None
) -> List[MaterialVersion]:
    query = db.query(MaterialVersion).filter(
        MaterialVersion.material_type == material_type,
        MaterialVersion.is_deleted == False
    )
    
    if customer_id:
        query = query.filter(MaterialVersion.customer_id == customer_id)
    if trademark_id:
        query = query.filter(MaterialVersion.trademark_id == trademark_id)
    
    return query.order_by(MaterialVersion.version.desc()).all()


def get_next_version(
    db: Session,
    material_type: MaterialType,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None
) -> int:
    query = db.query(MaterialVersion).filter(
        MaterialVersion.material_type == material_type,
        MaterialVersion.is_deleted == False
    )
    
    if customer_id:
        query = query.filter(MaterialVersion.customer_id == customer_id)
    if trademark_id:
        query = query.filter(MaterialVersion.trademark_id == trademark_id)
    
    latest = query.order_by(MaterialVersion.version.desc()).first()
    return latest.version + 1 if latest else 1


def create_material(db: Session, material_in: MaterialCreate) -> MaterialVersion:
    material = MaterialVersion(**material_in.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def update_material(db: Session, material_id: int, material_in: MaterialUpdate) -> MaterialVersion:
    material = get_material(db, material_id)
    
    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    return material


def delete_material(db: Session, material_id: int) -> None:
    material = get_material(db, material_id)
    material.is_deleted = True
    db.commit()


async def upload_file(
    db: Session,
    file: UploadFile,
    material_type: MaterialType,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None,
    description: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    replaced_reason: Optional[str] = None,
    handled_by: Optional[str] = None,
    correction_id: Optional[int] = None,
    correction_type_required: Optional[str] = None,
) -> Tuple[MaterialVersion, bool, Optional[int]]:
    try:
        file_path, file_size, file_hash = await save_upload_file(file, subdir=material_type.value)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    query = db.query(MaterialVersion).filter(
        MaterialVersion.material_type == material_type,
        MaterialVersion.is_deleted == False
    )
    if correction_id:
        query = query.filter(MaterialVersion.correction_id == correction_id)
    else:
        query = query.filter(MaterialVersion.correction_id.is_(None))
        if customer_id:
            query = query.filter(MaterialVersion.customer_id == customer_id)
        if trademark_id:
            query = query.filter(MaterialVersion.trademark_id == trademark_id)

    current_versions = query.filter(MaterialVersion.is_current == True).all()
    replaced_previous = len(current_versions) > 0
    previous_version_id: Optional[int] = None

    if replaced_previous:
        previous_version = current_versions[0]
        previous_version_id = previous_version.id
        previous_version.is_current = False
        previous_version.is_replaced = True
        previous_version.replaced_at = datetime.now()
        previous_version.replaced_reason = replaced_reason or "上传新版本替换"
        previous_version.handled_by = previous_version.handled_by or handled_by

    next_version = get_next_version(db, material_type, customer_id, trademark_id, correction_id)

    material_in = MaterialCreate(
        material_type=material_type.value,
        version=next_version,
        file_name=file.filename or "unknown",
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash,
        is_current=True,
        uploaded_by=uploaded_by,
        handled_by=handled_by,
        description=description,
        submitted_at=datetime.now(),
        replaced_by_version_id=None,
        correction_id=correction_id,
        correction_type_required=correction_type_required,
        customer_id=customer_id,
        trademark_id=trademark_id,
    )

    new_material = create_material(db, material_in)

    if replaced_previous and previous_version_id:
        previous = db.query(MaterialVersion).filter(MaterialVersion.id == previous_version_id).first()
        if previous:
            previous.replaced_by_version_id = new_material.id
            db.commit()

    return new_material, replaced_previous, previous_version_id


def get_next_version(
    db: Session,
    material_type: MaterialType,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None,
    correction_id: Optional[int] = None,
) -> int:
    query = db.query(MaterialVersion).filter(
        MaterialVersion.material_type == material_type,
        MaterialVersion.is_deleted == False
    )

    if correction_id:
        query = query.filter(MaterialVersion.correction_id == correction_id)
    else:
        query = query.filter(MaterialVersion.correction_id.is_(None))
        if customer_id:
            query = query.filter(MaterialVersion.customer_id == customer_id)
        if trademark_id:
            query = query.filter(MaterialVersion.trademark_id == trademark_id)

    latest = query.order_by(MaterialVersion.version.desc()).first()
    return latest.version + 1 if latest else 1


def list_versions_for_correction(
    db: Session,
    correction_id: int,
    material_type: Optional[MaterialType] = None,
) -> List[MaterialVersion]:
    query = db.query(MaterialVersion).filter(
        MaterialVersion.correction_id == correction_id,
        MaterialVersion.is_deleted == False
    )
    if material_type:
        query = query.filter(MaterialVersion.material_type == material_type)

    return query.order_by(
        MaterialVersion.material_type.asc(),
        MaterialVersion.version.desc()
    ).all()


def get_correction_material_summary(
    db: Session,
    correction_id: int,
) -> Dict[str, Any]:
    correction = db.query(Correction).filter(
        Correction.id == correction_id,
        Correction.is_deleted == False
    ).first()

    if not correction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"补正记录 ID {correction_id} 不存在"
        )

    required_types: List[str] = []
    if correction.required_materials:
        required_types = [t.strip() for t in correction.required_materials.split(",") if t.strip()]

    all_materials = list_versions_for_correction(db, correction_id)

    type_groups: Dict[str, List[MaterialVersion]] = {}
    for m in all_materials:
        mt_key = m.material_type.value
        if mt_key not in type_groups:
            type_groups[mt_key] = []
        type_groups[mt_key].append(m)

    current_versions: List[MaterialVersion] = []
    for mt_key, versions in type_groups.items():
        current = [v for v in versions if v.is_current]
        if current:
            current_versions.append(current[0])

    material_type_names = {
        MaterialType.CORRECTION_POWER_OF_ATTORNEY.value: "委托书",
        MaterialType.CORRECTION_SUBJECT_QUALIFICATION.value: "主体资格证明",
        MaterialType.CORRECTION_CATEGORY_DESCRIPTION.value: "类别说明",
        MaterialType.CORRECTION_CHINESE_TRANSLATION.value: "中文译名",
        MaterialType.CORRECTION_OTHER.value: "其他补正材料",
    }

    missing_types: List[str] = []
    for req in required_types:
        mapped = CORRECTION_TYPE_MATERIAL_MAP.get(req)
        if mapped:
            has_current = any(
                m for m in current_versions
                if m.material_type == mapped
            )
            if not has_current:
                missing_types.append(req)
        else:
            if req not in [m.material_type.value for m in current_versions]:
                missing_types.append(req)

    return {
        "correction_id": correction.id,
        "correction_number": correction.correction_number,
        "required_types": required_types,
        "required_materials": required_types,
        "uploaded_count": len(all_materials),
        "total_versions": len(all_materials),
        "current_versions": [
            {
                "id": m.id,
                "version": m.version,
                "file_name": m.file_name,
                "material_type": m.material_type.value,
                "material_type_name": material_type_names.get(m.material_type.value, m.material_type.value),
                "uploaded_by": m.uploaded_by,
                "handled_by": m.handled_by,
                "created_at": m.created_at,
                "submitted_at": m.submitted_at,
                "is_current": m.is_current,
                "is_replaced": m.is_replaced,
                "is_approved": m.is_approved,
                "replaced_reason": m.replaced_reason,
                "replaced_at": m.replaced_at,
                "correction_id": m.correction_id,
                "correction_type_required": m.correction_type_required,
            }
            for m in current_versions
        ],
        "all_versions": [
            {
                "id": m.id,
                "version": m.version,
                "file_name": m.file_name,
                "material_type": m.material_type.value,
                "material_type_name": material_type_names.get(m.material_type.value, m.material_type.value),
                "uploaded_by": m.uploaded_by,
                "handled_by": m.handled_by,
                "created_at": m.created_at,
                "submitted_at": m.submitted_at,
                "is_current": m.is_current,
                "is_replaced": m.is_replaced,
                "is_approved": m.is_approved,
                "replaced_reason": m.replaced_reason,
                "replaced_at": m.replaced_at,
                "correction_id": m.correction_id,
                "correction_type_required": m.correction_type_required,
            }
            for m in all_materials
        ],
        "missing_types": missing_types,
        "missing_materials": missing_types,
    }


def determine_correction_material_type(
    correction_type_required: Optional[str] = None,
) -> MaterialType:
    if correction_type_required:
        mapped = CORRECTION_TYPE_MATERIAL_MAP.get(correction_type_required)
        if mapped:
            return mapped
        for key, val in CORRECTION_TYPE_MATERIAL_MAP.items():
            if key.lower() in correction_type_required.lower():
                return val

    return MaterialType.CORRECTION_OTHER


async def upload_correction_material(
    db: Session,
    file: UploadFile,
    correction_id: int,
    correction_type_required: Optional[str] = None,
    replaced_reason: Optional[str] = None,
    handled_by: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    description: Optional[str] = None,
) -> Tuple[MaterialVersion, bool, Optional[int]]:
    correction = db.query(Correction).filter(
        Correction.id == correction_id,
        Correction.is_deleted == False
    ).first()

    if not correction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"补正记录 ID {correction_id} 不存在"
        )

    material_type = determine_correction_material_type(correction_type_required)

    trademark_id = correction.trademark_id

    from app.models.trademark import Trademark
    trademark = db.query(Trademark).filter(
        Trademark.id == trademark_id,
        Trademark.is_deleted == False
    ).first()
    customer_id = trademark.customer_id if trademark else None

    return await upload_file(
        db=db,
        file=file,
        material_type=material_type,
        customer_id=customer_id,
        trademark_id=trademark_id,
        description=description,
        uploaded_by=uploaded_by,
        replaced_reason=replaced_reason,
        handled_by=handled_by,
        correction_id=correction_id,
        correction_type_required=correction_type_required,
    )


def approve_material(
    db: Session,
    material_id: int,
    approved_by: Optional[str] = None,
    review_notes: Optional[str] = None,
) -> MaterialVersion:
    material = get_material(db, material_id)

    if material.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该材料已被删除，无法审核"
        )

    material.is_approved = True
    material.approved_at = datetime.now().isoformat()

    if approved_by:
        material.approved_by = approved_by

    if review_notes:
        material.approval_notes = review_notes
        material.review_notes = (material.review_notes or "") + f"\n审核备注: {review_notes}"

    db.commit()
    db.refresh(material)
    return material


def get_material_version_history(
    db: Session,
    material_id: int,
) -> List[MaterialVersion]:
    material = get_material(db, material_id)

    query = db.query(MaterialVersion).filter(
        MaterialVersion.is_deleted == False,
        MaterialVersion.material_type == material.material_type,
    )

    if material.correction_id:
        query = query.filter(MaterialVersion.correction_id == material.correction_id)
    else:
        query = query.filter(MaterialVersion.correction_id.is_(None))
        if material.customer_id:
            query = query.filter(MaterialVersion.customer_id == material.customer_id)
        if material.trademark_id:
            query = query.filter(MaterialVersion.trademark_id == material.trademark_id)

    return query.order_by(MaterialVersion.version.desc()).all()


def protect_historical_material(
    db: Session,
    material_id: int,
) -> MaterialVersion:
    material = get_material(db, material_id)

    if material.is_current and not material.is_replaced:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前版本材料无需保护，只有历史版本需要保护"
        )

    material.is_replaced = True

    notes_suffix = "\n[系统保护] 该历史版本已被保护，不可直接覆盖。"
    if material.description:
        material.description = material.description + notes_suffix
    else:
        material.description = notes_suffix.strip()

    db.commit()
    db.refresh(material)
    return material
