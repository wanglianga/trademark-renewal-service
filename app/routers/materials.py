from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form
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
    PaginatedResponse
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    material = await material_service.upload_file(
        db,
        file=file,
        material_type=material_type,
        customer_id=customer_id,
        trademark_id=trademark_id,
        description=description,
        uploaded_by=uploaded_by
    )
    return MaterialUploadResponse(
        success=True,
        material_id=material.id,
        file_name=material.file_name,
        file_path=material.file_path,
        version=material.version,
        message="File uploaded successfully"
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
