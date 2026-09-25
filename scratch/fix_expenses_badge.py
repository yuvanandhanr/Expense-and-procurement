with open("frontend/src/pages/Expenses.tsx", "r") as f:
    content = f.read()

import re

# Replace the getStatusBadge implementation
old_get_status = """  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === "approved" || s === "closed" || s === "payment requested" || s === "finance verified") return <Badge variant="success">{status}</Badge>;
    if (s === "pending" || s.includes("pending") || s === "corrected claim") return <Badge variant="warning">{status}</Badge>;
    if (s === "rejected" || s === "returned for correction") return <Badge variant="error">{status}</Badge>;
    return <Badge variant="neutral">{status}</Badge>;
  };"""

new_get_status = """  const getStatusBadge = (status: string) => {
    return <StatusBadge status={status} />;
  };"""

content = content.replace(old_get_status, new_get_status)

with open("frontend/src/pages/Expenses.tsx", "w") as f:
    f.write(content)
