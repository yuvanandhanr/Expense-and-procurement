export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return "N/A";
  const d = new Date(dateString);
  return isNaN(d.getTime()) ? "N/A" : d.toLocaleDateString();
};

export const getErrorMessage = (err: any, defaultMsg: string = "An error occurred."): string => {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d: any) => {
      const field = d.loc && d.loc.length > 0 ? d.loc[d.loc.length - 1] : "";
      return field ? `${field}: ${d.msg || d.type}` : (d.msg || d.type);
    }).join("\n");
  }
  if (detail && typeof detail === "object") {
    return detail.msg || defaultMsg;
  }
  return err.message || defaultMsg;
};
