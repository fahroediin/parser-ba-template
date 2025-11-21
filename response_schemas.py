from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    success: bool
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class PaginationInfo(BaseModel):
    """Pagination metadata"""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class UploadResponse(BaseModel):
    """Response for file upload"""
    batch_id: str
    status: str
    filename: str
    upload_timestamp: str

class DocumentInfo(BaseModel):
    """Document information model"""
    id: str
    title: str
    category_id: Optional[int] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None

class CategoryInfo(BaseModel):
    """Category information model"""
    id: int
    name: str
    slug: str

class BatchStatusResponse(BaseModel):
    """Batch status response model"""
    batch_id: str
    filename: str
    status: str
    total_rows: int
    success_count: int
    failed_count: int
    error_log: Optional[Dict[str, Any]] = None
    created_at: str
    documents: List[DocumentInfo]
    progress_percentage: Optional[int] = None

class BatchListItem(BaseModel):
    """Batch list item model"""
    id: str
    filename: str
    status: str
    success_count: int
    failed_count: int
    total_rows: int
    created_at: str
    progress_percentage: Optional[int] = None

class BatchListResponse(BaseModel):
    """Batch list response model"""
    batches: List[BatchListItem]
    pagination: PaginationInfo

class DocumentDetailResponse(BaseModel):
    """Document detail response model"""
    id: str
    title: str
    description: Optional[str] = None
    category: Optional[CategoryInfo] = None
    parsed_data: Dict[str, Any]
    status: str
    created_at: str
    updated_at: Optional[str] = None
    parsing_completeness: Optional[Dict[str, Any]] = None

class ErrorDetail(BaseModel):
    """Error detail model"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = False
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    error_code: str
    details: Optional[List[ErrorDetail]] = None
    path: Optional[str] = None

# Standard status codes and messages
class ResponseStatus:
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"

class ResponseMessage:
    # Upload messages
    UPLOAD_SUCCESS = "File uploaded successfully"
    UPLOAD_PROCESSING = "File uploaded successfully, processing started"

    # Batch messages
    BATCH_FOUND = "Batch retrieved successfully"
    BATCH_NOT_FOUND = "Batch not found"
    BATCH_LIST_RETRIEVED = "Batch list retrieved successfully"

    # Document messages
    DOCUMENT_FOUND = "Document retrieved successfully"
    DOCUMENT_NOT_FOUND = "Document not found"

    # Error messages
    VALIDATION_ERROR = "Validation error occurred"
    INTERNAL_ERROR = "Internal server error occurred"
    INVALID_FILE_FORMAT = "Invalid file format. Must be .xlsx"
    FILE_TOO_LARGE = "File size exceeds maximum allowed limit"