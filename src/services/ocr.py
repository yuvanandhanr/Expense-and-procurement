import io
import os
import re
import shutil
from decimal import Decimal
import pytesseract
from PIL import Image, ImageEnhance
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Configure pytesseract binary path dynamically
tesseract_path = shutil.which("tesseract")
if not tesseract_path:
    for candidate in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract"]:
        if os.path.exists(candidate):
            tesseract_path = candidate
            break

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    logger.info(f"Configured Tesseract binary path at: {tesseract_path}")
else:
    logger.warning("Tesseract binary not found in PATH or standard system directories.")

from typing import Dict, Any, Optional

class OCRService:
    @staticmethod
    def _extract_receipt_date(text: str) -> Optional[str]:
        """Extract a valid receipt date, tolerating common OCR character errors.

        Dates are returned in ISO format so the API can persist them reliably.
        A correction is only made when OCR produced an impossible month, such as
        ``67`` for a printed ``07``; valid dates are never rewritten.
        """
        date_pattern = re.compile(
            r"(?:date|dated)\s*[:#-]?\s*"
            r"(\d{1,2}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*\d{2,4})",
            re.IGNORECASE,
        )
        fallback_pattern = re.compile(
            r"\b(\d{4}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*\d{1,2}|"
            r"\d{1,2}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*\d{2,4})\b"
        )
        match = date_pattern.search(text) or fallback_pattern.search(text)
        if not match:
            return None

        candidate = re.sub(r"\s+", "", match.group(1))
        candidate = candidate.replace("/", "-").replace(".", "-")
        parts = candidate.split("-")
        if len(parts) != 3:
            return None
        # Tesseract commonly reads a leading 0 as 6 on small receipt text.
        # Apply this only to an invalid month, never to a valid date.
        if len(parts[1]) == 2 and int(parts[1]) > 12 and parts[1].startswith("6"):
            parts[1] = "0" + parts[1][1]
        candidate = "-".join(parts)

        formats = ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%d-%m-%y", "%m-%d-%y")
        for date_format in formats:
            try:
                return datetime.strptime(candidate, date_format).date().isoformat()
            except ValueError:
                continue
        return None

    @staticmethod
    def _preprocess_image(image: Image.Image) -> Image.Image:
        """
        Enhances image for OCR by converting to grayscale and increasing contrast.
        """
        try:
            # Convert to grayscale
            gray = image.convert('L')
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            return enhancer.enhance(1.8)
        except Exception as e:
            logger.warning(f"Image preprocessing warning: {e}")
            return image

    @staticmethod
    def process_invoice_image(image_bytes: bytes) -> Dict[str, Any]:
        """
        Runs OCR on the given invoice image bytes and attempts to sum all detected monetary amounts,
        extract the date, and infer a cause.
        """
        try:
            raw_image = Image.open(io.BytesIO(image_bytes))
            processed_image = OCRService._preprocess_image(raw_image)
            
            # Extract text
            text = pytesseract.image_to_string(processed_image)
            if not text.strip():
                text = pytesseract.image_to_string(raw_image)
                
            logger.info(f"Extracted OCR Text: {text}")
            
            # Use regex to find potential amounts
            amount_pattern = re.compile(r'(?:^|\s|[$€£₹]|\bUSD\b|\bEUR\b|\bINR\b)\s*([\d,]+\.\d{2})\b', re.IGNORECASE)
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
            date_pattern = re.compile(r'\b(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\b')
            date_match = date_pattern.search(text)
            extracted_date = date_match.group(0) if date_match else None
            
            # Extract Cause
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
            raw_image = Image.open(io.BytesIO(image_bytes))
            processed_image = OCRService._preprocess_image(raw_image)
            
            text = pytesseract.image_to_string(processed_image)
            if not text.strip():
                text = pytesseract.image_to_string(raw_image)
                
            logger.info(f"Extracted OCR Text for Receipt: {text}")
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            total_amount = Decimal("0.00")
            confidence = Decimal("0.00")
            
            # Flexible amount pattern (e.g., 50.00, 1,234.50, $50, 50.0)
            amount_pattern = re.compile(r'(?:^|\s|[$€£₹]|\bUSD\b|\bEUR\b|\bINR\b)\s*([\d,]+\.?\d{0,2})\b', re.IGNORECASE)
            strict_amount_pattern = re.compile(r'(?:^|\s|[$€£₹]|\bUSD\b|\bEUR\b|\bINR\b)\s*([\d,]+\.\d{2})\b', re.IGNORECASE)
            
            # 1. Search for Total keywords (bottom-up search)
            total_keywords = ["grand total", "total", "amount paid", "balance due", "subtotal", "amount", "total amount"]
            found_total = False
            for line in reversed(lines):
                lower_line = line.lower()
                if any(kw in lower_line for kw in total_keywords):
                    matches = strict_amount_pattern.findall(line) or amount_pattern.findall(line)
                    if matches:
                        try:
                            # Parse numeric value
                            clean_str = matches[-1].replace(',', '')
                            if '.' not in clean_str:
                                clean_str += ".00"
                            val = Decimal(clean_str)
                            if val > 0:
                                total_amount = val
                                confidence = Decimal("85.00")
                                found_total = True
                                break
                        except Exception:
                            pass
                            
            if not found_total:
                # Fallback: Find largest numeric value on receipt
                all_matches = strict_amount_pattern.findall(text) or amount_pattern.findall(text)
                valid_vals = []
                for m in all_matches:
                    try:
                        clean_str = m.replace(',', '')
                        if '.' not in clean_str:
                            clean_str += ".00"
                        v = Decimal(clean_str)
                        if 0 < v < Decimal("100000.00"): # filter out unrealistic transaction numbers
                            valid_vals.append(v)
                    except Exception:
                        pass
                if valid_vals:
                    total_amount = max(valid_vals)
                    confidence = Decimal("60.00")
                        
            # 2. Extract Date. 
            # Optimization: Use the already extracted text to avoid redundant Tesseract passes.
            extracted_date = OCRService._extract_receipt_date(text)
            if extracted_date:
                if confidence > 0:
                    confidence += Decimal("10.00")
                else:
                    confidence = Decimal("30.00")
                
            # 3. Extract Merchant Name and an optional stated expense category.
            merchant = "Unknown Merchant"
            category = None
            for line in lines:
                category_match = re.search(r"expense\s*category\s*[:#-]?\s*(.+)", line, re.IGNORECASE)
                if category_match:
                    category = category_match.group(1).strip()[:100] or None
                    break
            for line in lines:
                clean_l = re.sub(r'[^a-zA-Z0-9\s&,-]', '', line).strip()
                if len(clean_l) > 3 and not re.search(r'\d', clean_l) and clean_l.lower() not in ["receipt", "invoice", "bill", "tax invoice", "customer copy", "welcome"]:
                    merchant = clean_l[:255]
                    if confidence > 0:
                        confidence += Decimal("5.00")
                    break
                    
            if total_amount > 0 and confidence < 50:
                confidence = Decimal("50.00")

            # Extract receipt number (e.g. Receipt #: 1234, Inv: 5678)
            receipt_number = None
            receipt_no_pattern = re.compile(r'(?:receipt|invoice|inv|bill)\s*(?:no|number|#)?\s*[:.-]?\s*([A-Za-z0-9_-]+)', re.IGNORECASE)
            for line in lines:
                match = receipt_no_pattern.search(line)
                if match:
                    receipt_number = match.group(1).strip()
                    break

            return {
                "merchant_name": merchant,
                "date": extracted_date,
                "receipt_number": receipt_number,
                "category": category,
                "total_amount": total_amount,
                "confidence": min(confidence, Decimal("99.85")),
                "raw_text": text
            }
        except Exception as e:
            logger.error(f"Failed to process Receipt OCR: {str(e)}")
            return {
                "merchant_name": "Unknown",
                "date": None,
                "receipt_number": None,
                "total_amount": Decimal("0.00"),
                "confidence": Decimal("0.00"),
                "raw_text": ""
            }

