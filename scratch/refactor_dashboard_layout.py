import re

with open("frontend/src/layouts/DashboardLayout.tsx", "r") as f:
    content = f.read()

# 1. Extract the notification center block
notification_start = content.find("            {/* Notification Center */}")
notification_end = content.find("            {/* Apple Role Pill Badge */}")

if notification_start == -1 or notification_end == -1:
    print("Could not find notification block!")
    exit(1)

notification_block = content[notification_start:notification_end]

# 2. Modify the notification badge background to use slate-900 / slate-100
# Original: bg-gradient-to-r from-pink-500 to-rose-500 text-white
new_badge = "bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900"
notification_block = notification_block.replace("bg-gradient-to-r from-pink-500 to-rose-500 text-white", new_badge)

# 3. Remove notification block from top header
content = content[:notification_start] + content[notification_end:]

# 4. Find the sidebar header and insert the notification block there
sidebar_header_start = content.find("{/* Apple Sidebar Header & Logo */}")
if sidebar_header_start == -1:
    print("Could not find sidebar header!")
    exit(1)

# Find the closing div of the sidebar header
sidebar_header_end = content.find("        </div>\n\n        {/* Navigation Items */}", sidebar_header_start)
if sidebar_header_end == -1:
    print("Could not find sidebar header end!")
    exit(1)

# Ensure the sidebar header has 'relative z-50' to support the dropdown!
# Find the opening div of the sidebar header
opening_div = content.find('<div className="h-16 flex items-center justify-between px-5 border-b border-border/60">', sidebar_header_start)
if opening_div != -1:
    content = content[:opening_div] + '<div className="h-16 flex items-center justify-between px-3 border-b border-border/60 relative z-50">' + content[opening_div + len('<div className="h-16 flex items-center justify-between px-5 border-b border-border/60">'):]
    sidebar_header_end += len(' relative z-50') - 2 # adjust index approximately, better to recalculate

sidebar_header_end = content.find("        </div>\n\n        {/* Navigation Items */}", sidebar_header_start)

# We need to adjust indentation of the notification block
# The notification block is indented by 12 spaces.
# In the sidebar header, it should be indented by 10 spaces.
lines = notification_block.split("\n")
adjusted_lines = []
for line in lines:
    if line.startswith("  "):
        adjusted_lines.append(line[2:])
    else:
        adjusted_lines.append(line)
adjusted_notification_block = "\n".join(adjusted_lines)

# Also we need to change "absolute right-0" to "absolute left-0" so the dropdown doesn't go off-screen
adjusted_notification_block = adjusted_notification_block.replace("absolute right-0", "absolute left-4")

new_content = content[:sidebar_header_end] + "\n" + adjusted_notification_block + "\n" + content[sidebar_header_end:]

with open("frontend/src/layouts/DashboardLayout.tsx", "w") as f:
    f.write(new_content)

print("Refactored DashboardLayout.tsx successfully!")
