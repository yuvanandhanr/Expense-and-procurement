import sqlite3

conn = sqlite3.connect('/Users/a.chaitnasree/Expense-and-procurement/expense_procurement.db')
c = conn.cursor()

# Get existing categories
c.execute("SELECT category_id, category_name FROM asset_categories")
existing = c.fetchall()
existing_names = [row[1] for row in existing]

new_categories = [
    "Hardware", "Network", "Server & Storage", "Software", 
    "Software Licenses", "Cloud", "Security", "Communication", 
    "Office", "Vehicle"
]

for cat in new_categories:
    if cat not in existing_names:
        c.execute("INSERT INTO asset_categories (category_name, description) VALUES (?, ?)", (cat, cat + " assets"))

conn.commit()
conn.close()
