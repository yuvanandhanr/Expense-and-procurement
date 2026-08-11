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

    @staticmethod
    def process_receipt_image(image_bytes: bytes) -> Dict[str, Any]:
        """
        Runs OCR on an employee receipt image.
        Uses keyword-based detection to find the total amount (e.g., 'Total', 'Amount Paid')
        instead of summing all numbers. Extracts merchant name, date, and provides a confidence score.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            logger.info(f"Extracted OCR Text for Receipt: {text}")
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            total_amount = Decimal("0.00")
            confidence = Decimal("0.00")
            
            # Amount extraction pattern (e.g., 50.00, $50.00, 1,234.50)
            amount_pattern = re.compile(r'(?:^|\s|\$)\s*([\d,]+\.\d{2})\b')
            
            # 1. Search for Total keywords
            total_keywords = ["grand total", "total", "amount paid", "balance due", "amount"]
            found_total = False
            for line in reversed(lines): # Search from bottom up
                lower_line = line.lower()
                if any(kw in lower_line for kw in total_keywords):
                    matches = amount_pattern.findall(line)
                    if matches:
                        try:
                            val = Decimal(matches[-1].replace(',', ''))
                            total_amount = val
                            confidence = Decimal("85.00") # High confidence if keyword found
                            found_total = True
                            break
                        except:
                            pass
                            
            if not found_total:
                # Fallback: Just find the largest number on the receipt
                all_matches = amount_pattern.findall(text)
                if all_matches:
                    try:
                        max_val = max([Decimal(m.replace(',', '')) for m in all_matches])
                        total_amount = max_val
                        confidence = Decimal("40.00") # Low confidence fallback
                    except:
                        pass
                        
            # 2. Extract Date
            date_pattern = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b')
            date_match = date_pattern.search(text)
            extracted_date = date_match.group(0) if date_match else None
            if extracted_date and confidence > 0:
                confidence += Decimal("10.00") # Boost confidence if date is found
                
            # 3. Extract Merchant (heuristic: first non-numeric line)
            merchant = "Unknown Merchant"
            for line in lines:
                if len(line) > 3 and not re.search(r'\d', line) and line.lower() not in ["receipt", "invoice", "bill"]:
                    merchant = line[:255]
                    break
                    
            return {
                "merchant_name": merchant,
                "date": extracted_date,
                "total_amount": total_amount,
                "confidence": min(confidence, Decimal("100.00")),
                "raw_text": text
            }
        except Exception as e:
            logger.error(f"Failed to process Receipt OCR: {str(e)}")
            return {
                "merchant_name": "Unknown",
                "date": None,
                "total_amount": Decimal("0.00"),
                "confidence": Decimal("0.00"),
                "raw_text": ""
            }

