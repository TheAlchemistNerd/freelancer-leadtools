from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from .models import Base

# Default to SQLite for LeadTools (lightweight)
DATABASE_URL = settings.database_url or "sqlite:///./leadtools.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
