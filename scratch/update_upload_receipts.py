import re

with open("src/api/expenses.py", "r") as f:
    content = f.read()

# 1. Update duplicate check to search the whole DB
old_duplicate_check = r"if content_hash in batch_hashes or await repo.get_receipt_by_content_hash\(report_id, content_hash\):"
new_duplicate_check = """# Check globally for duplicates
        query_dup = select(Receipt).where(Receipt.content_hash == content_hash)
        result_dup = await db.execute(query_dup)
        if content_hash in batch_hashes or result_dup.scalars().first():"""
content = re.sub(old_duplicate_check, new_duplicate_check, content)

# 2. Add 'import asyncio' at the top if missing
if "import asyncio" not in content:
    content = "import asyncio\n" + content

# 3. Update OCRService.process_receipt_image(content) to use asyncio.to_thread
old_ocr = r"ocr_result = OCRService\.process_receipt_image\(content\)"
new_ocr = r"ocr_result = await asyncio.to_thread(OCRService.process_receipt_image, content)"
content = re.sub(old_ocr, new_ocr, content)

with open("src/api/expenses.py", "w") as f:
    f.write(content)
