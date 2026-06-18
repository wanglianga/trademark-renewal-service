from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.models import MaterialVersion
from app.models.material_version import MaterialType
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
    uploaded_by: Optional[str] = None
) -> MaterialVersion:
    try:
        file_path, file_size, file_hash = await save_upload_file(file, subdir=material_type.value)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    query = db.query(MaterialVersion).filter(
        MaterialVersion.material_type == material_type,
        MaterialVersion.is_current == True,
        MaterialVersion.is_deleted == False
    )
    if customer_id:
        query = query.filter(MaterialVersion.customer_id == customer_id)
    if trademark_id:
        query = query.filter(MaterialVersion.trademark_id == trademark_id)
    query.update({MaterialVersion.is_current: False})
    
    next_version = get_next_version(db, material_type, customer_id, trademark_id)
    
    material_in = MaterialCreate(
        material_type=material_type.value,
        version=next_version,
        file_name=file.filename or "unknown",
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash,
        is_current=True,
        uploaded_by=uploaded_by,
        description=description,
        customer_id=customer_id,
        trademark_id=trademark_id
    )
    
    return create_material(db, material_in)
