import os
import uuid
import zipfile
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.worksheet.worksheet import Worksheet
from models import DocumentImage
from sqlalchemy.orm import Session

class ImageExtractor:
    """Service for extracting and storing images from Excel files"""

    def __init__(self, file_content: bytes, batch_id: str, document_id: str):
        self.file_content = file_content
        self.batch_id = batch_id
        self.document_id = document_id
        self.temp_dir = f"temp_uploads/{batch_id}"
        self.extracted_images = []

    def create_upload_directory(self) -> str:
        """Create directory structure for image storage"""
        document_dir = os.path.join("uploads", self.batch_id, self.document_id)
        image_types = ["mockups", "screenshots", "diagrams", "wireframes"]

        os.makedirs(document_dir, exist_ok=True)
        for img_type in image_types:
            os.makedirs(os.path.join(document_dir, img_type), exist_ok=True)

        return document_dir

    def extract_images_from_excel(self) -> List[Dict[str, Any]]:
        """Extract all images from Excel file using multiple methods"""

        self.create_upload_directory()

        images = []

        # Method 1: Extract using openpyxl (primary method)
        openpyxl_images = self._extract_with_openpyxl()
        images.extend(openpyxl_images)

        # Method 2: Extract using ZIP method (fallback)
        zip_images = self._extract_with_zip()
        images.extend(zip_images)

        # Remove duplicates
        unique_images = self._remove_duplicates(images)

        return unique_images

    def _extract_with_openpyxl(self) -> List[Dict[str, Any]]:
        """Extract images using openpyxl library"""

        images = []
        try:
            workbook = openpyxl.load_workbook(BytesIO(self.file_content))

            for sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]

                # Get images from worksheet
                if hasattr(worksheet, '_images') and worksheet._images:
                    for img in worksheet._images:
                        image_data = self._process_openpyxl_image(img, sheet_name)
                        if image_data:
                            images.append(image_data)

                # Also check workbook level images
                if hasattr(workbook, '_images') and workbook._images:
                    for img in workbook._images:
                        image_data = self._process_openpyxl_image(img, sheet_name)
                        if image_data:
                            images.append(image_data)

        except Exception as e:
            print(f"Openpyxl extraction error: {e}")

        return images

    def _extract_with_zip(self) -> List[Dict[str, Any]]:
        """Extract images directly from ZIP archive"""

        images = []
        try:
            with zipfile.ZipFile(BytesIO(self.file_content)) as zip_file:
                # Look for media files
                for file_info in zip_file.filelist:
                    if file_info.filename.startswith('xl/media/'):
                        image_data = self._process_zip_image(zip_file, file_info)
                        if image_data:
                            images.append(image_data)

        except Exception as e:
            print(f"ZIP extraction error: {e}")

        return images

    def _process_openpyxl_image(self, img: OpenpyxlImage, sheet_name: str) -> Optional[Dict[str, Any]]:
        """Process image extracted via openpyxl"""

        try:
            # Get image data
            if hasattr(img, '_data'):
                image_bytes = img._data()
            else:
                return None

            # Determine image type based on sheet name
            image_type = self._determine_image_type(sheet_name)

            # Save image file
            file_name = f"{uuid.uuid4()}.{self._get_image_extension(image_bytes)}"
            relative_path = os.path.join(
                self.batch_id, self.document_id, image_type, file_name
            )
            full_path = os.path.join("uploads", relative_path)

            # Save file
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(image_bytes)

            # Get image dimensions
            try:
                with Image.open(BytesIO(image_bytes)) as pil_img:
                    width, height = pil_img.size
                    mime_type = pil_img.format.lower() if pil_img.format else None
            except:
                width, height = None, None
                mime_type = None

            return {
                'image_type': image_type,
                'sheet_name': sheet_name,
                'cell_reference': getattr(img, 'anchor', None),
                'file_name': file_name,
                'file_path': relative_path,
                'file_size': len(image_bytes),
                'mime_type': mime_type,
                'width': width,
                'height': height,
                'extraction_method': 'openpyxl'
            }

        except Exception as e:
            print(f"Error processing openpyxl image: {e}")
            return None

    def _process_zip_image(self, zip_file: zipfile.ZipFile, file_info: zipfile.ZipInfo) -> Optional[Dict[str, Any]]:
        """Process image extracted via ZIP"""

        try:
            # Extract image data
            with zip_file.open(file_info) as file:
                image_bytes = file.read()

            # Determine image type based on filename
            image_type = self._determine_image_type_from_path(file_info.filename)

            # Generate filename
            file_name = os.path.basename(file_info.filename)
            relative_path = os.path.join(
                self.batch_id, self.document_id, image_type, file_name
            )
            full_path = os.path.join("uploads", relative_path)

            # Save file
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(image_bytes)

            # Get image dimensions
            try:
                with Image.open(BytesIO(image_bytes)) as pil_img:
                    width, height = pil_img.size
                    mime_type = pil_img.format.lower() if pil_img.format else None
            except:
                width, height = None, None
                mime_type = None

            return {
                'image_type': image_type,
                'sheet_name': 'Unknown (ZIP extraction)',
                'cell_reference': None,
                'file_name': file_name,
                'file_path': relative_path,
                'file_size': len(image_bytes),
                'mime_type': mime_type,
                'width': width,
                'height': height,
                'extraction_method': 'zip_extraction'
            }

        except Exception as e:
            print(f"Error processing ZIP image: {e}")
            return None

    def _determine_image_type(self, sheet_name: str) -> str:
        """Determine image type based on sheet name"""

        sheet_lower = sheet_name.lower()

        if any(keyword in sheet_lower for keyword in ['design', 'ui', 'ux', 'mockup', 'wireframe']):
            return 'mockups'
        elif any(keyword in sheet_lower for keyword in ['screenshot', 'screen', 'capture']):
            return 'screenshots'
        elif any(keyword in sheet_lower for keyword in ['diagram', 'arch', 'flow', 'chart']):
            return 'diagrams'
        else:
            return 'wireframes'  # Default

    def _determine_image_type_from_path(self, file_path: str) -> str:
        """Determine image type based on file path"""

        path_lower = file_path.lower()
        if 'design' in path_lower or 'mockup' in path_lower or 'ui' in path_lower:
            return 'mockups'
        elif 'screenshot' in path_lower or 'screen' in path_lower:
            return 'screenshots'
        elif 'diagram' in path_lower or 'arch' in path_lower:
            return 'diagrams'
        else:
            return 'wireframes'

    def _get_image_extension(self, image_bytes: bytes) -> str:
        """Determine image file extension from magic bytes"""

        # PNG
        if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        # JPEG
        elif image_bytes.startswith(b'\xff\xd8\xff'):
            return 'jpg'
        # GIF
        elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
            return 'gif'
        # BMP
        elif image_bytes.startswith(b'BM'):
            return 'bmp'
        else:
            return 'png'  # Default to PNG

    def _remove_duplicates(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate images based on file size and content"""

        seen = set()
        unique_images = []

        for img in images:
            # Create a unique key based on file size and type
            key = (img['file_size'], img['image_type'])
            if key not in seen:
                seen.add(key)
                unique_images.append(img)

        return unique_images

    def save_images_to_database(self, db: Session, images: List[Dict[str, Any]]) -> List[DocumentImage]:
        """Save extracted images to database"""

        db_images = []

        for img_data in images:
            db_image = DocumentImage(
                document_id=self.document_id,
                image_type=img_data['image_type'],
                sheet_name=img_data['sheet_name'],
                cell_reference=img_data['cell_reference'],
                file_name=img_data['file_name'],
                file_path=img_data['file_path'],
                file_size=img_data['file_size'],
                mime_type=img_data['mime_type'],
                width=img_data['width'],
                height=img_data['height'],
                extraction_method=img_data['extraction_method']
            )

            db.add(db_image)
            db_images.append(db_image)

        db.commit()
        return db_images

    def generate_image_metadata(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate image metadata for JSON storage"""

        metadata_images = []

        for img in images:
            metadata_images.append({
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
            })

        return metadata_images

    def cleanup_temp_files(self):
        """Clean up temporary files (optional for large files)"""
        # For now, we keep uploaded files
        pass