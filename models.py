import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

# Import Base dari database.py
from database import Base 

# Helper agar default ID tetap generate UUID string
def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = 'users'
    
    # Menggunakan String untuk ID agar support SQLite
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default='USER')
    created_at = Column(DateTime, default=datetime.utcnow)

class ImportBatch(Base):
    __tablename__ = 'import_batches'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'))
    filename = Column(String(255))
    total_rows = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # Tipe JSON generik (Support SQLite & Postgres)
    error_log = Column(JSON, nullable=True)
    
    status = Column(String(20), default='PROCESSING') 
    created_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    import_batch_id = Column(String(36), ForeignKey('import_batches.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    title = Column(String(255))
    description = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    
    # Metadata disimpan sebagai JSON
    metadata_content = Column(JSON, name='metadata') 
    
    status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)