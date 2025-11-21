from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- KONFIGURASI SQLITE ---
# File database akan otomatis dibuat di folder project dengan nama 'parser_app.db'
SQLALCHEMY_DATABASE_URL = "sqlite:///./parser_app.db"

# connect_args={"check_same_thread": False} KHUSUS untuk SQLite di FastAPI
# agar bisa diakses oleh multiple thread (background tasks)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()