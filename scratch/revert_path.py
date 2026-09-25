with open("src/api/expenses.py", "r") as f:
    content = f.read()

content = content.replace('image_path=f"/uploads/{unique_name}",', 'image_path=f"/uploads/receipts/{unique_name}",')

with open("src/api/expenses.py", "w") as f:
    f.write(content)
