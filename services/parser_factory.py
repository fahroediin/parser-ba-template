from services.ba_parser import BAParserService
from services.uix_parser import UIUXParserService
from services.eng_parser import EngineerParserService
from typing import List, Optional, Type
import pandas as pd

class ParserFactory:
    """Factory for creating appropriate parser based on template detection"""

    # Registry of available parsers
    _parsers = [
        UIUXParserService,
        EngineerParserService,
        BAParserService  # Keep BA as fallback
    ]

    @classmethod
    def detect_template_type(cls, file_content: bytes) -> str:
        """
        Automatically detect template type based on sheet names and content
        Returns: 'UIUX', 'ENGINEER', or 'BA'
        """
        try:
            # Load Excel to inspect sheet names
            excel_file = pd.ExcelFile(pd.io.common.BytesIO(file_content))
            sheet_names = excel_file.sheet_names

            print(f"Available sheets: {sheet_names}")

            # Score each parser based on sheet name matches
            parser_scores = []

            for parser_class in cls._parsers:
                # Create temporary instance for evaluation
                temp_parser = parser_class(file_content)
                expected_sheets = temp_parser.get_template_sheets()
                priority = temp_parser.get_template_priority()

                # Count matching sheets
                matches = len([sheet for sheet in expected_sheets if sheet in sheet_names])

                # Calculate score: (matches * priority) / total_expected
                if len(expected_sheets) > 0:
                    score = (matches * priority) / len(expected_sheets)
                else:
                    score = 0

                parser_scores.append({
                    'parser_class': parser_class,
                    'template_type': temp_parser.get_template_type(),
                    'matches': matches,
                    'total_expected': len(expected_sheets),
                    'priority': priority,
                    'score': score
                })

                print(f"{temp_parser.get_template_type()}: {matches}/{len(expected_sheets)} sheets match (score: {score:.2f})")

            # Sort by score (highest first)
            parser_scores.sort(key=lambda x: x['score'], reverse=True)

            # Return the template type with highest score
            best_match = parser_scores[0]
            print(f"Best match: {best_match['template_type']} (score: {best_match['score']:.2f})")

            return best_match['template_type']

        except Exception as e:
            print(f"Error detecting template type: {e}")
            # Fallback to BA parser
            return "BA"

    @classmethod
    def create_parser(cls, file_content: bytes, template_type: str = None):
        """
        Create appropriate parser instance
        If template_type is None, auto-detect based on file content
        """
        if template_type is None:
            template_type = cls.detect_template_type(file_content)

        print(f"Creating parser for template type: {template_type}")

        # Find the appropriate parser class
        parser_class = cls._get_parser_class(template_type)

        if parser_class:
            return parser_class(file_content)
        else:
            raise ValueError(f"Unknown template type: {template_type}")

    @classmethod
    def _get_parser_class(cls, template_type: str) -> Optional[Type]:
        """Get parser class by template type"""
        # Map template types to their classes
        parser_map = {
            "UIUX": UIUXParserService,
            "ENGINEER": EngineerParserService,
            "BA": BAParserService
        }
        return parser_map.get(template_type)

    @classmethod
    def get_supported_template_types(cls) -> List[str]:
        """Get list of supported template types"""
        return ["UIUX", "ENGINEER", "BA"]

    @classmethod
    def validate_template(cls, file_content: bytes, template_type: str = None) -> dict:
        """
        Validate if the file can be parsed by the specified template type
        If template_type is None, validate against all parsers
        Returns validation results
        """
        results = {}

        if template_type:
            # Validate against specific template type
            try:
                parser_class = cls._get_parser_class(template_type)
                if parser_class:
                    parser = parser_class(file_content)
                    is_valid = parser.validate_template()
                    results[template_type] = {
                        'valid': is_valid,
                        'sheets_found': parser.xls.sheet_names,
                        'expected_sheets': parser.get_template_sheets()
                    }
                else:
                    results[template_type] = {
                        'valid': False,
                        'error': f'Unknown template type: {template_type}'
                    }
            except Exception as e:
                results[template_type] = {
                    'valid': False,
                    'error': str(e)
                }
        else:
            # Validate against all template types
            for parser_class in cls._parsers:
                try:
                    parser = parser_class(file_content)
                    template_name = parser.get_template_type()
                    is_valid = parser.validate_template()
                    results[template_name] = {
                        'valid': is_valid,
                        'sheets_found': parser.xls.sheet_names,
                        'expected_sheets': parser.get_template_sheets()
                    }
                except Exception as e:
                    template_name = parser_class(b"dummy").get_template_type()
                    results[template_name] = {
                        'valid': False,
                        'error': str(e)
                    }

        return results

# Backward compatibility - maintain ExcelParserService class
class ExcelParserService:
    """
    Backward compatible wrapper that uses ParserFactory
    This maintains the existing API while using the new modular architecture
    """

    def __init__(self, file_content: bytes):
        self.factory_parser = ParserFactory.create_parser(file_content)
        self.excel_file = self.factory_parser.excel_file
        self.xls = self.factory_parser.xls

    def process_file(self, batch_id: str = None, document_id: str = None) -> dict:
        """Process file using the appropriate parser"""
        return self.factory_parser.process_file(batch_id, document_id)