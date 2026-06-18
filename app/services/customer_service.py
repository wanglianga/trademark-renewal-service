from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Customer
from app.schemas import CustomerCreate, CustomerUpdate


def list_customers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = None
) -> Tuple[List[Customer], int]:
    query = db.query(Customer).filter(Customer.is_deleted == False)
    
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (Customer.name.ilike(search_pattern)) |
            (Customer.unified_social_credit_code.ilike(search_pattern)) |
            (Customer.legal_representative.ilike(search_pattern))
        )
    
    total = query.count()
    customers = query.order_by(Customer.id.desc()).offset(skip).limit(limit).all()
    return customers, total


def get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.is_deleted == False
    ).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


def get_customer_by_credit_code(db: Session, credit_code: str) -> Optional[Customer]:
    return db.query(Customer).filter(
        Customer.unified_social_credit_code == credit_code,
        Customer.is_deleted == False
    ).first()


def create_customer(db: Session, customer_in: CustomerCreate) -> Customer:
    existing_customer = get_customer_by_credit_code(db, customer_in.unified_social_credit_code)
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this unified social credit code already exists"
        )
    
    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer_id: int, customer_in: CustomerUpdate) -> Customer:
    customer = get_customer(db, customer_id)
    
    if customer_in.unified_social_credit_code and customer_in.unified_social_credit_code != customer.unified_social_credit_code:
        existing_customer = get_customer_by_credit_code(db, customer_in.unified_social_credit_code)
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this unified social credit code already exists"
            )
    
    update_data = customer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> None:
    customer = get_customer(db, customer_id)
    customer.is_deleted = True
    db.commit()
