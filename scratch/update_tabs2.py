import re

with open("frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

old_approved = r"const isApprovedWf = \(wf: any\) => \{\n\s+const s = String\(wf\?.status \|\| \"\"\)\.toLowerCase\(\);\n\s+return s\.includes\(\"approved\"\).*?\n\s+\};"
new_approved = """const isApprovedWf = (wf: any) => {
    const s = String(wf?.status || "").toLowerCase();
    // Exclude "approved for payment" from being marked as strictly Approved.
    // Closed claims count as Approved.
    if (s === "approved for payment") return false;
    return s.includes("approved") || s === "closed" || s === "pass" || s === "completed" || s === "fulfilled";
  };"""

content = re.sub(old_approved, new_approved, content, flags=re.DOTALL)

# Also let's check isSubmittedWf
old_submitted = r"const isSubmittedWf = \(wf: any\) => \{\n\s+const s = String\(wf\?.status \|\| \"\"\)\.toLowerCase\(\);\n\s+return s \!== \"draft\" \&\& \!isApprovedWf\(wf\) \&\& \!isRejectedWf\(wf\) \&\& \!isReturnedWf\(wf\);\n\s+\};"
if not re.search(old_submitted, content):
    pass # it probably already does !isApprovedWf && !isRejectedWf etc.

with open("frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
