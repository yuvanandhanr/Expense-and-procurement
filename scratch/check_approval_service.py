with open("src/services/approval_service.py", "r") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "requestor.roles" in line or "requestor.designation" in line:
            print(f"{i+1}: {line.strip()}")
