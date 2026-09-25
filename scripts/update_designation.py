import re

def update_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Pattern to match the current designation logic
    old_logic1 = r'"requestor_designation": reporter\.designation if reporter and hasattr\(reporter, \'designation\'\) and reporter\.designation else "",'
    new_logic1 = '''"requestor_designation": reporter.designation if reporter and hasattr(reporter, 'designation') and reporter.designation else (", ".join(r.role_name for r in reporter.roles) if reporter and hasattr(reporter, 'roles') and reporter.roles else "Employee"),'''
    
    old_logic2 = r'"requestor_designation": requestor\.designation if requestor and hasattr\(requestor, \'designation\'\) and requestor\.designation else "",'
    new_logic2 = '''"requestor_designation": requestor.designation if requestor and hasattr(requestor, 'designation') and requestor.designation else (", ".join(r.role_name for r in requestor.roles) if requestor and hasattr(requestor, 'roles') and requestor.roles else "Employee"),'''

    content = re.sub(old_logic1, new_logic1, content)
    content = re.sub(old_logic2, new_logic2, content)

    with open(filepath, 'w') as f:
        f.write(content)

update_file('src/api/approvals_inbox.py')
update_file('src/services/approval_service.py')
print("Done")
