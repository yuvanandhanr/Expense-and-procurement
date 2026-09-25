with open("src/main.py", "r") as f:
    content = f.read()

content = content.replace('app.mount("/uploads/receipts", StaticFiles(directory=UPLOAD_DIR), name="uploads_receipts_fallback")\n', '')

with open("src/main.py", "w") as f:
    f.write(content)
