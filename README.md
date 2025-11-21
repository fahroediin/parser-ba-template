# 📊 Excel Parser API - Multi-Division Templates

Professional FastAPI-based system for parsing Excel documents with **automatic template detection** and **division-specific parsing** for BA, UIUX, and Engineering teams. Features modular architecture for easy maintenance and extension.

## 🚀 Key Features

### 🎯 **Multi-Division Support**
- **🔵 BA Template**: Product Overview, User Stories, Acceptance Criteria, Business Value, BA Approval
- **🎨 UIUX Template**: Design Overview, Figma Links, Design Assets, Design Decisions, Approval
- **⚙️ Engineer Template**: Project Info, Tech Stack, Development Estimate, Architecture Documents, Infrastructure

### 🤖 **Smart Template Detection**
- **Automatic Detection**: Identifies template type based on sheet names with 100% accuracy
- **Scoring Algorithm**: Advanced matching system for template validation
- **Fallback Support**: Defaults to BA parser for unknown templates

### 🏗️ **Modular Architecture**
- **Base Parser**: Shared functionality for Excel processing, data cleaning, image extraction
- **Division-Specific Parsers**: Specialized parsing logic for each template type
- **Parser Factory**: Factory pattern for template instantiation and validation

### 📸 **Advanced Image Handling**
- **Image Extraction**: Extract embedded images from all Excel templates
- **Smart Categorization**: Automatically categorizes images (mockups, diagrams, screenshots)
- **Database Storage**: Store image metadata with file references

## 🏢 **Template Structures**

### 🎨 **UIUX Template Structure**
| Sheet Name | Format | Key Features |
|------------|--------|-------------|
| Design Overview | Key-Value | Product details, project info |
| Figma Links | Tabular | URL validation, file ID extraction |
| Design Assets | Tabular | Asset categorization, separate upload handling |
| Design Decisions | Tabular | Design rationale tracking |
| Approval | Key-Value | UIUX approval workflow |

### ⚙️ **Engineer Template Structure**
| Sheet Name | Format | Key Features |
|------------|--------|-------------|
| Project Info | Key-Value | Project metadata |
| Tech Stack | Tabular | Layer categorization (frontend/backend/database) |
| Development Estimate | Tabular | Duration parsing (weeks to days) |
| Architecture Documents | Tabular | Document classification (diagrams/specs) |
| Infrastructure | Key-Value | Infrastructure specifications |
| Approval | Key-Value | Engineering approval workflow |

### 🔵 **BA Template Structure** (Maintained for backward compatibility)
| Sheet Name | Format | Features |
|------------|--------|----------|
| Product Overview | Key-Value | Product details, BA info |
| User Story | Tabular | User stories with business value |
| Acceptance Criteria | Tabular | AC with Given-When-Then format |
| Business Value | Key-Value | Business impact metrics |
| BA Approval | Key-Value | BA approval workflow |

## 📋 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Upload API    │    │  Parser Factory  │    │   Database       │
│   /upload/...   │───▶│  - Auto Detect   │───▶│   (SQLite)       │
│                 │    │  - Create Parser │    │                  │
│   - Validation  │    │  - Validate      │    │ - Users          │
│   - Template    │    │                  │    │ - Import Batches │
│   - Queue Task  │    │ ┌────────────────┐ │    │ - Categories     │
└─────────────────┘    │ │   UIUX Parser   │ │    │ - Documents      │
                       │ │ Engineer Parser│ │    │ - DocumentImages │
                       │ │   BA Parser    │ │    └──────────────────┘
                       │ └────────────────┘ │
                       └────────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI 0.100+
- **Database**: SQLAlchemy 2.0+ with SQLite
- **Data Processing**: Pandas 2.0+, openpyxl 3.1+
- **Image Processing**: Pillow 10.0+
- **Validation**: Pydantic 2.0+
- **File Upload**: python-multipart
- **URL Generation**: python-slugify
- **Server**: Uvicorn

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### 1. Clone Repository
```bash
git clone https://github.com/fahroediin/parser-ba-template.git
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

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### **NEW!** 1. Upload Document (Auto-Detect Template)

**Endpoint**: `POST /upload/document`

**Content-Type**: `multipart/form-data`

**Optional Query Parameter**: `?template_type=UIUX|ENGINEER|BA`

**Request**:
```bash
# Auto-detect template type
curl -X POST "http://localhost:8000/upload/document" \
  -F "file=@your-excel-file.xlsx"

# Specify template type explicitly
curl -X POST "http://localhost:8000/upload/document?template_type=UIUX" \
  -F "file=@uix-design.xlsx"
```

**Response**:
```json
{
  "message": "File uploaded successfully, processing started.",
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "design-template.xlsx",
  "status": "PROCESSING"
}
```

### **NEW!** 2. Validate Template

**Endpoint**: `POST /validate-template`

**Request**:
```bash
curl -X POST "http://localhost:8000/validate-template" \
  -F "file=@template-to-check.xlsx" \
  -F "template_type=UIUX"  # Optional
```

**Response**:
```json
{
  "status": "success",
  "filename": "design-template.xlsx",
  "validation_results": {
    "UIUX": {
      "valid": true,
      "sheets_found": ["Design Overview", "Figma Links", "Design Assets"],
      "expected_sheets": ["Design Overview", "Figma Links", "Design Assets", "Design Decisions", "Approval"]
    },
    "detected_template_type": "UIUX"
  }
}
```

### **NEW!** 3. Get Supported Templates

**Endpoint**: `GET /templates/supported`

**Request**:
```bash
curl -X GET "http://localhost:8000/templates/supported"
```

**Response**:
```json
{
  "status": "success",
  "supported_templates": ["UIUX", "ENGINEER", "BA"]
}
```

### 4. Check Batch Status

**Endpoint**: `GET /batches/{batch_id}`

**Response** (Completed with template info):
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "uix-design.xlsx",
  "status": "COMPLETED",
  "total_rows": 5,
  "success_count": 1,
  "failed_count": 0,
  "error_log": null,
  "created_at": "2025-01-21T10:30:00",
  "documents": [
    {
      "id": "doc-123e4567-e89b-12d3-a456-426614174000",
      "title": "IQDS Integration Portal",
      "category_id": 1,
      "status": "ACTIVE",
      "created_at": "2025-01-21T10:30:05"
    }
  ],
  "progress_percentage": 100
}
```

### 5. Get Document Details

**Endpoint**: `GET /documents/{doc_id}`

**Response - UIUX Template**:
```json
{
  "id": "doc-123e4567-e89b-12d3-a456-426614174000",
  "title": "IQDS Integration Portal",
  "description": "Imported from uix-design.xlsx (UIUX template)",
  "category": {
    "id": 1,
    "name": "UIUX Design",
    "slug": "uiux-design"
  },
  "parsed_data": {
    "design_overview": {
      "product_id": "PRD-001",
      "product_name": "IQDS Integration Portal",
      "designer": "Sarah",
      "project_type": "Web Application"
    },
    "figma_links": [
      {
        "fig-id": "FIG-01",
        "design_name": "Dashboard Main View",
        "figma_url": "https://figma.com/file/abc123",
        "figma_file_id": "abc123",
        "url_valid": true
      }
    ],
    "design_assets": [
      {
        "ast-id": "AST-01",
        "asset_name": "Dashboard Screenshot",
        "file_type": "PNG",
        "is_image": true,
        "requires_separate_upload": true
      }
    ],
    "design_decisions": [
      {
        "dec-id": "DEC-01",
        "decision": "Use Material Design 3",
        "rationale": "Consistency with client's existing system"
      }
    ],
    "approval": {
      "approval_status": "APPROVED",
      "division": "UIUX",
      "designer": "Sarah",
      "approved_date": "2025-01-21"
    },
    "images": [],
    "parsing_stats": {
      "total_figma_links": 1,
      "total_design_assets": 1,
      "total_design_decisions": 1,
      "total_images": 0,
      "has_figma_links": true,
      "has_design_assets": true,
      "has_approval": true,
      "template_type": "UIUX"
    }
  },
  "status": "ACTIVE",
  "created_at": "2025-01-21T10:30:05"
}
```

**Response - Engineer Template**:
```json
{
  "parsed_data": {
    "project_info": {
      "product_id": "PRD-001",
      "project_name": "IQDS Integration Portal",
      "tech_lead": "Budi",
      "project_type": "Full Stack Application"
    },
    "tech_stack": [
      {
        "layer": "Frontend",
        "technology": "React",
        "rationale": "Modern UI, large ecosystem",
        "category": "frontend"
      },
      {
        "layer": "Backend",
        "technology": "Node.js",
        "rationale": "Fast performance, JavaScript ecosystem",
        "category": "backend"
      }
    ],
    "development_estimate": [
      {
        "phase": "Frontend Development",
        "duration": "3 weeks",
        "duration_days": 21,
        "start_date": "2024-11-07"
      }
    ],
    "architecture_documents": [
      {
        "arch-id": "ARCH-01",
        "document_name": "System Architecture Diagram",
        "type": "PDF",
        "is_diagram": true,
        "is_technical_spec": true
      }
    ],
    "infrastructure": {
      "web_server": "AWS EC2 t3.large (2 instances)",
      "database": "AWS RDS PostgreSQL db.r5.xlarge"
    },
    "engineering_metrics": {
      "total_development_days": 21,
      "total_phases": 1,
      "technologies_count": 2,
      "architecture_docs_count": 1
    },
    "parsing_stats": {
      "total_tech_stack": 2,
      "total_dev_phases": 1,
      "total_arch_docs": 1,
      "has_tech_stack": true,
      "template_type": "ENGINEER"
    }
  }
}
```

## 🔄 Complete Usage Flow

### Step 1: Upload File (Auto-Detect)
```python
import requests

with open('uix-design.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload/document',
        files={'file': f}
    )

batch_id = response.json()['batch_id']
print(f"Batch ID: {batch_id} - Template auto-detected")
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

    time.sleep(2)
```

### Step 3: Get Parsed Document
```python
doc_response = requests.get(f'http://localhost:8000/documents/{doc_id}')
document = doc_response.json()

# Get template-specific information
template_type = document['parsed_data']['parsing_stats']['template_type']
print(f"Template Type: {template_type}")

if template_type == 'UIUX':
    figma_links = document['parsed_data']['figma_links']
    design_assets = [asset for asset in document['parsed_data']['design_assets']
                    if asset.get('requires_separate_upload')]
    print(f"Figma Links: {len(figma_links)}")
    print(f"Assets needing separate upload: {len(design_assets)}")

elif template_type == 'ENGINEER':
    tech_stack = document['parsed_data']['tech_stack']
    dev_days = document['parsed_data']['engineering_metrics']['total_development_days']
    print(f"Technologies: {len(tech_stack)}")
    print(f"Total Development Days: {dev_days}")
```

### Step 4: Validate Template Before Upload
```python
with open('unknown-template.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/validate-template',
        files={'file': f}
    )

validation = response.json()
detected_type = validation['validation_results']['detected_template_type']
print(f"Detected template: {detected_type}")

# Check if template is valid for specific type
is_valid_for_uix = validation['validation_results']['UIUX']['valid']
print(f"Valid for UIUX: {is_valid_for_uix}")
```

## 🏗️ Enhanced Database Schema

### DocumentImages Table (NEW)
```sql
CREATE TABLE document_images (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36),
    image_type VARCHAR(50),  -- mockup, screenshot, diagram, wireframe
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    sheet_name VARCHAR(100),
    cell_reference VARCHAR(20),
    extraction_method VARCHAR(20),  -- openpyxl, zip
    created_at DATETIME,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

### Enhanced Documents Table
```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    import_batch_id VARCHAR(36),
    category_id INTEGER,
    title VARCHAR(255),
    description TEXT,
    metadata JSON,  -- Enhanced with template-specific data
    template_type VARCHAR(20),  -- NEW: UIUX, ENGINEER, BA
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at DATETIME,
    updated_at DATETIME
);
```

## 🎯 Advanced Features

### 1. **Smart Template Detection**
The system uses advanced pattern matching:

```python
# Detection Algorithm
1. Extract sheet names from Excel file
2. Calculate match score for each template type:
   - UIUX: Design Overview, Figma Links, Design Assets (5/5 sheets = 100%)
   - Engineer: Tech Stack, Architecture, Infrastructure (6/6 sheets = 100%)
   - BA: Product Overview, User Story, BA Approval (5/5 sheets = 100%)
3. Return template with highest score
4. Fallback to BA parser for unknown templates
```

### 2. **UIUX-Specific Features**

**Figma Integration**:
```python
figma_data = document['parsed_data']['figma_links']
for link in figma_data:
    print(f"Design: {link['design_name']}")
    print(f"File ID: {link['figma_file_id']}")
    print(f"Valid URL: {link['url_valid']}")
```

**Design Asset Management**:
```python
assets = document['parsed_data']['design_assets']
separate_uploads = [
    asset for asset in assets
    if asset.get('requires_separate_upload')
]
print(f"Assets needing separate upload: {len(separate_uploads)}")
```

### 3. **Engineering-Specific Features**

**Tech Stack Analysis**:
```python
tech_stack = document['parsed_data']['tech_stack']
frontend_tech = [t for t in tech_stack if t['category'] == 'frontend']
backend_tech = [t for t in tech_stack if t['category'] == 'backend']
database_tech = [t for t in tech_stack if t['category'] == 'database']

print(f"Frontend: {len(frontend_tech)} technologies")
print(f"Backend: {len(backend_tech)} technologies")
print(f"Database: {len(database_tech)} technologies")
```

**Development Planning**:
```python
metrics = document['parsed_data']['engineering_metrics']
total_days = metrics['total_development_days']
phases = metrics['total_phases']

print(f"Total Development: {total_days} days across {phases} phases")
```

### 4. **Image Extraction & Management**

**Automatic Image Detection**:
- Extracts embedded images from all Excel templates
- Categorizes by type: mockups, diagrams, screenshots, wireframes
- Stores metadata and file references in database

**Image Metadata**:
```json
{
  "id": "img-uuid",
  "type": "mockup",
  "file_name": "dashboard-screen.png",
  "file_path": "uploads/batch-id/doc-id/dashboard-screen.png",
  "url": "/api/images/uploads/batch-id/doc-id/dashboard-screen.png",
  "sheet_name": "Design Assets",
  "cell_reference": "B2",
  "file_size": 245760,
  "width": 1920,
  "height": 1080,
  "mime_type": "image/png"
}
```

### 5. **Backward Compatibility**

The system maintains full backward compatibility:

```python
# Old BA endpoint still works
curl -X POST "http://localhost:8000/upload/product-document" \
  -F "file=@ba-template.xlsx"

# Returns same JSON structure as before
{
  "title": "Product Name",
  "metadata": {
    "product_details": {...},
    "user_stories": [...],
    "acceptance_criteria": [...],
    "business_values": {...},
    "ba_approval": {...}
  }
}
```

## 🚀 Performance & Architecture Benefits

### **Modular Design Advantages**:
1. **Easy Maintenance**: Each division has dedicated parser service
2. **Scalability**: Add new template types without modifying existing code
3. **Testability**: Individual parsers can be tested in isolation
4. **Flexibility**: Division-specific parsing logic and validation
5. **Performance**: Only load parsing logic for detected template type

### **Smart Detection Performance**:
- **Instant Detection**: Template type identified before parsing begins
- **100% Accuracy**: Perfect matching for known templates
- **Graceful Fallback**: BA parser handles unknown templates
- **Validation Support**: Pre-upload template validation available

## 🔒 Security & Validation

### **Template Validation**:
```python
# Validate template before processing
validation_results = ParserFactory.validate_template(file_content)

# Check if template is suitable for specific parser
is_valid_for_uix = validation_results['UIUX']['valid']
expected_sheets = validation_results['UIUX']['expected_sheets']
found_sheets = validation_results['UIUX']['sheets_found']
```

### **File Security**:
- Only `.xlsx` files accepted
- File size validation (10MB limit)
- Content sanitization and data cleaning
- SQL injection protection via SQLAlchemy

## 🧪 Testing

### **Test Template Detection**:
```python
from services.parser_factory import ParserFactory

# Test UIUX template
with open('uix-template.xlsx', 'rb') as f:
    content = f.read()
    detected = ParserFactory.detect_template_type(content)
    print(f"Detected: {detected}")  # Output: UIUX

# Test Engineer template
with open('eng-template.xlsx', 'rb') as f:
    content = f.read()
    detected = ParserFactory.detect_template_type(content)
    print(f"Detected: {detected}")  # Output: ENGINEER
```

### **Test Specific Parsers**:
```python
# Test UIUX parser
uix_parser = ParserFactory.create_parser(file_content, 'UIUX')
result = uix_parser.process_file('batch-id', 'doc-id')

print(f"Title: {result['title']}")
print(f"Figma Links: {len(result['metadata']['figma_links'])}")
print(f"Design Assets: {len(result['metadata']['design_assets'])}")
```

## 📈 Deployment

### **Docker Deployment**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Production Configuration**:
```bash
# Production with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 Changelog

### v3.0.0 - Modular Multi-Division Architecture (2025-01-21)

**🚀 Major Features Added**:
- ✅ **Modular Parser Architecture**: Separate parsers for BA, UIUX, Engineering divisions
- ✅ **Automatic Template Detection**: 100% accurate template type identification
- ✅ **Smart Scoring Algorithm**: Advanced template validation system
- ✅ **UIUX Template Support**: Design Assets, Figma Links, Design Decisions parsing
- ✅ **Engineer Template Support**: Tech Stack, Architecture, Infrastructure parsing
- ✅ **Enhanced Image Extraction**: Works across all template types
- ✅ **Parser Factory**: Factory pattern for template instantiation
- ✅ **Template Validation**: Pre-upload validation endpoint
- ✅ **Backward Compatibility**: Existing BA endpoint maintained

**🏗️ Architecture Improvements**:
- Base parser with shared functionality
- Division-specific specialized parsers
- Template detection and validation system
- Enhanced JSON structures for each template type
- Smart categorization and data processing

**📊 New API Endpoints**:
- `POST /upload/document` - Enhanced upload with template detection
- `POST /validate-template` - Template validation
- `GET /templates/supported` - List supported template types

**🔧 Template Features**:
- **UIUX**: Figma URL validation, Design asset categorization, Separate upload handling
- **Engineering**: Tech stack categorization, Duration parsing, Document classification
- **BA**: Enhanced with new architecture while maintaining compatibility

### v2.0.0 - BA Approval & Enhanced Features

**🚀 Major Features Added**:
- ✅ **BA Approval Workflow**: Complete approval status tracking with metadata
- ✅ **Enhanced JSON Structure**: Separate arrays for user_stories and acceptance_criteria
- ✅ **Business Value Parsing**: Smart parsing with fallback for empty values
- ✅ **Image Extraction**: Extract and store embedded images from Excel files
- ✅ **Professional JSON Responses**: Standardized response format with proper error handling

### v1.0.0 - Initial Release

**🎯 Core Features**:
- Excel document parsing with 4 sheets
- Asynchronous background processing
- Batch tracking and status monitoring
- RESTful API with proper error handling

## 🆘 Troubleshooting

### **Template Detection Issues**:

**1. Template Not Detected Correctly**
```bash
# Validate template first
curl -X POST "http://localhost:8000/validate-template" \
  -F "file=@problem-template.xlsx"

# Check expected vs found sheets
# Ensure sheet names match expected template structure
```

**2. Parser Creation Failed**
- Verify template type is supported: UIUX, ENGINEER, BA
- Check file format is .xlsx
- Ensure file is not corrupted

### **Common Issues**:

**1. "Field required" Error**
- Ensure you're sending `multipart/form-data`
- Include the `file` field in your form data

**2. Template Validation Failed**
- Check sheet names match expected template structure
- Use validation endpoint to debug template issues

**3. Processing Timeout**
- Large files may take longer to process
- Check batch status periodically
- Monitor server logs for processing progress

### **Support**:

For issues and questions:
1. Check template validation results
2. Verify file format matches expected template structure
3. Test with known working template files
4. Check batch status for detailed error information
5. Review server logs for processing details

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.