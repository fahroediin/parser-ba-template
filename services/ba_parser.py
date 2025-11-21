from services.base_parser import BaseParserService
from typing import Dict, Any, List

class BAParserService(BaseParserService):
    """Business Analysis template parser - maintains existing functionality"""

    def get_template_type(self) -> str:
        return "BA"

    def get_template_sheets(self) -> List[str]:
        return [
            "Product Overview",
            "User Story",
            "Acceptance Criteria",
            "Business Value",
            "BA Approval"
        ]

    def get_template_priority(self) -> int:
        return 1  # Lowest priority - fallback parser

    def parse_product_overview(self) -> Dict[str, Any]:
        """Parse Product Overview sheet (Key-Value Vertical)"""
        return self.parse_key_value_sheet("Product Overview")

    def parse_user_stories(self) -> List[Dict[str, Any]]:
        """Parse User Story sheet (Tabular Horizontal)"""
        return self.parse_tabular_sheet("User Story")

    def parse_acceptance_criteria(self) -> List[Dict[str, Any]]:
        """Parse Acceptance Criteria sheet (Tabular Horizontal)"""
        return self.parse_tabular_sheet("Acceptance Criteria")

    def parse_business_value(self) -> Dict[str, Any]:
        """Parse Business Value sheet (Key-Value Vertical)"""
        return self.parse_key_value_sheet(
            "Business Value",
            skip_headers=["field", "metric", "success metrics"]
        )

    def parse_ba_approval(self) -> Dict[str, Any]:
        """Parse BA Approval sheet (Key-Value Vertical)"""
        return self.parse_key_value_sheet("BA Approval")

    def process_file(self, batch_id: str = None, document_id: str = None) -> Dict[str, Any]:
        """Process BA template file"""
        # Parse all BA sections
        overview = self.parse_product_overview()
        user_stories = self.parse_user_stories()
        acceptance_criteria = self.parse_acceptance_criteria()
        business_values = self.parse_business_value()
        ba_approval = self.parse_ba_approval()

        # Extract images if batch_id and document_id are provided
        extracted_images = self.extract_images(batch_id, document_id)

        # Get critical data for documents table
        doc_title = overview.get('product_name', 'Untitled Product')
        category_name = overview.get('category', 'Uncategorized')

        # Generate image metadata for JSON
        image_metadata = self.generate_image_metadata()

        # Extract approval status from BA Approval
        approval_status = "PENDING"
        if ba_approval:
            status_field = ba_approval.get('status', '').upper()
            if status_field in ['APPROVED', 'REJECTED', 'PENDING']:
                approval_status = status_field

        # Structure final JSON for metadata column
        full_json_metadata = {
            "product_details": overview,
            "business_values": business_values,
            "ba_approval": ba_approval,
            "user_stories": user_stories,
            "acceptance_criteria": acceptance_criteria,
            "images": image_metadata,
            "approval_status": approval_status,
            "parsing_stats": {
                "total_us": len(user_stories),
                "total_ac": len(acceptance_criteria),
                "total_bv": len(business_values),
                "total_images": len(extracted_images),
                "has_ba_approval": len(ba_approval) > 0,
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
            "extracted_images": extracted_images
        }