import os
import re

directories = ['frontend/src', 'src', 'tests']

for directory in directories:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.tsx', '.ts', '.py')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    # Check if line contains $ followed by Number
                    if re.search(r'\$Number', line) or re.search(r'\$\{Number', line) or re.search(r'\$\w', line) or re.search(r'\$\d', line) or re.search(r'\$[{a-z]', line):
                        # But ignore typical js string interpolation like `${className}` unless preceded by `$`
                        # Actually let's just print lines with \$ followed by Number or digit
                        if re.search(r'\$\{Number', line) or re.search(r'\$\d', line) or re.search(r'\$0\.00', line) or re.search(r'>\$', line) or re.search(r'\>\s?\$', line) or re.search(r' \$(?=\{)', line) or re.search(r'\$ \$\{', line) or re.search(r'\$\{\w*\.total', line) or re.search(r'\$\{\w*\.amount', line):
                            pass
                            #print(f"{filepath}:{i+1}: {line.strip()}")

