from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.models import User, UserRole
from app.schemas import UserCreate, Token, UserResponse
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)


def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(
        User.username == username,
        User.is_deleted == False
    ).first()


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(
        User.email == email,
        User.is_deleted == False
    ).first()


def register(db: Session, user_in: UserCreate) -> User:
    existing_user = get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = get_user_by_email(db, user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        role_enum = UserRole(user_in.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be one of: admin, agent, finance, client"
        )
    
    user_data = user_in.model_dump()
    password = user_data.pop("password")
    user_data["hashed_password"] = hash_password(password)
    user_data["role"] = role_enum
    
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, form_data: OAuth2PasswordRequestForm) -> Token:
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


def get_current_user(db: Session, token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
