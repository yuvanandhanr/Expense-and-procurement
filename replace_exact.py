import os

replacements = {
    "${Number(": "₹{Number(",
    "${generateMatchDetails(": "₹{generateMatchDetails(",
    "${a.cost": "₹{a.cost",
    "${p.total_amount": "₹{p.total_amount",
    "${item.total_price": "₹{item.total_price",
    "${po.grand_total": "₹{po.grand_total",
    "${q.total_amount": "₹{q.total_amount",
    "$0.00": "₹0.00",
    "`$${": "`₹${",
    'TBD"}</td>': 'TBD"}</td>', # just placeholder
    "dollors": "rupees",
    "dollars": "rupees",
    "Dollar": "Rupee"
}

directories = ['frontend/src', 'src', 'tests']

for directory in directories:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.py', '.md')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()

                new_content = content
                
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                # Check for `>${` replacing to `>₹{`
                new_content = new_content.replace(">${Number", ">₹{Number")

                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")

