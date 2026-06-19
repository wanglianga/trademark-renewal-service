from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.base import Base

__all__ = ["engine", "SessionLocal", "get_db", "Base"]


def _create_engine_with_fallback():
    try:
        db_url = settings.ACTIVE_DATABASE_URL
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            engine = create_engine(
                db_url,
                connect_args=connect_args,
                echo=settings.APP_ENV == "development"
            )
        else:
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.APP_ENV == "development"
            )
        with engine.connect() as conn:
            pass
        return engine
    except Exception:
        print(f"Warning: Failed to connect to {settings.ACTIVE_DATABASE_URL}, falling back to SQLite")
        return create_engine(
            "sqlite:///./trademark_renewal.db",
            connect_args={"check_same_thread": False},
            echo=settings.APP_ENV == "development"
        )


engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
