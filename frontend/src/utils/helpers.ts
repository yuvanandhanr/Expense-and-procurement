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

export const isValidText = (text?: string | null): boolean => {
  if (!text) return false;
  return /[a-zA-Z0-9]/.test(text);
};

export const resolveImageUrl = (rawUrl?: string | null, fallbackId?: number | null): string => {
  if (!rawUrl && !fallbackId) return "";

  if (rawUrl && (rawUrl.startsWith("http://") || rawUrl.startsWith("https://") || rawUrl.startsWith("data:"))) {
    return rawUrl;
  }

  // Derive origin from VITE_API_URL or relative
  const envApi = import.meta.env.VITE_API_URL || "";
  let baseOrigin = "";
  if (envApi.startsWith("http")) {
    baseOrigin = envApi.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  }

  if (fallbackId && (!rawUrl || rawUrl === "N/A" || rawUrl === "None" || rawUrl === "null")) {
    return `${baseOrigin}/api/v1/expenses/receipts/${fallbackId}/image`;
  }

  if (!rawUrl) return "";

  let path = rawUrl.trim();
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }

  return `${baseOrigin}${path}`;
};

