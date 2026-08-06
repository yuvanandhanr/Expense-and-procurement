import io
import re
from decimal import Decimal
import pytesseract
from PIL import Image
import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any, Optional

class OCRService:
    @staticmethod
    def process_invoice_image(image_bytes: bytes) -> Dict[str, Any]:
        """
        Runs OCR on the given invoice image bytes and attempts to sum all detected monetary amounts,
        extract the date, and infer a cause.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Extract text
            text = pytesseract.image_to_string(image)
            logger.info(f"Extracted OCR Text: {text}")
            
            # Use regex to find potential amounts
            # Matches formats like: 500, 500.00, $500, 1,500.50, $ 5,000
            amount_pattern = re.compile(r'(?:^|\s|\$)\s*([\d,]+\.\d{2})\b')
            matches = amount_pattern.findall(text)
            
            total = Decimal("0.00")
            for match in matches:
                try:
                    clean_match = match.replace(',', '')
                    val = Decimal(clean_match)
                    total += val
                except Exception:
                    pass
            
            # Extract Date
            date_pattern = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b')
            date_match = date_pattern.search(text)
            extracted_date = date_match.group(0) if date_match else None
            
            # Extract Cause (heuristic: first alphabetic line that is not a generic word)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cause = "General Expense"
            for line in lines:
                if len(line) > 5 and not re.search(r'\d', line) and line.lower() not in ["invoice", "bill", "total", "subtotal", "date", "amount"]:
                    cause = line[:255]
                    break

            return {
                "total": total,
                "date": extracted_date,
                "cause": cause
            }
        except Exception as e:
            logger.error(f"Failed to process OCR image: {str(e)}")
            return {
                "total": Decimal("0.00"),
                "date": None,
                "cause": "General Expense"
            }

