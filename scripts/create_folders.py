import os

def create_structure():
    base_dir = r"c:\Yuvan\Proj\Expense and Procurement"
    
    # List of directories to create
    directories = [
        # Inside src
        "src/api",
        "src/auth",
        "src/employees",
        "src/expenses",
        "src/procurement",
        "src/vendors",
        "src/invoices",
        "src/assets",
        "src/approval",
        "src/policy",
        "src/analytics",
        "src/audit",
        "src/admin",
        "src/notifications",
        "src/storage",
        "src/database",
        "src/models",
        "src/repositories",
        "src/services",
        "src/schemas",
        "src/middleware",
        "src/core",
        "src/utils",
        # Outside src
        "alembic",
        "tests",
        "docs",
        "scripts",
        "docker",
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        # Create a .gitkeep file
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        with open(gitkeep_path, "w") as f:
            f.write("")
        print(f"Created directory and .gitkeep for: {directory}")

if __name__ == "__main__":
    create_structure()
