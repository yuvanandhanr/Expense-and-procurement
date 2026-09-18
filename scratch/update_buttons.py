import os
import re

frontend_pages_dir = '/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages'

for filename in os.listdir(frontend_pages_dir):
    if filename.endswith('.tsx'):
        filepath = os.path.join(frontend_pages_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()

        new_content = ""
        last_idx = 0
        
        # Find all <Button tags
        for match in re.finditer(r'<Button\b', content):
            start = match.end()
            
            # Find the closing </Button>
            end_match = re.search(r'</Button>', content[start:])
            if not end_match:
                continue
                
            end = start + end_match.start()
            
            button_inner = content[start:end]
            # Check if it contains 'Cancel' or 'Close' (and nothing else but whitespace)
            
            # Extract the content between > and </Button>
            # we need to find the first > that is outside of {} brackets, which is hard.
            # but we can just split by > from the right side.
            last_bracket = button_inner.rfind('>')
            if last_bracket != -1:
                text_content = button_inner[last_bracket+1:].strip()
                if text_content in ['Cancel', 'Close']:
                    attrs = button_inner[:last_bracket]
                    attrs = re.sub(r'variant="[^"]+"', '', attrs)
                    attrs = re.sub(r'size="[^"]+"', '', attrs)
                    attrs = attrs.strip()
                    
                    new_button = f' variant="close" size="sm" {attrs}>{text_content}'
                    
                    new_content += content[last_idx:start] + new_button
                    last_idx = end
                    
        new_content += content[last_idx:]
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filename}")
