import os
import re

frontend_pages_dir = '/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages'

for filename in os.listdir(frontend_pages_dir):
    if filename.endswith('.tsx'):
        filepath = os.path.join(frontend_pages_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        # Reduce spacing around footer buttons
        # Match 'pt-4 border-t'
        new_content = re.sub(r'pt-4(\s+border-t)', r'pt-3 mt-2\1', content)
        # Match 'pt-4 flex justify-end'
        new_content = re.sub(r'pt-4\s+flex\s+justify-end', r'pt-3 mt-2 flex justify-end', new_content)
        # Match 'flex justify-end.*?pt-4' (if pt-4 comes after flex)
        new_content = re.sub(r'(flex\s+justify-end\s+.*?)\bpt-4\b', r'\1pt-3 mt-2', new_content)
        
        # We also have "flex justify-end space-x-2 pt-4"
        # The previous regex will match this because of the third pattern.

        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filename}")
