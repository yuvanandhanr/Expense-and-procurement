import { api } from "../services/api";

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

export const canViewAmount = (user: any): boolean => {
  if (!user) return false;
  const roles: string[] = (user.roles || []).map((r: any) => 
    typeof r === 'string' ? r : (r.role_name || r.name || '')
  );
  // Only Admin and Finance Manager can view amounts.
  // Explicitly hidden from: Employee, Manager, Vendor, CFO, CEO.
  return roles.some(r => r === 'Admin' || r === 'Finance Manager' || r === 'SuperAdmin');
};

export const isPdfReceipt = (receipt?: any, url?: string | null): boolean => {
  if (receipt?.is_pdf) return true;
  const fileName = (receipt?.file_name || "").toLowerCase();
  const imagePath = (receipt?.image_path || "").toLowerCase();
  const rawUrl = (url || receipt?.file_url || "").toLowerCase();

  if (fileName.endsWith(".pdf") || imagePath.endsWith(".pdf")) return true;
  if (rawUrl.split("?")[0].endsWith(".pdf")) return true;
  return false;
};

export const resolveImageUrl = (rawUrl?: string | null, fallbackId?: number | null): string => {
  if (!rawUrl && !fallbackId) return "";

  // Derive origin from VITE_API_URL or relative
  const envApi = import.meta.env.VITE_API_URL || "";
  let baseOrigin = "";
  if (envApi.startsWith("http")) {
    baseOrigin = envApi.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  }

  let finalPath = "";

  // If fallback receipt ID is provided, route directly to the persistent, access-controlled endpoint
  if (fallbackId) {
    finalPath = `/api/v1/expenses/receipts/${fallbackId}/image`;
  } else if (rawUrl && (rawUrl.startsWith("http://") || rawUrl.startsWith("https://") || rawUrl.startsWith("data:"))) {
    finalPath = rawUrl;
  } else if (rawUrl) {
    let path = rawUrl.trim();
    if (!path.startsWith("/")) path = `/${path}`;
    // If it points to /uploads/receipts/, replace with api route if ID is embedded
    finalPath = path;
  }

  if (!finalPath) return "";

  let fullUrl = (finalPath.startsWith("http://") || finalPath.startsWith("https://") || finalPath.startsWith("data:"))
    ? finalPath
    : `${baseOrigin}${finalPath}`;

  // Attach token for authenticated viewing in <img>, <iframe>, and new tabs
  const token = localStorage.getItem("access_token");
  if (token && fullUrl.includes("/expenses/receipts/") && !fullUrl.includes("token=")) {
    fullUrl += (fullUrl.includes("?") ? "&" : "?") + `token=${encodeURIComponent(token)}`;
  }

  return fullUrl;
};

export const downloadReceiptFile = async (receiptId: number, fileName: string = "receipt"): Promise<void> => {
  try {
    const response = await api.get(`/expenses/receipts/${receiptId}/image?download=true`, {
      responseType: "blob",
    });
    const blob = response.data;
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (err) {
    const fallbackUrl = resolveImageUrl("", receiptId) + (resolveImageUrl("", receiptId).includes("?") ? "&" : "?") + "download=true";
    window.open(fallbackUrl, "_blank");
  }
};

