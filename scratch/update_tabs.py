import re

with open("frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

# isApprovedWf logic
old_approved = r"const isApprovedWf = \(wf: any\) => \{\n\s+const s = String\(wf\?.status \|\| \"\"\)\.toLowerCase\(\);\n\s+return s === \"approved\" \|\| s === \"fulfilled\" \|\| s === \"approved for payment\" \|\| s === \"closed\";\n\s+\};"
new_approved = """const isApprovedWf = (wf: any) => {
  const s = String(wf?.status || "").toLowerCase();
  return s === "approved" || s === "fulfilled" || s === "closed";
};"""
content = re.sub(old_approved, new_approved, content, flags=re.DOTALL)

with open("frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
