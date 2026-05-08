import fitz  # PyMuPDF
import pdfplumber
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Handles PDF text extraction with fallback mechanisms."""

    def __init__(self):
        self.max_pages = 100  # Limit for large PDFs
        self.chunk_size = 50   # Process in chunks for memory efficiency

    def extract_text(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from PDF using PyMuPDF first, fallback to pdfplumber.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict containing 'text', 'pages', 'success', 'error'
        """
        try:
            # Try PyMuPDF first
            result = self._extract_with_pymupdf(pdf_path)
            if result['success']:
                return result
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")

        try:
            # Fallback to pdfplumber
            result = self._extract_with_pdfplumber(pdf_path)
            if result['success']:
                return result
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")

        return {
            'text': '',
            'pages': [],
            'success': False,
            'error': 'Failed to extract text from PDF using both PyMuPDF and pdfplumber'
        }

    def _extract_with_pymupdf(self, pdf_path: str) -> Dict[str, any]:
        """Extract text using PyMuPDF."""
        doc = fitz.open(pdf_path)
        full_text = ""
        pages = []

        try:
            for page_num in range(min(len(doc), self.max_pages)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text += f"\n--- Page {page_num + 1} ---\n{text}"
                pages.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'char_count': len(text)
                })

            return {
                'text': full_text,
                'pages': pages,
                'success': True,
                'error': None
            }
        finally:
            doc.close()

    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict[str, any]:
        """Extract text using pdfplumber."""
        full_text = ""
        pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages[:self.max_pages]):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}"
                    pages.append({
                        'page_number': page_num + 1,
                        'text': text,
                        'char_count': len(text)
                    })

                # Extract tables if available
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        table_text = "\n".join(["\t".join([str(cell) if cell else "" for cell in row]) for row in table])
                        full_text += f"\n--- Table {table_idx + 1} on Page {page_num + 1} ---\n{table_text}"

        return {
            'text': full_text,
            'pages': pages,
            'success': True,
            'error': None
        }

    def validate_pdf(self, pdf_path: str) -> Dict[str, any]:
        """Validate PDF file before processing."""
        try:
            with fitz.open(pdf_path) as doc:
                info = {
                    'page_count': len(doc),
                    'is_encrypted': doc.is_encrypted,
                    'metadata': doc.metadata
                }
                return {'valid': True, 'info': info}
        except Exception as e:
            return {'valid': False, 'error': str(e)}