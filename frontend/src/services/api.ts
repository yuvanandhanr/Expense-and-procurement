import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import toast from "react-hot-toast";

// Get base API URL (default to relative path mapped by proxy)
let API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";
if (API_BASE_URL && API_BASE_URL.startsWith('http') && !API_BASE_URL.endsWith('/api/v1')) {
  API_BASE_URL = API_BASE_URL.replace(/\/$/, "") + "/api/v1";
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 300s timeout
});

// Cache tokens locally for quick synchronous access in interceptors
let accessToken: string | null = localStorage.getItem("access_token");
let refreshToken: string | null = localStorage.getItem("refresh_token");

export const setTokens = (access: string, refresh: string) => {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_profile");
};

// Request Interceptor: Inject JWT token into headers
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track token refresh state to prevent multiple parallel refresh requests
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor: Handle auto-refresh and global errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        toast.error("Request timed out. The server might be processing a large file.");
      } else {
        toast.error(`Network Error: ${error.message}. Please ensure the backend is running.`);
      }
      return Promise.reject(error);
    }

    const { status } = error.response;

    // Handle token refresh on 401 Unauthorized
    if (status === 401 && !originalRequest._retry) {
      if (
        originalRequest.url?.includes("/auth/login") ||
        originalRequest.url?.includes("/auth/google") ||
        originalRequest.url?.includes("/auth/vendor/otp") ||
        originalRequest.url?.includes("/auth/refresh")
      ) {
        clearTokens();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Call backend token refresh endpoint
        const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = refreshResponse.data;
        setTokens(access_token, refresh_token);
        
        isRefreshing = false;
        processQueue(null, access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        processQueue(new Error("Refresh token expired"), null);
        clearTokens();
        toast.error("Session expired. Please log in again.");
        window.location.href = "/";
        return Promise.reject(refreshError);
      }
    }

    // Handle global access control errors
    if (status === 403) {
      toast.error("Access Denied: You do not have permissions for this action.");
    } else if (status === 404) {
      // Allow individual endpoints to handle 404 silently if desired
      console.warn("API Endpoint Resource Not Found (404):", originalRequest.url);
    } else if (status >= 500) {
      toast.error("Internal Server Error. Please contact administrator.");
    }

    return Promise.reject(error);
  }
);

// Simple In-Memory Cache for Instant Tab Switching
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 30000; // 30 seconds

const originalGet = api.get;
api.get = async (url: string, config?: any) => {
  // Don't cache search queries or live endpoints
  if (url.includes("/search?q=") || url.includes("/notifications")) {
    return originalGet.call(api, url, config);
  }
  
  const key = url + (config ? JSON.stringify(config) : "");
  const cached = cache.get(key);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return Promise.resolve(cached.data);
  }
  
  const response = await originalGet.call(api, url, config);
  cache.set(key, { data: response, timestamp: Date.now() });
  return response;
};

// Clear cache on mutations to ensure fresh data
const originalPost = api.post;
api.post = async (...args: Parameters<typeof originalPost>) => {
  cache.clear();
  return originalPost.apply(api, args);
};

const originalPut = api.put;
api.put = async (...args: Parameters<typeof originalPut>) => {
  cache.clear();
  return originalPut.apply(api, args);
};

const originalDelete = api.delete;
api.delete = async (...args: Parameters<typeof originalDelete>) => {
  cache.clear();
  return originalDelete.apply(api, args);
};
