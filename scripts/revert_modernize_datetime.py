import os
import re

def revert_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    # Replace datetime.now(timezone.utc) with datetime.utcnow()
    content = content.replace("datetime.now(timezone.utc)", "datetime.utcnow()")
    
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
                    if revert_file(full_path):
                        print(f"Reverted: {full_path}")
                        updated_count += 1
    print(f"Total files reverted: {updated_count}")

if __name__ == "__main__":
    main()
