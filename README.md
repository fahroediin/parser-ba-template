# 📊 Excel Parser API - Business Analysis Template

FastAPI-based system for parsing Excel business analysis documents with asynchronous processing and real-time status tracking.

## 🚀 Features

- **Excel Document Parsing**: Parse structured Excel files with multiple sheets (Product Overview, User Stories, Acceptance Criteria, Business Value)
- **Asynchronous Processing**: Non-blocking background processing for large files
- **Real-time Status Tracking**: Monitor upload and processing status via batch tracking
- **Structured Data Storage**: Store parsed data as JSON in relational database
- **Category Management**: Automatic category creation with slug generation
- **RESTful API**: Complete REST API with proper error handling
- **SQLite Database**: Lightweight, file-based database with multi-thread support

## 📋 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Upload API    │    │  Background     │    │   Database       │
│   /upload/...   │───▶│  Processing     │───▶│   (SQLite)       │
│                 │    │                 │    │                  │
│   - Validation  │    │ - Excel Parser  │    │ - Users          │
│   - File Read   │    │ - Data Cleaning │    │ - Import Batches │
│   - Queue Task  │    │ - JSON Struct   │    │ - Categories     │
└─────────────────┘    └─────────────────┘    │ - Documents      │
                                             └──────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI 0.100+
- **Database**: SQLAlchemy 2.0+ with SQLite
- **Data Processing**: Pandas 2.0+, openpyxl 3.1+
- **File Upload**: python-multipart
- **Validation**: Pydantic 2.0+
- **URL Generation**: python-slugify
- **Server**: Uvicorn

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### 1. Clone Repository
```bash
git clone <repository-url>
cd parser-ba-template
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📁 Excel Template Structure

The system expects Excel files with the following sheet structure:

### Sheet 1: **Product Overview** (Key-Value Format)
| Column A | Column B |
|----------|----------|
| Product Name | [Product Name] |
| Category | [Category] |
| Version | [Version] |
| Created Date | [Date] |
| ... | ... |

### Sheet 2: **User Story** (Tabular Format)
| ID | User Story | Priority | Status |
|----|------------|----------|--------|
| US001 | As a user... | High | Active |
| US002 | As an admin... | Medium | Pending |

### Sheet 3: **Acceptance Criteria** (Tabular Format)
| ID | Criteria | User Story ID | Status |
|----|----------|---------------|--------|
| AC001 | Given When Then | US001 | Active |
| AC002 | Another criteria | US001 | Active |

### Sheet 4: **Business Value** (Key-Value Format)
| Metric | Value |
|--------|-------|
| ROI | 150% |
| Time to Market | 6 months |
| ... | ... |

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### 1. Upload Excel Document

**Endpoint**: `POST /upload/product-document`

**Content-Type**: `multipart/form-data`

**Request**:
```bash
curl -X POST "http://localhost:8000/upload/product-document" \
  -F "file=@your-excel-file.xlsx" \
  -H "Content-Type: multipart/form-data"
```

**Response**:
```json
{
  "message": "File uploaded successfully, processing started.",
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING"
}
```

### 2. Check Batch Status

**Endpoint**: `GET /batches/{batch_id}`

**Request**:
```bash
curl -X GET "http://localhost:8000/batches/550e8400-e29b-41d4-a716-446655440000"
```

**Response** (Processing):
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "product-template.xlsx",
  "status": "PROCESSING",
  "total_rows": 0,
  "success_count": 0,
  "failed_count": 0,
  "error_log": null,
  "created_at": "2025-01-21T10:30:00",
  "documents": []
}
```

**Response** (Completed):
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "product-template.xlsx",
  "status": "COMPLETED",
  "total_rows": 25,
  "success_count": 1,
  "failed_count": 0,
  "error_log": null,
  "created_at": "2025-01-21T10:30:00",
  "documents": [
    {
      "id": "doc-123e4567-e89b-12d3-a456-426614174000",
      "title": "Amazing Product",
      "category_id": 1,
      "status": "ACTIVE",
      "created_at": "2025-01-21T10:30:05"
    }
  ]
}
```

### 3. List All Batches

**Endpoint**: `GET /batches`

**Query Parameters**:
- `limit` (int, optional): Number of batches to return (default: 10)
- `offset` (int, optional): Number of batches to skip (default: 0)
- `status` (string, optional): Filter by status (PROCESSING, COMPLETED, FAILED)

**Request**:
```bash
curl -X GET "http://localhost:8000/batches?limit=5&status=COMPLETED"
```

**Response**:
```json
{
  "batches": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "product1.xlsx",
      "status": "COMPLETED",
      "success_count": 1,
      "failed_count": 0,
      "created_at": "2025-01-21T10:30:00"
    }
  ],
  "total": 1
}
```

### 4. Get Document Details

**Endpoint**: `GET /documents/{doc_id}`

**Request**:
```bash
curl -X GET "http://localhost:8000/documents/doc-123e4567-e89b-12d3-a456-426614174000"
```

**Response**:
```json
{
  "id": "doc-123e4567-e89b-12d3-a456-426614174000",
  "title": "Amazing Product",
  "description": "Imported from product-template.xlsx",
  "category": {
    "id": 1,
    "name": "E-Commerce",
    "slug": "e-commerce"
  },
  "parsed_data": {
    "product_details": {
      "product_name": "Amazing Product",
      "category": "E-Commerce",
      "version": "1.0"
    },
    "business_values": {
      "roi": "150%",
      "time_to_market": "6 months"
    },
    "features": {
      "user_stories": [
        {
          "id": "US001",
          "user_story": "As a user, I want to search products",
          "priority": "High",
          "status": "Active"
        }
      ],
      "acceptance_criteria": [
        {
          "id": "AC001",
          "criteria": "Given I am on homepage When I search Then I see results",
          "user_story_id": "US001",
          "status": "Active"
        }
      ]
    },
    "parsing_stats": {
      "total_us": 5,
      "total_ac": 12
    }
  },
  "status": "ACTIVE",
  "created_at": "2025-01-21T10:30:05",
  "updated_at": "2025-01-21T10:30:05"
}
```

## 🔄 Complete Usage Flow

### Step 1: Upload File
```python
import requests

with open('product-template.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload/product-document',
        files={'file': f}
    )

batch_id = response.json()['batch_id']
print(f"Batch ID: {batch_id}")
```

### Step 2: Monitor Processing Status
```python
import time

def check_batch_status(batch_id):
    response = requests.get(f'http://localhost:8000/batches/{batch_id}')
    return response.json()

while True:
    status = check_batch_status(batch_id)
    print(f"Status: {status['status']}")

    if status['status'] == 'COMPLETED':
        doc_id = status['documents'][0]['id']
        print(f"Document ready! ID: {doc_id}")
        break
    elif status['status'] == 'FAILED':
        print(f"Processing failed: {status['error_log']}")
        break

    time.sleep(2)  # Check every 2 seconds
```

### Step 3: Get Parsed Document
```python
doc_response = requests.get(f'http://localhost:8000/documents/{doc_id}')
document = doc_response.json()

print(f"Product: {document['title']}")
print(f"Category: {document['category']['name']}")
print(f"User Stories: {len(document['parsed_data']['features']['user_stories'])}")
```

## 🏗️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'USER',
    created_at DATETIME
);
```

### Import Batches Table
```sql
CREATE TABLE import_batches (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    filename VARCHAR(255),
    total_rows INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    error_log JSON,
    status VARCHAR(20) DEFAULT 'PROCESSING',
    created_at DATETIME
);
```

### Categories Table
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100),
    created_at DATETIME
);
```

### Documents Table
```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    import_batch_id VARCHAR(36),
    category_id INTEGER,
    title VARCHAR(255),
    description TEXT,
    metadata JSON,  -- Stores parsed Excel data
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at DATETIME,
    updated_at DATETIME
);
```

## 🔧 Configuration

### Database Settings
The system uses SQLite by default. Database file: `parser_app.db`

To change to PostgreSQL:
```python
# In database.py
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/parser_db"
```

### Server Settings
```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🧪 Testing

### Upload Test with Sample File
```bash
# Create a test file or use an existing Excel template
curl -X POST "http://localhost:8000/upload/product-document" \
  -F "file=@test-data/sample-product.xlsx"
```

### API Testing with Python
```python
import requests
import json

# Test upload
with open('test.xlsx', 'rb') as f:
    response = requests.post('http://localhost:8000/upload/product-document', files={'file': f})
    print(json.dumps(response.json(), indent=2))

# Test batch status
batch_id = "your-batch-id"
response = requests.get(f'http://localhost:8000/batches/{batch_id}')
print(json.dumps(response.json(), indent=2))
```

## 🔍 Error Handling

### Common Error Responses

**Invalid File Format**:
```json
{
  "detail": "Invalid file format. Must be .xlsx"
}
```

**Missing File Field**:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**Batch Not Found**:
```json
{
  "detail": "Batch not found"
}
```

**Document Not Found**:
```json
{
  "detail": "Document not found"
}
```

### Error Logging
Processing errors are stored in the `error_log` field of the import batch:
```json
{
  "error_log": {
    "critical_error": "Sheet 'Product Overview' not found",
    "parsing_errors": [
      "Error parsing User Story: Invalid data format"
    ]
  }
}
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# .env file
DATABASE_URL=sqlite:///./parser_app.db
SECRET_KEY=your-secret-key
DEBUG=False
```

## 📈 Performance Considerations

- **Background Processing**: Large files are processed asynchronously to prevent timeout
- **Memory Efficiency**: Files are read into memory once and passed to background tasks
- **Database Optimization**: SQLite with multi-thread support for concurrent operations
- **Error Recovery**: Failed processing is logged without losing batch records

## 🔒 Security Notes

- **File Validation**: Only `.xlsx` files are accepted
- **Size Limits**: Consider implementing file size limits for production
- **Input Sanitization**: All Excel data is cleaned before storage
- **Database Security**: SQLAlchemy provides SQL injection protection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**1. "Field required" Error**
- Ensure you're sending `multipart/form-data` not `application/json`
- Include the `file` field in your form data

**2. Database Connection Errors**
- Check if SQLite file has proper permissions
- Ensure only one instance is running in development

**3. Processing Timeout**
- Large files may take longer to process
- Check batch status periodically using the batch tracking endpoint

**4. Missing Dependencies**
```bash
pip install -r requirements.txt
```

### Support

For issues and questions:
1. Check the error logs
2. Verify file format matches expected template
3. Test with smaller files first
4. Check batch status for detailed error information# parser-ba-template
