with open("frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

old_sort = """    .sort((a: any, b: any) => {
      const isPendingA = isPendingForUser(a);
      const isPendingB = isPendingForUser(b);
      
      // Priority: pending approval workflows (for the current user) come first
      if (isPendingA && !isPendingB) return -1;
      if (!isPendingA && isPendingB) return 1;
      
      // Sort according to time of creation (newest first)"""

new_sort = """    .sort((a: any, b: any) => {
      const isPendingA = isPendingForUser(a);
      const isPendingB = isPendingForUser(b);
      
      // Priority 1: pending approval workflows (for the current user) come first
      if (isPendingA && !isPendingB) return -1;
      if (!isPendingA && isPendingB) return 1;
      
      // Priority 2: keep in-progress above approved/closed/rejected
      const sA = String(a?.status || "").toLowerCase();
      const sB = String(b?.status || "").toLowerCase();
      const isClosedA = sA.includes("closed") || sA === "approved" || sA.includes("reject") || sA.includes("paid");
      const isClosedB = sB.includes("closed") || sB === "approved" || sB.includes("reject") || sB.includes("paid");
      
      if (!isClosedA && isClosedB) return -1;
      if (isClosedA && !isClosedB) return 1;

      // Priority 3: Sort according to time of creation (newest first)"""

content = content.replace(old_sort, new_sort)

with open("frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
