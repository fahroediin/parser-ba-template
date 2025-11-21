import pandas as pd
import io
import json
from datetime import datetime

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
            # Kita skip header section seperti 'PRODUCT IDENTIFICATION' dengan mendeteksi kolom B kosong/nan
            for index, row in df.iterrows():
                key = row[0]
                val = row[1]
                
                if pd.notna(key) and pd.notna(val):
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
        """Parsing Sheet 4: Business Value (Mirip Overview tapi mungkin ada Section Header)"""
        return self.parse_product_overview() # Logicnya sama (Key-Value pair), pakai ulang fungsi di atas.

    def process_file(self):
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
        # Note: Jika sheet namanya beda, sesuaikan stringnya. Disini saya anggap 'Business Value'
        business_values = {}
        if 'Business Value' in self.xls.sheet_names:
             # Logic khusus jika Business Value formatnya Key-Value
             # Kita gunakan logic manual read_excel untuk sheet ini
             try:
                 df_bv = pd.read_excel(self.xls, sheet_name='Business Value', header=None)
                 for index, row in df_bv.iterrows():
                     key = row[0]
                     val = row[1]
                     if pd.notna(key) and pd.notna(val):
                         business_values[str(key).strip()] = self.clean_value(val)
             except Exception as e:
                 self.errors.append(f"Error parsing Business Value: {str(e)}")

        # Struktur JSON akhir untuk kolom 'metadata'
        full_json_metadata = {
            "product_details": overview,
            "business_values": business_values,
            "features": {
                "user_stories": user_stories,
                "acceptance_criteria": acceptance_criteria
            },
            "parsing_stats": {
                "total_us": len(user_stories),
                "total_ac": len(acceptance_criteria)
            }
        }

        return {
            "title": doc_title,
            "category_name": category_name,
            "metadata": full_json_metadata,
            "errors": self.errors
        }