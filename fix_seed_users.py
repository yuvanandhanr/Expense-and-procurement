import re
with open("scripts/seed_users.py", "r") as f:
    content = f.read()

# We need to make sure seed_users.py adds users.view
