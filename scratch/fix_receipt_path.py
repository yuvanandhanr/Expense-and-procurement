import re

with open("src/api/expenses.py", "r") as f:
    content = f.read()

# Replace image_path=f"/uploads/receipts/{unique_name}"
# With image_path=f"/uploads/{unique_name}"
content = content.replace('image_path=f"/uploads/receipts/{unique_name}",', 'image_path=f"/uploads/{unique_name}",')

with open("src/api/expenses.py", "w") as f:
    f.write(content)
