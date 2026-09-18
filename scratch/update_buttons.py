import os
import re

frontend_pages_dir = '/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages'

for filename in os.listdir(frontend_pages_dir):
    if filename.endswith('.tsx'):
        filepath = os.path.join(frontend_pages_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        new_content = re.sub(r'variant="close" size="sm"', 'variant="close"', content)
        
        # Also let's reduce the spacing at the bottom of modals.
        # Often it is `pt-4` on the parent div containing the buttons.
        # `<div className="flex justify-end space-x-2 pt-4 border-t border-border">`
        # Let's change `pt-4` to `pt-2` or `pt-3`? The user said "the spacing is also too much".
        # Let's change `pt-4` to `pt-2` and `mt-4` to `mt-2` for the button containers.
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filename}")
