import os
import re

directories = ['frontend/src', 'src', 'tests']

for directory in directories:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.py', '.md')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()

                # Replace literal '$' before interpolation in JSX, like `$${` -> `₹${`
                # Be careful: `\$${` is a string literal '$' followed by '${' in JS templates.
                # Actually in JS template literal, it's `$${`. In TSX text, it's `$${` or just `$`.
                
                # We can replace all occurrences of `\$` followed by `{` when it's meant to be currency.
                # Regex for currency: 
                # \$\s?(\d+) -> ₹\1
                # \$\s?\$\{ -> ₹${
                # \$\s?\{ -> ₹{
                
                new_content = content
                
                new_content = re.sub(r'\$(?=\$\{)', '₹', new_content)
                new_content = re.sub(r'\$(?=\{[a-zA-Z])', '₹', new_content) 
                new_content = re.sub(r'\$(?=[0-9])', '₹', new_content)
                new_content = new_content.replace('dollors', 'rupees').replace('dollars', 'rupees').replace('Dollar', 'Rupee')
                
                # Specific string for expense UI text
                new_content = new_content.replace('$0.00', '₹0.00')

                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")

