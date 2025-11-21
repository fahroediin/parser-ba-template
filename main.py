from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from database import get_db, engine # Anggap setup DB standar
import models
import shutil
from services.excel_parser import ExcelParserService
from slugify import slugify

# Init DB Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Excel Parser System")

async def process_upload_background(batch_id: str, file_content: bytes, db: Session):
    """Background task untuk parsing dan insert DB"""
    
    # Ambil record batch
    batch = db.query(models.ImportBatch).filter(models.ImportBatch.id == batch_id).first()
    
    try:
        # Parsing Excel
        parser = ExcelParserService(file_content)
        result = parser.process_file()
        
        if result['errors']:
            batch.error_log = result['errors']
            # Kita tidak langsung fail kalau ada error parsial, tapi dicatat
        
        # 1. Handle Category (Cari atau Buat)
        cat_name = result['category_name']
        category = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not category:
            category = models.Category(name=cat_name, slug=slugify(cat_name))
            db.add(category)
            db.flush() # Dapatkan ID
            
        # 2. Insert Document
        new_doc = models.Document(
            import_batch_id=batch.id,
            category_id=category.id,
            title=result['title'],
            description=f"Imported from {batch.filename}",
            metadata_content=result['metadata'], # DATA JSON DISIMPAN DISINI
            status='ACTIVE'
        )
        db.add(new_doc)
        
        # 3. Update Batch Status
        batch.status = 'COMPLETED'
        batch.success_count = 1 # Asumsi 1 file = 1 dokumen sukses
        batch.total_rows = result['metadata']['parsing_stats']['total_us'] # Contoh metric
        
        db.commit()
        print(f"Batch {batch_id} completed successfully.")

    except Exception as e:
        db.rollback()
        batch.status = 'FAILED'
        batch.error_log = {"critical_error": str(e)}
        batch.failed_count = 1
        db.commit()
        print(f"Batch {batch_id} failed: {e}")

@app.post("/upload/product-document")
async def upload_document(
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    # Validasi Ekstensi
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Invalid file format. Must be .xlsx")

    # Baca file ke memory (untuk diteruskan ke background task)
    content = await file.read()
    
    # Mock User ID (Di real app ambil dari JWT Token)
    # Pastikan ada user di DB dulu
    mock_user = db.query(models.User).first()
    if not mock_user:
        # Create dummy user for testing
        mock_user = models.User(email="admin@company.com", password_hash="xxx", full_name="Admin")
        db.add(mock_user)
        db.commit()
        
    # 1. Create Import Batch Record (Status: PROCESSING)
    new_batch = models.ImportBatch(
        user_id=mock_user.id,
        filename=file.filename,
        status='PROCESSING'
    )
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    
    # 2. Trigger Background Processing
    background_tasks.add_task(process_upload_background, new_batch.id, content, db)
    
    return {
        "message": "File uploaded successfully, processing started.",
        "batch_id": str(new_batch.id),
        "status": "PROCESSING"
    }

@app.get("/batches/{batch_id}")
def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    """Get batch processing status and related documents"""
    batch = db.query(models.ImportBatch).filter(models.ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, "Batch not found")

    # Get related documents if batch is completed
    documents = []
    if batch.status == 'COMPLETED':
        docs = db.query(models.Document).filter(models.Document.import_batch_id == batch_id).all()
        for doc in docs:
            documents.append({
                "id": doc.id,
                "title": doc.title,
                "category_id": doc.category_id,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })

    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "status": batch.status,
        "total_rows": batch.total_rows,
        "success_count": batch.success_count,
        "failed_count": batch.failed_count,
        "error_log": batch.error_log,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "documents": documents  # List of document IDs if completed
    }

@app.get("/batches")
def list_batches(
    limit: int = 10,
    offset: int = 0,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all batches with optional filtering"""
    query = db.query(models.ImportBatch)

    if status:
        query = query.filter(models.ImportBatch.status == status.upper())

    batches = query.order_by(models.ImportBatch.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "batches": [
            {
                "id": batch.id,
                "filename": batch.filename,
                "status": batch.status,
                "success_count": batch.success_count,
                "failed_count": batch.failed_count,
                "created_at": batch.created_at.isoformat() if batch.created_at else None
            }
            for batch in batches
        ],
        "total": len(batches)
    }

@app.get("/documents/{doc_id}")
def get_document_detail(doc_id: str, db: Session = Depends(get_db)):
    """Contoh cara mengambil data JSON yang sudah diparsing"""
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    # Get category info
    category = db.query(models.Category).filter(models.Category.id == doc.category_id).first()

    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "category": {
            "id": category.id,
            "name": category.name,
            "slug": category.slug
        } if category else None,
        "parsed_data": doc.metadata_content,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    }