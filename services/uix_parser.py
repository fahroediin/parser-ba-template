from services.base_parser import BaseParserService
from typing import Dict, Any, List

class UIUXParserService(BaseParserService):
    """UI/UX Design template parser"""

    def get_template_type(self) -> str:
        return "UIUX"

    def get_template_sheets(self) -> List[str]:
        return [
            "Design Overview",
            "Figma Links",
            "Design Assets",
            "Design Decisions",
            "Approval"
        ]

    def get_template_priority(self) -> int:
        return 3  # High priority - very specific sheet names

    def parse_design_overview(self) -> Dict[str, Any]:
        """Parse Design Overview sheet (Key-Value Vertical)"""
        return self.parse_key_value_sheet("Design Overview")

    def parse_figma_links(self) -> List[Dict[str, Any]]:
        """Parse Figma Links sheet (Tabular)"""
        try:
            if "Figma Links" not in self.xls.sheet_names:
                return []

            df = pd.read_excel(self.xls, sheet_name="Figma Links", header=0)
            records = []

            for _, row in df.iterrows():
                clean_row = {k: self.clean_value(v) for k, v in row.items()}

                # Validate Figma URL format
                if 'figma_url' in clean_row:
                    url = clean_row['figma_url']
                    if url and url != "-" and 'figma.com' in url.lower():
                        # Extract figma file ID if possible
                        file_id = self._extract_figma_file_id(url)
                        clean_row['figma_file_id'] = file_id
                        clean_row['url_valid'] = True
                    else:
                        clean_row['url_valid'] = False

                records.append(clean_row)

            return records

        except Exception as e:
            self.errors.append(f"Error parsing Figma Links: {str(e)}")
            return []

    def parse_design_assets(self) -> List[Dict[str, Any]]:
        """Parse Design Assets sheet - focus on image file references"""
        try:
            if "Design Assets" not in self.xls.sheet_names:
                return []

            df = pd.read_excel(self.xls, sheet_name="Design Assets", header=0)
            records = []

            for _, row in df.iterrows():
                clean_row = {k: self.clean_value(v) for k, v in row.items()}

                # Identify file types and processing requirements
                if 'file_type' in clean_row:
                    file_type = clean_row['file_type'].upper()
                    clean_row['is_image'] = file_type in ['PNG', 'JPG', 'JPEG', 'GIF', 'SVG']
                    clean_row['is_design_file'] = file_type in ['FIG', 'SKETCH', 'PSD', 'AI']

                # Mark assets for separate processing as requested
                if 'asset_name' in clean_row:
                    asset_name = clean_row['asset_name']
                    clean_row['requires_separate_upload'] = any(
                        keyword in asset_name.lower()
                        for keyword in ['screenshot', 'mockup', 'prototype', 'design', 'wireframe']
                    )

                records.append(clean_row)

            return records

        except Exception as e:
            self.errors.append(f"Error parsing Design Assets: {str(e)}")
            return []

    def parse_design_decisions(self) -> List[Dict[str, Any]]:
        """Parse Design Decisions sheet (Tabular)"""
        return self.parse_tabular_sheet("Design Decisions")

    def parse_approval(self) -> Dict[str, Any]:
        """Parse Approval sheet (Key-Value Vertical)"""
        approval_data = self.parse_key_value_sheet("Approval")

        # Extract approval status specifically
        if approval_data:
            status = approval_data.get('status', 'PENDING').upper()
            approval_data['approval_status'] = status
            approval_data['division'] = 'UIUX'

        return approval_data

    def _extract_figma_file_id(self, url: str) -> str:
        """Extract Figma file ID from URL"""
        try:
            # Example: https://figma.com/file/abc123/Design-Name
            # We want to extract 'abc123'
            if '/file/' in url:
                parts = url.split('/file/')
                if len(parts) > 1:
                    file_part = parts[1].split('/')[0]
                    return file_part
        except:
            pass
        return ""

    def process_file(self, batch_id: str = None, document_id: str = None) -> Dict[str, Any]:
        """Process UIUX template file"""
        # Parse all UIUX sections
        design_overview = self.parse_design_overview()
        figma_links = self.parse_figma_links()
        design_assets = self.parse_design_assets()
        design_decisions = self.parse_design_decisions()
        approval = self.parse_approval()

        # Extract images if batch_id and document_id are provided
        extracted_images = self.extract_images(batch_id, document_id)

        # Get critical data for documents table
        doc_title = design_overview.get('product_name', design_overview.get('project_name', 'Untitled UIUX Project'))
        category_name = "UIUX Design"  # Default category for UIUX projects

        # Generate image metadata for JSON
        image_metadata = self.generate_image_metadata()

        # Process design assets for separate upload requirement
        assets_requiring_upload = [
            asset for asset in design_assets
            if asset.get('requires_separate_upload', False)
        ]

        # Extract approval status
        approval_status = approval.get('approval_status', 'PENDING')

        # Structure final JSON for metadata column
        full_json_metadata = {
            "design_overview": design_overview,
            "figma_links": figma_links,
            "design_assets": design_assets,
            "design_decisions": design_decisions,
            "approval": approval,
            "images": image_metadata,
            "assets_requiring_separate_upload": assets_requiring_upload,
            "approval_status": approval_status,
            "parsing_stats": {
                "total_figma_links": len(figma_links),
                "total_design_assets": len(design_assets),
                "total_design_decisions": len(design_decisions),
                "total_images": len(extracted_images),
                "assets_needing_upload": len(assets_requiring_upload),
                "has_figma_links": len(figma_links) > 0,
                "has_design_assets": len(design_assets) > 0,
                "has_approval": len(approval) > 0,
                "has_images": len(extracted_images) > 0,
                "template_type": self.get_template_type()
            }
        }

        return {
            "title": doc_title,
            "category_name": category_name,
            "template_type": self.get_template_type(),
            "metadata": full_json_metadata,
            "errors": self.errors,
            "extracted_images": extracted_images,
            "special_requirements": {
                "separate_asset_upload": len(assets_requiring_upload) > 0,
                "figma_integration": len(figma_links) > 0
            }
        }

# Import pandas for the parse_figma_links method
import pandas as pd