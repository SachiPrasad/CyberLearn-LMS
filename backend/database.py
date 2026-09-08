import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load .env from backend directory if present, as well as cwd
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "cyberlearn.db").replace("\\", "/")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# Normalize postgres:// to postgresql:// for SQLAlchemy 1.4+ / 2.0+
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args=connect_args
    )
    # Test connection if remote database
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            pass
except Exception as e:
    # Graceful fallback to local SQLite if PostgreSQL driver is missing or remote DB unreachable
    sqlite_url = f"sqlite:///{DEFAULT_SQLITE_PATH}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
