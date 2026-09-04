import React, { createContext, useContext, useState, useEffect } from "react";
import { User } from "../types";
import { api, setTokens, clearTokens } from "../services/api";
import toast from "react-hot-toast";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  googleLogin: (credential: string) => Promise<void>;
  vendorLogin: (email: string, otp: string) => Promise<void>;
  logout: () => void;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load profile from localStorage on start
  useEffect(() => {
    const cachedProfile = localStorage.getItem("user_profile");
    if (cachedProfile) {
      try {
        setUser(JSON.parse(cachedProfile));
      } catch {
        clearTokens();
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await api.post("/auth/login", { email, password });
      const { access_token, refresh_token } = response.data;
      
      setTokens(access_token, refresh_token);

      // Retrieve full user profile
      const meResponse = await api.get("/auth/me");
      const userProfile = meResponse.data;
      
      setUser(userProfile);
      localStorage.setItem("user_profile", JSON.stringify(userProfile));
      toast.success(`Welcome back, ${userProfile.first_name}!`);
    } catch (error: any) {
      const msg = error.response?.data?.detail || "Authentication failed. Please check credentials.";
      toast.error(msg);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const googleLogin = async (credential: string) => {
    setIsLoading(true);
    try {
      const response = await api.post("/auth/google", { credential });
      const { access_token, refresh_token } = response.data;
      
      setTokens(access_token, refresh_token);

      // Retrieve full user profile
      const meResponse = await api.get("/auth/me");
      const userProfile = meResponse.data;
      
      setUser(userProfile);
      localStorage.setItem("user_profile", JSON.stringify(userProfile));
      toast.success(`Welcome back, ${userProfile.first_name}!`);
    } catch (error: any) {
      const msg = error.response?.data?.detail || "Google Sign-In authentication failed.";
      toast.error(msg);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const vendorLogin = async (email: string, otp: string) => {
    setIsLoading(true);
    try {
      const response = await api.post("/auth/vendor/otp-verify", { email, otp });
      const { access_token, refresh_token } = response.data;
      
      setTokens(access_token, refresh_token);

      // Retrieve full user profile
      const meResponse = await api.get("/auth/me");
      const userProfile = meResponse.data;
      
      setUser(userProfile);
      localStorage.setItem("user_profile", JSON.stringify(userProfile));
      toast.success(`Welcome back, ${userProfile.first_name || "Supplier"}!`);
    } catch (error: any) {
      const msg = error.response?.data?.detail || "Vendor OTP verification failed.";
      toast.error(msg);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    clearTokens();
    toast.success("Logged out successfully.");
    window.location.href = "/login";
  };

  const hasRole = (roleName: string): boolean => {
    if (!user || !Array.isArray(user.roles)) return false;
    // Treat "Finance" and "Finance Manager" interchangeably for frontend access checks
    if (roleName === "Finance" && user.roles.some((role) => role?.role_name === "Finance Manager" && role?.status)) return true;
    if (roleName === "Finance Manager" && user.roles.some((role) => role?.role_name === "Finance" && role?.status)) return true;
    // Treat "Vendor" and "Vendor Portal" interchangeably
    if (roleName === "Vendor" && user.roles.some((role) => role?.role_name === "Vendor Portal" && role?.status)) return true;
    if (roleName === "Vendor Portal" && user.roles.some((role) => role?.role_name === "Vendor" && role?.status)) return true;
    return user.roles.some((role) => role?.role_name === roleName && role?.status);
  };

  const hasPermission = (permissionName: string): boolean => {
    if (!user || !Array.isArray(user.roles)) return false;
    // Check permissions across all active roles
    return user.roles.some((role) => {
      if (!role?.status) return false;
      // Admin bypass
      if (role?.role_name === "Admin") return true;
      return role?.permissions?.some((perm) => perm?.permission_name === permissionName) || false;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        googleLogin,
        vendorLogin,
        logout,
        hasRole,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
