from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import AgencyEntrustment
from app.schemas import AgencyCreate, AgencyUpdate


def get_agency_by_entrustment_number(db: Session, entrustment_number: str) -> Optional[AgencyEntrustment]:
    return db.query(AgencyEntrustment).filter(
        AgencyEntrustment.entrustment_number == entrustment_number,
        AgencyEntrustment.is_deleted == False
    ).first()


def list_agencies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[int] = None,
    trademark_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None
) -> Tuple[List[AgencyEntrustment], int]:
    query = db.query(AgencyEntrustment).filter(AgencyEntrustment.is_deleted == False)
    
    if customer_id:
        query = query.filter(AgencyEntrustment.customer_id == customer_id)
    if trademark_id:
        query = query.filter(AgencyEntrustment.trademark_id == trademark_id)
    if is_active is not None:
        query = query.filter(AgencyEntrustment.is_active == is_active)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (AgencyEntrustment.entrustment_number.ilike(search_pattern)) |
            (AgencyEntrustment.service_scope.ilike(search_pattern)) |
            (AgencyEntrustment.remarks.ilike(search_pattern))
        )
    
    total = query.count()
    agencies = query.order_by(AgencyEntrustment.id.desc()).offset(skip).limit(limit).all()
    return agencies, total


def get_agency(db: Session, agency_id: int) -> AgencyEntrustment:
    agency = db.query(AgencyEntrustment).filter(
        AgencyEntrustment.id == agency_id,
        AgencyEntrustment.is_deleted == False
    ).first()
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency entrustment not found"
        )
    return agency


def create_agency(db: Session, agency_in: AgencyCreate) -> AgencyEntrustment:
    existing_agency = get_agency_by_entrustment_number(db, agency_in.entrustment_number)
    if existing_agency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agency entrustment with this number already exists"
        )
    
    agency = AgencyEntrustment(**agency_in.model_dump())
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


def update_agency(db: Session, agency_id: int, agency_in: AgencyUpdate) -> AgencyEntrustment:
    agency = get_agency(db, agency_id)
    
    if agency_in.entrustment_number and agency_in.entrustment_number != agency.entrustment_number:
        existing_agency = get_agency_by_entrustment_number(db, agency_in.entrustment_number)
        if existing_agency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agency entrustment with this number already exists"
            )
    
    update_data = agency_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agency, field, value)
    
    db.commit()
    db.refresh(agency)
    return agency


def delete_agency(db: Session, agency_id: int) -> None:
    agency = get_agency(db, agency_id)
    agency.is_deleted = True
    db.commit()
