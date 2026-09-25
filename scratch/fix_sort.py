with open("frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

old_sort = """    .sort((a: any, b: any) => {
      const sA = String(a?.status || "").toLowerCase();
      const sB = String(b?.status || "").toLowerCase();
      const isPendingA = sA.includes("pending") || sA.includes("review");
      const isPendingB = sB.includes("pending") || sB.includes("review");
      
      // Priority: pending approval workflows come first
      if (isPendingA && !isPendingB) return -1;
      if (!isPendingA && isPendingB) return 1;"""

new_sort = """    .sort((a: any, b: any) => {
      const isPendingA = isPendingForUser(a);
      const isPendingB = isPendingForUser(b);
      
      // Priority: pending approval workflows (for the current user) come first
      if (isPendingA && !isPendingB) return -1;
      if (!isPendingA && isPendingB) return 1;"""

content = content.replace(old_sort, new_sort)

with open("frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
