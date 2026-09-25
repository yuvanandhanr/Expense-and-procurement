with open("src/repositories/purchase_requisition.py", "r") as f:
    lines = f.readlines()

# Find PRItemRepository start
pr_item_idx = -1
for i, line in enumerate(lines):
    if "class PRItemRepository" in line:
        pr_item_idx = i
        break

# Find list_accessible_prs start
list_acc_idx = -1
for i, line in enumerate(lines):
    if "async def list_accessible_prs" in line:
        list_acc_idx = i
        break

# Extract list_accessible_prs to the end of the file
list_acc_lines = lines[list_acc_idx:]

# Keep everything before list_accessible_prs
new_lines = lines[:list_acc_idx]

# We need to insert list_acc_lines right BEFORE PRItemRepository!
# Actually wait, PRItemRepository is at line 78, list_accessible_prs is at line 93.
# This means list_accessible_prs is INSIDE PRItemRepository.
# We should move list_acc_lines to right above PRItemRepository.

with open("src/repositories/purchase_requisition.py", "w") as f:
    f.writelines(lines[:pr_item_idx])
    f.writelines(list_acc_lines)
    f.writelines(lines[pr_item_idx:list_acc_idx])

