"""
PDF Handler - Handles PDF parsing and text extraction using PyMuPDF.

This module extracts text content from PDF documents for further processing
by the extraction layer.
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Union
import logging


logger = logging.getLogger(__name__)


class PDFHandler:
    """
    PDF parsing handler using PyMuPDF (fitz).
    
    Handles text extraction from PDF documents with error handling
    and fallback mechanisms.
    """

    def __init__(self):
        """Initialize the PDF handler."""
        pass

    def parse_pdf(self, pdf_path: Union[str, Path]) -> str:
        """
        Parse a PDF file and extract its text content.

        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content from the PDF
            
        Raises:
            FileNotFoundError: If the PDF file does not exist
            ValueError: If the file is not a valid PDF
            RuntimeError: If PDF parsing fails
        """
        pdf_path = Path(pdf_path)
        
        # Validate file exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Validate file extension
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"Not a PDF file: {pdf_path}")
        
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Check if the document is password protected
            if doc.needs_pass:
                raise ValueError(f"Password protected PDF: {pdf_path}")
            
            # Extract text from all pages
            text_parts = []
            
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    
                    # Clean up the text
                    cleaned_text = self._clean_text(text)
                    text_parts.append(cleaned_text)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue  # Skip problematic pages and continue
            
            # Close the document
            doc.close()
            
            # Join all text parts
            full_text = "\n".join(text_parts)
            
            if not full_text.strip():
                raise RuntimeError(f"No text content found in PDF: {pdf_path}")
                
            return full_text
            
        except fitz.FileDataError as e:
            raise ValueError(f"Invalid PDF file: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF {pdf_path}: {e}") from e

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and normalizing characters.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters but preserve common punctuation
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        return text.strip()

    def get_pdf_info(self, pdf_path: Union[str, Path]) -> dict:
        """
        Get metadata and information about the PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            info = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", ""),
                "pages": len(doc),
                "encrypted": doc.is_encrypted,
                "text_chars": 0,
                "text_words": 0,
            }
            
            # Count text characters and words
            text = self.parse_pdf(pdf_path)
            info["text_chars"] = len(text)
            info["text_words"] = len(text.split())
            
            doc.close()
            return info
            
        except Exception as e:
            raise RuntimeError(f"Failed to get PDF info {pdf_path}: {e}") from e