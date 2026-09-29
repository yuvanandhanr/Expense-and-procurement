import os
import re

def modernize_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    # Replace datetime.utcnow() with datetime.now(timezone.utc)
    content = re.sub(r'datetime\.utcnow\(\)', 'datetime.now(timezone.utc)', content)
    # Replace default=datetime.utcnow with default=lambda: datetime.now(timezone.utc)
    content = re.sub(r'default=datetime\.utcnow\b', 'default=lambda: datetime.now(timezone.utc)', content)
    # Replace onupdate=datetime.utcnow with onupdate=lambda: datetime.now(timezone.utc)
    content = re.sub(r'onupdate=datetime\.utcnow\b', 'onupdate=lambda: datetime.now(timezone.utc)', content)

    # If timezone is used in file, ensure it is imported
    if "timezone" in content:
        if "from datetime import" in content:
            # Check if timezone is in the import line
            def add_tz(m):
                line = m.group(0)
                if "timezone" not in line:
                    return line.replace("from datetime import ", "from datetime import timezone, ")
                return line
            content = re.sub(r'from datetime import [^\n]+', add_tz, content, count=1)
        elif "import datetime" in content:
            if "from datetime import timezone" not in content:
                content = content.replace("import datetime", "import datetime\nfrom datetime import timezone")
        else:
            content = "from datetime import timezone\n" + content

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    target_dirs = ["src", "tests"]
    updated_count = 0
    for tdir in target_dirs:
        for root, _, files in os.walk(tdir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    if modernize_file(full_path):
                        print(f"Modernized: {full_path}")
                        updated_count += 1
    print(f"Total files modernized: {updated_count}")

if __name__ == "__main__":
    main()
