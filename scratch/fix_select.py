with open("src/api/expenses.py", "r") as f:
    content = f.read()

# Add from sqlalchemy import select at the top if it's missing globally
if "\nfrom sqlalchemy import select" not in content:
    # Just add it locally inside upload_receipts for safety
    content = content.replace(
        "query_dup = select(Receipt).where(Receipt.content_hash == content_hash)",
        "from sqlalchemy import select\n        query_dup = select(Receipt).where(Receipt.content_hash == content_hash)"
    )

with open("src/api/expenses.py", "w") as f:
    f.write(content)
