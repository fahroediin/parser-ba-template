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

    # Relationship to images
    images = relationship("DocumentImage", back_populates="document", cascade="all, delete-orphan")

class DocumentImage(Base):
    __tablename__ = 'document_images'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey('documents.id'), nullable=False)

    # Image metadata
    image_type = Column(String(50), nullable=False)  # mockup, screenshot, diagram, wireframe
    sheet_name = Column(String(255), nullable=True)   # Excel sheet where image was found
    cell_reference = Column(String(20), nullable=True) # Cell location (e.g., "B5")

    # File information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)    # Relative storage path
    file_size = Column(Integer, default=0)             # File size in bytes
    mime_type = Column(String(100), nullable=True)
    width = Column(Integer, nullable=True)              # Image dimensions
    height = Column(Integer, nullable=True)

    # Processing metadata
    extraction_method = Column(String(50), default="openpyxl")  # openpyxl, zip_extraction
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to document
    document = relationship("Document", back_populates="images")