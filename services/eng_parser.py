from services.base_parser import BaseParserService
from typing import Dict, Any, List
import pandas as pd

class EngineerParserService(BaseParserService):
    """Engineering template parser"""

    def get_template_type(self) -> str:
        return "ENGINEER"

    def get_template_sheets(self) -> List[str]:
        return [
            "Project Info",
            "Tech Stack",
            "Development Estimate",
            "Architecture Documents",
            "Infrastructure",
            "Approval"
        ]

    def get_template_priority(self) -> int:
        return 3  # High priority - very specific sheet names

    def parse_project_info(self) -> Dict[str, Any]:
        """Parse Project Info sheet (Key-Value Vertical)"""
        return self.parse_key_value_sheet("Project Info")

    def parse_tech_stack(self) -> List[Dict[str, Any]]:
        """Parse Tech Stack sheet (Tabular)"""
        try:
            if "Tech Stack" not in self.xls.sheet_names:
                return []

            df = pd.read_excel(self.xls, sheet_name="Tech Stack", header=0)
            records = []

            for _, row in df.iterrows():
                clean_row = {k: self.clean_value(v) for k, v in row.items()}

                # Categorize technologies by layer
                if 'layer' in clean_row:
                    layer = clean_row['layer'].lower()
                    clean_row['category'] = self._categorize_tech_layer(layer)

                records.append(clean_row)

            return records

        except Exception as e:
            self.errors.append(f"Error parsing Tech Stack: {str(e)}")
            return []

    def parse_development_estimate(self) -> List[Dict[str, Any]]:
        """Parse Development Estimate sheet (Tabular)"""
        try:
            if "Development Estimate" not in self.xls.sheet_names:
                return []

            df = pd.read_excel(self.xls, sheet_name="Development Estimate", header=0)
            records = []

            for _, row in df.iterrows():
                clean_row = {k: self.clean_value(v) for k, v in row.items()}

                # Parse duration and calculate total days
                if 'duration' in clean_row:
                    duration_str = clean_row['duration']
                    clean_row['duration_days'] = self._parse_duration_to_days(duration_str)

                # Parse dates
                for date_field in ['start_date', 'end_date']:
                    if date_field in clean_row:
                        date_val = clean_row[date_field]
                        if date_val and date_val != "-":
                            clean_row[f'{date_field}_parsed'] = str(date_val)  # Already formatted by clean_value

                records.append(clean_row)

            return records

        except Exception as e:
            self.errors.append(f"Error parsing Development Estimate: {str(e)}")
            return []

    def parse_architecture_documents(self) -> List[Dict[str, Any]]:
        """Parse Architecture Documents sheet (Tabular)"""
        try:
            if "Architecture Documents" not in self.xls.sheet_names:
                return []

            df = pd.read_excel(self.xls, sheet_name="Architecture Documents", header=0)
            records = []

            for _, row in df.iterrows():
                clean_row = {k: self.clean_value(v) for k, v in row.items()}

                # Categorize document types
                if 'type' in clean_row:
                    doc_type = clean_row['type'].upper()
                    clean_row['is_diagram'] = doc_type in ['PNG', 'JPG', 'JPEG', 'SVG', 'PDF']
                    clean_row['is_document'] = doc_type in ['PDF', 'DOC', 'DOCX', 'TXT']
                    clean_row['is_technical_spec'] = any(
                        keyword in clean_row.get('document_name', '').lower()
                        for keyword in ['architecture', 'schema', 'api', 'technical', 'specification']
                    )

                records.append(clean_row)

            return records

        except Exception as e:
            self.errors.append(f"Error parsing Architecture Documents: {str(e)}")
            return []

    def parse_infrastructure(self) -> Dict[str, Any]:
        """Parse Infrastructure sheet (Key-Value Vertical)"""
        return self.parse_key_value_sheet("Infrastructure")

    def parse_approval(self) -> Dict[str, Any]:
        """Parse Approval sheet (Key-Value Vertical)"""
        approval_data = self.parse_key_value_sheet("Approval")

        # Extract approval status specifically
        if approval_data:
            status = approval_data.get('status', 'PENDING').upper()
            approval_data['approval_status'] = status
            approval_data['division'] = 'ENGINEERING'

        return approval_data

    def _categorize_tech_layer(self, layer: str) -> str:
        """Categorize technology layer"""
        layer_lower = layer.lower()
        if 'frontend' in layer_lower or 'ui' in layer_lower:
            return 'frontend'
        elif 'backend' in layer_lower or 'api' in layer_lower:
            return 'backend'
        elif 'database' in layer_lower or 'data' in layer_lower:
            return 'database'
        elif 'infrastructure' in layer_lower or 'devops' in layer_lower:
            return 'infrastructure'
        elif 'testing' in layer_lower or 'qa' in layer_lower:
            return 'testing'
        else:
            return 'other'

    def _parse_duration_to_days(self, duration_str: str) -> int:
        """Parse duration string to days (e.g., '3 weeks' -> 21, '2 days' -> 2)"""
        try:
            duration_str = str(duration_str).lower()
            if 'week' in duration_str:
                # Extract number before 'week'
                import re
                match = re.search(r'(\d+)', duration_str)
                if match:
                    weeks = int(match.group(1))
                    return weeks * 7
            elif 'day' in duration_str:
                import re
                match = re.search(r'(\d+)', duration_str)
                if match:
                    return int(match.group(1))
            elif 'month' in duration_str:
                import re
                match = re.search(r'(\d+)', duration_str)
                if match:
                    months = int(match.group(1))
                    return months * 30  # Approximate
        except:
            pass
        return 0

    def process_file(self, batch_id: str = None, document_id: str = None) -> Dict[str, Any]:
        """Process Engineer template file"""
        # Parse all Engineering sections
        project_info = self.parse_project_info()
        tech_stack = self.parse_tech_stack()
        dev_estimate = self.parse_development_estimate()
        arch_documents = self.parse_architecture_documents()
        infrastructure = self.parse_infrastructure()
        approval = self.parse_approval()

        # Extract images if batch_id and document_id are provided
        extracted_images = self.extract_images(batch_id, document_id)

        # Get critical data for documents table
        doc_title = project_info.get('project_name', project_info.get('product_name', 'Untitled Engineering Project'))
        category_name = "Engineering"  # Default category for Engineering projects

        # Generate image metadata for JSON
        image_metadata = self.generate_image_metadata()

        # Calculate total development time
        total_dev_days = sum(item.get('duration_days', 0) for item in dev_estimate)

        # Extract approval status
        approval_status = approval.get('approval_status', 'PENDING')

        # Structure final JSON for metadata column
        full_json_metadata = {
            "project_info": project_info,
            "tech_stack": tech_stack,
            "development_estimate": dev_estimate,
            "architecture_documents": arch_documents,
            "infrastructure": infrastructure,
            "approval": approval,
            "images": image_metadata,
            "approval_status": approval_status,
            "engineering_metrics": {
                "total_development_days": total_dev_days,
                "total_phases": len(dev_estimate),
                "technologies_count": len(tech_stack),
                "architecture_docs_count": len(arch_documents)
            },
            "parsing_stats": {
                "total_tech_stack": len(tech_stack),
                "total_dev_phases": len(dev_estimate),
                "total_arch_docs": len(arch_documents),
                "total_images": len(extracted_images),
                "total_dev_days": total_dev_days,
                "has_tech_stack": len(tech_stack) > 0,
                "has_dev_estimate": len(dev_estimate) > 0,
                "has_architecture_docs": len(arch_documents) > 0,
                "has_infrastructure": len(infrastructure) > 0,
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
                "architecture_diagrams": len(arch_documents) > 0,
                "technical_specifications": len(tech_stack) > 0
            }
        }