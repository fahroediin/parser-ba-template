from datetime import datetime
from typing import Optional, Any, List, Dict
from fastapi import HTTPException, Request
from response_schemas import (
    BaseResponse, ErrorResponse, ErrorDetail, PaginationInfo,
    ResponseMessage, ResponseStatus
)
import math

def create_success_response(
    message: str,
    data: Optional[Any] = None,
    success: bool = True
) -> BaseResponse:
    """Create a standard success response"""
    return BaseResponse(
        success=success,
        message=message,
        timestamp=datetime.utcnow().isoformat(),
        data=data
    )

def create_error_response(
    message: str,
    error_code: str,
    details: Optional[List[ErrorDetail]] = None,
    path: Optional[str] = None
) -> ErrorResponse:
    """Create a standard error response"""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details,
        path=path
    )

def create_pagination_info(
    page: int,
    limit: int,
    total: int
) -> PaginationInfo:
    """Create pagination metadata"""
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return PaginationInfo(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

def handle_http_exception(exc: HTTPException, request: Request = None) -> ErrorResponse:
    """Handle HTTP exceptions and return standardized error response"""
    path = str(request.url.path) if request else None

    error_details = []
    if hasattr(exc, 'detail') and isinstance(exc.detail, list):
        # Handle Pydantic validation errors
        for error in exc.detail:
            error_details.append(ErrorDetail(
                field=str(error.get('loc', [''])[0]) if error.get('loc') else None,
                message=error.get('msg', 'Validation error'),
                code=error.get('type', 'validation_error')
            ))
    else:
        # Handle simple string error messages
        error_details.append(ErrorDetail(
            message=str(exc.detail) if hasattr(exc, 'detail') else str(exc)
        ))

    return create_error_response(
        message=str(exc.detail) if hasattr(exc, 'detail') else "HTTP Error",
        error_code=f"HTTP_{exc.status_code}",
        details=error_details,
        path=path
    )

def handle_validation_error(
    field: str,
    message: str,
    code: str = "validation_error"
) -> ErrorDetail:
    """Create a validation error detail"""
    return ErrorDetail(
        field=field,
        message=message,
        code=code
    )

# Common response creators
def create_upload_response(
    batch_id: str,
    filename: str,
    status: str = ResponseStatus.PROCESSING
) -> BaseResponse:
    """Create standardized upload response"""
    return create_success_response(
        message=ResponseMessage.UPLOAD_PROCESSING,
        data={
            "batch_id": batch_id,
            "filename": filename,
            "status": status,
            "upload_timestamp": datetime.utcnow().isoformat()
        }
    )

def create_batch_response(
    batch_data: Dict[str, Any]
) -> BaseResponse:
    """Create standardized batch response"""
    return create_success_response(
        message=ResponseMessage.BATCH_FOUND,
        data=batch_data
    )

def create_batch_list_response(
    batches: List[Dict[str, Any]],
    page: int,
    limit: int,
    total: int
) -> BaseResponse:
    """Create standardized batch list response"""
    pagination = create_pagination_info(page, limit, total)

    return create_success_response(
        message=ResponseMessage.BATCH_LIST_RETRIEVED,
        data={
            "batches": batches,
            "pagination": pagination.dict()
        }
    )

def create_document_response(
    document_data: Dict[str, Any]
) -> BaseResponse:
    """Create standardized document response"""
    return create_success_response(
        message=ResponseMessage.DOCUMENT_FOUND,
        data=document_data
    )