import pandas as pd
import io
import json
from datetime import datetime
from services.image_extractor import ImageExtractor
import uuid

class ExcelParserService:
    def __init__(self, file_content: bytes):
        self.excel_file = io.BytesIO(file_content)
        self.xls = pd.ExcelFile(self.excel_file)
        self.parsed_data = {}
        self.errors = []

    def clean_value(self, val):
        """Membersihkan nilai NaN atau kosong menjadi dash (-) atau None"""
        if pd.isna(val) or val == "" or str(val).lower() == "nan":
            return "-"
        if isinstance(val, datetime):
            return val.strftime('%Y-%m-%d')
        return str(val).strip()

    def parse_product_overview(self):
        """Parsing Sheet 1: Product Overview (Key-Value Vertikal)"""
        try:
            df = pd.read_excel(self.xls, sheet_name='Product Overview', header=None)
            overview_data = {}

            # Loop setiap baris, cari Key di kolom A dan Value di kolom B
            # Skip header rows yang tidak memiliki data di kolom B
            for index, row in df.iterrows():
                key = row[0]
                val = row[1]

                # Skip row jika key adalah "field" atau "Field" (header row)
                if pd.notna(key) and pd.notna(val) and str(key).lower() != "field":
                    # Mapping nama field Excel ke key JSON yang rapi
                    clean_key = str(key).lower().replace(" ", "_").replace(":", "")
                    overview_data[clean_key] = self.clean_value(val)

            return overview_data
        except Exception as e:
            self.errors.append(f"Error parsing Product Overview: {str(e)}")
            return {}

    def parse_tabular_sheet(self, sheet_name):
        """Parsing Sheet 2 & 3: User Story & Acceptance Criteria (Tabel Horizontal)"""
        try:
            # Load data, anggap baris 1 (index 0) adalah header
            df = pd.read_excel(self.xls, sheet_name=sheet_name, header=0)
            records = []
            
            for _, row in df.iterrows():
                # Convert row ke dictionary, bersihkan NaN
                clean_row = {k: self.clean_value(v) for k, v in row.items()}
                records.append(clean_row)
            
            return records
        except Exception as e:
            self.errors.append(f"Error parsing {sheet_name}: {str(e)}")
            return []

    def parse_business_value(self):
        """Parsing Sheet 4: Business Value (Key-Value Vertikal)"""
        try:
            # Cek sheet Business Value ada
            if 'Business Value' not in self.xls.sheet_names:
                return {}

            df = pd.read_excel(self.xls, sheet_name='Business Value', header=None)
            business_values = {}

            # Loop setiap baris, cari Key di kolom A dan Value di kolom B
            for index, row in df.iterrows():
                key = row[0]
                val = row[1]

                # Skip row jika key adalah "field", "Metric", atau header rows
                if pd.notna(key) and str(key).lower() not in ["field", "metric", "success metrics"]:
                    # Jika value kosong, gunakan "Not specified" atau "-"
                    if pd.notna(val):
                        value = self.clean_value(val)
                    else:
                        value = "-"  # Default value untuk kosong

                    # Mapping nama field Excel ke key JSON yang rapi
                    clean_key = str(key).lower().replace(" ", "_").replace(":", "")
                    business_values[clean_key] = value

            return business_values
        except Exception as e:
            self.errors.append(f"Error parsing Business Value: {str(e)}")
            return {}

    def parse_ba_approval(self):
        """Parsing Sheet 5: BA Approval (Key-Value Vertikal)"""
        try:
            # Cek sheet BA Approval ada
            if 'BA Approval' not in self.xls.sheet_names:
                return {}

            df = pd.read_excel(self.xls, sheet_name='BA Approval', header=None)
            ba_approval = {}

            # Loop setiap baris, cari Key di kolom A dan Value di kolom B
            for index, row in df.iterrows():
                key = row[0]
                val = row[1]

                # Skip header rows
                if pd.notna(key) and pd.notna(val) and str(key).lower() != "field":
                    # Mapping nama field Excel ke key JSON yang rapi
                    clean_key = str(key).lower().replace(" ", "_").replace(":", "")
                    ba_approval[clean_key] = self.clean_value(val)

            return ba_approval
        except Exception as e:
            self.errors.append(f"Error parsing BA Approval: {str(e)}")
            return {}

    def process_file(self, batch_id: str = None, document_id: str = None):
        # 1. Parse Product Overview
        overview = self.parse_product_overview()

        # Ambil data kritikal untuk table 'documents'
        doc_title = overview.get('product_name', 'Untitled Product')
        category_name = overview.get('category', 'Uncategorized')

        # 2. Parse User Stories
        user_stories = self.parse_tabular_sheet('User Story')

        # 3. Parse Acceptance Criteria
        acceptance_criteria = self.parse_tabular_sheet('Acceptance Criteria')

        # 4. Parse Business Value
        business_values = self.parse_business_value()

        # 5. Parse BA Approval
        ba_approval = self.parse_ba_approval()

        # 6. Extract Images (New Feature!)
        extracted_images = []
        if batch_id and document_id:
            try:
                image_extractor = ImageExtractor(self.excel_file.getvalue(), batch_id, document_id)
                extracted_images = image_extractor.extract_images_from_excel()
                self.extracted_images = extracted_images
                print(f"Extracted {len(extracted_images)} images from Excel file")
            except Exception as e:
                print(f"Image extraction failed: {e}")
                self.errors.append(f"Image extraction error: {str(e)}")

        # Generate image metadata for JSON
        image_metadata = []
        if hasattr(self, 'extracted_images'):
            image_metadata = [
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

        # Struktur JSON akhir untuk kolom 'metadata'
        full_json_metadata = {
            "product_details": overview,
            "business_values": business_values,
            "ba_approval": ba_approval,
            "user_stories": user_stories,
            "acceptance_criteria": acceptance_criteria,
            "images": image_metadata,  # NEW: Image metadata
            "parsing_stats": {
                "total_us": len(user_stories),
                "total_ac": len(acceptance_criteria),
                "total_bv": len(business_values),
                "total_images": len(extracted_images),
                "has_ba_approval": len(ba_approval) > 0,
                "has_images": len(extracted_images) > 0
            }
        }

        return {
            "title": doc_title,
            "category_name": category_name,
            "metadata": full_json_metadata,
            "errors": self.errors,
            "extracted_images": extracted_images  # Return extracted images for DB storage
        }