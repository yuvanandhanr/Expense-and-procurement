with open("src/main.py", "r") as f:
    content = f.read()

# Add a second mount for /uploads/receipts
if 'app.mount("/uploads/receipts"' not in content:
    content = content.replace(
        'app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")',
        'app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")\napp.mount("/uploads/receipts", StaticFiles(directory=UPLOAD_DIR), name="uploads_receipts_fallback")'
    )

with open("src/main.py", "w") as f:
    f.write(content)
