with open("frontend/src/pages/PurchaseRequisitions.tsx", "r") as f:
    content = f.read()

old_get_status = """  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === "approved" || s === "completed") return <Badge variant="success">{status}</Badge>;
    if (s === "pending" || s === "under review" || s === "submitted" || s.includes("pending")) return <Badge variant="warning">{status}</Badge>;
    if (s === "rejected" || s === "cancelled") return <Badge variant="error">{status}</Badge>;
    return <Badge variant="neutral">{status}</Badge>;
  };"""

new_get_status = """  const getStatusBadge = (status: string) => {
    return <StatusBadge status={status} />;
  };"""

content = content.replace(old_get_status, new_get_status)

with open("frontend/src/pages/PurchaseRequisitions.tsx", "w") as f:
    f.write(content)
