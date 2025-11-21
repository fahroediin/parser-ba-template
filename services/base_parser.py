import pandas as pd
import io
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from services.image_extractor import ImageExtractor
import uuid

class BaseParserService(ABC):
    """Base class for all Excel parsers with common functionality"""

    def __init__(self, file_content: bytes):
        self.excel_file = io.BytesIO(file_content)
        self.xls = pd.ExcelFile(self.excel_file)
        self.parsed_data = {}
        self.errors = []
        self.extracted_images = []

    def clean_value(self, val):
        """Clean NaN or empty values to dash (-) or None"""
        if pd.isna(val) or val == "" or str(val).lower() == "nan":
            return "-"
        if isinstance(val, datetime):
            return val.strftime('%Y-%m-%d')
        return str(val).strip()

    def parse_key_value_sheet(self, sheet_name: str, key_column: int = 0, value_column: int = 1,
                             skip_headers: List[str] = None) -> Dict[str, Any]:
        """Parse key-value vertical sheets (like Product Overview, Business Value)"""
        if skip_headers is None:
            skip_headers = ["field", "metric", "success metrics"]

        try:
            if sheet_name not in self.xls.sheet_names:
                return {}

            df = pd.read_excel(self.xls, sheet_name=sheet_name, header=None)
            result_data = {}

            for index, row in df.iterrows():
                key = row[key_column]
                val = row[value_column]

                # Skip header rows
                if (pd.notna(key) and
                    pd.notna(val) and
                    str(key).lower() not in skip_headers):

                    # Clean key for JSON
                    clean_key = str(key).lower().replace(" ", "_").replace(":", "").replace("/", "_").replace("(", "").replace(")", "")
                    result_data[clean_key] = self.clean_value(val)

            return result_data

        except Exception as e:
            self.errors.append(f"Error parsing {sheet_name}: {str(e)}")
            return {}

    def parse_tabular_sheet(self, sheet_name: str) -> List[Dict[str, Any]]:
        """Parse tabular horizontal sheets (like User Story, Acceptance Criteria)"""
        try:
            if sheet_name not in self.xls.sheet_names:
                return []

            # Load data, assuming row 1 (index 0) is header
            df = pd.read_excel(self.xls, sheet_name=sheet_name, header=0)
            records = []

            for _, row in df.iterrows():
                # Convert row to dictionary, clean NaN values
                clean_row = {k: self.clean_value(v) for k, v in row.items()}
                records.append(clean_row)

            return records

        except Exception as e:
            self.errors.append(f"Error parsing {sheet_name}: {str(e)}")
            return []

    def extract_images(self, batch_id: str = None, document_id: str = None) -> List[Dict[str, Any]]:
        """Extract images from Excel file"""
        if not batch_id or not document_id:
            return []

        try:
            image_extractor = ImageExtractor(self.excel_file.getvalue(), batch_id, document_id)
            self.extracted_images = image_extractor.extract_images_from_excel()
            print(f"Extracted {len(self.extracted_images)} images from Excel file")
            return self.extracted_images

        except Exception as e:
            print(f"Image extraction failed: {e}")
            self.errors.append(f"Image extraction error: {str(e)}")
            return []

    def generate_image_metadata(self) -> List[Dict[str, Any]]:
        """Generate standardized metadata for extracted images"""
        if not self.extracted_images:
            return []

        return [
            {
                'id': str(uuid.uuid4()),
                'type': img['image_type'],
                'file_name': img['file_name'],
                'file_path': img['file_path'],
                'url': f"/api/images/{img['file_path']}",
                'sheet_name': img['sheet_name'],
                'cell_reference': img['cell_reference'],
                'file_size': img['file_size'],
                'width': img['width'],
                'height': img['height'],
                'mime_type': img['mime_type']
            }
            for img in self.extracted_images
        ]

    @abstractmethod
    def get_template_type(self) -> str:
        """Return the template type (BA, UIUX, ENGINEER)"""
        pass

    @abstractmethod
    def process_file(self, batch_id: str = None, document_id: str = None) -> Dict[str, Any]:
        """Process the file and return parsed data"""
        pass

    @abstractmethod
    def get_template_sheets(self) -> List[str]:
        """Return list of expected sheet names for this template type"""
        pass

    def validate_template(self) -> bool:
        """Validate if this parser can handle the uploaded file"""
        expected_sheets = self.get_template_sheets()
        available_sheets = self.xls.sheet_names

        # Check if at least half of expected sheets are present
        matches = len([sheet for sheet in expected_sheets if sheet in available_sheets])
        return matches >= len(expected_sheets) * 0.5

    def get_template_priority(self) -> int:
        """Return priority for template detection (higher = more specific)"""
        return 1