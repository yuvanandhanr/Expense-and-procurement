import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button, Input } from "../components/ui";
import { api } from "../services/api";
import toast from "react-hot-toast";
import { QRCodeSVG } from 'qrcode.react';
import { ShieldCheck, UserCheck, Briefcase, ChevronRight, Lock, Sparkles, Building2 } from "lucide-react";

declare global {
  interface Window {
    google: any;
  }
}

const GoogleIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
    />
  </svg>
);

export const Login: React.FC = () => {
  const { googleLogin, vendorLogin } = useAuth();
  const navigate = useNavigate();
  
  // Tab controller: "employee" | "vendor"
  const [activeTab, setActiveTab] = React.useState<"employee" | "vendor">("employee");
  
  // Employee Google Email input state
  const [employeeEmail, setEmployeeEmail] = React.useState("");
  const [showEmailInput, setShowEmailInput] = React.useState(false);
  
  // Vendor OTP form state
  const [vendorEmail, setVendorEmail] = React.useState("");
  const [otp, setOtp] = React.useState("");
  const [otpSent, setOtpSent] = React.useState(false);
  const [isMfaRequired, setIsMfaRequired] = React.useState(false);
  const [mfaSetupData, setMfaSetupData] = React.useState<{secret: string, uri: string} | null>(null);
  const [sendingOtp, setSendingOtp] = React.useState(false);
  
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleCredentialResponse = async (response: any) => {
    setIsSubmitting(true);
    setError("");
    try {
      await googleLogin(response.credential);
      toast.success("Authenticated with Google Workspace!");
      setTimeout(() => {
        navigate("/");
      }, 100);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Google authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSignInClick = () => {
    if (window.google?.accounts?.id) {
      try {
        window.google.accounts.id.prompt((notification: any) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
             toast.error("Google Sign-In popup blocked. Please allow popups or try again.");
          }
        });
        return;
      } catch (e) {
        console.warn("GSI prompt fallback", e);
      }
    }
    // Fallback standard Google login
    toast.error("Google Identity Services failed to load. Please refresh.");
  };

  const handleCustomGoogleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!employeeEmail.trim()) {
      setError("Please enter your corporate Google email address.");
      return;
    }
    const cleanEmail = employeeEmail.trim().toLowerCase();
    handleCredentialResponse({ credential: `mock_google_${cleanEmail}` });
  };

  React.useEffect(() => {
    const initializeGoogle = () => {
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "548174577821-mockgoogleclientid.apps.googleusercontent.com";
      
      if (window.google && activeTab === "employee") {
        try {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          });
          const btnElem = document.getElementById("google-signin-btn");
          if (btnElem) {
            window.google.accounts.id.renderButton(
              btnElem,
              { theme: "filled_blue", size: "large", width: "100%", shape: "rectangular", text: "signin_with" }
            );
          }
        } catch (err) {
          console.warn("Google SDK init warning:", err);
        }
      }
    };

    if (activeTab === "employee") {
      if (window.google) {
        initializeGoogle();
      } else {
        const interval = setInterval(() => {
          if (window.google) {
            initializeGoogle();
            clearInterval(interval);
          }
        }, 500);
        return () => clearInterval(interval);
      }
    }
  }, [activeTab]);

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vendorEmail) {
      setError("Please enter your registered vendor email address.");
      return;
    }
    setError("");
    setSendingOtp(true);
    try {
      const res = await api.post("/auth/vendor/otp-request", { email: vendorEmail });
      setOtpSent(true);
      if (res.data?.mfa_required) {
        setIsMfaRequired(true);
        setMfaSetupData(null);
        toast.success("Please enter your Authenticator App code.");
      } else if (res.data?.mfa_setup_required) {
        setIsMfaRequired(true);
        setMfaSetupData({ secret: res.data.secret, uri: res.data.uri });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to send OTP. Is your email registered?");
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) {
      setError("Please enter the 6-digit OTP code.");
      return;
    }
    setError("");
    setIsSubmitting(true);
    try {
      await vendorLogin(vendorEmail, otp);
      toast.success("Login successful!");
      setTimeout(() => {
        navigate("/vendor-portal");
      }, 100);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid Authenticator code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const testAccounts = [
    { name: "Alex Rivera", role: "Admin", email: "mock_google_y.raja@dataeko.ai", badgeColor: "bg-blue-500/15 text-blue-500 border-blue-500/30" },
    { name: "Sarah Chen", role: "CEO", email: "mock_google_ceo@dataeko.ai", badgeColor: "bg-purple-500/15 text-purple-500 border-purple-500/30" },
    { name: "Marcus Johnson", role: "CFO", email: "mock_google_cfo@dataeko.ai", badgeColor: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30" },
    { name: "Elena Rodriguez", role: "Finance Mgr", email: "mock_google_finance@dataeko.ai", badgeColor: "bg-teal-500/15 text-teal-500 border-teal-500/30" },
    { name: "David Kim", role: "Manager", email: "mock_google_manager@dataeko.ai", badgeColor: "bg-amber-500/15 text-amber-500 border-amber-500/30" },
    { name: "Rachel Foster", role: "Employee", email: "mock_google_employee@dataeko.ai", badgeColor: "bg-slate-500/15 text-slate-500 border-slate-500/30" },
  ];

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden p-4 sm:p-6">
      {/* Apple Frosted Card Container */}
      <div className="w-full max-w-[440px] relative z-10 apple-card rounded-3xl p-6 sm:p-8 backdrop-blur-3xl shadow-2xl animate-spring-in border border-border/80">
        
        {/* Apple Brand Identity Header */}
        <div className="text-center pt-2 pb-4 border-b border-border/50">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary to-primary-hover flex items-center justify-center text-white font-extrabold text-xl mx-auto shadow-apple-glow mb-3">
            ✦
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-foreground">
            ProcureSync
          </h2>
          <p className="text-xs font-semibold text-muted-foreground mt-1 tracking-tight">
            Enterprise Single Sign-On Portal
          </p>
        </div>
        
        <div className="space-y-6 pt-3">
          {/* Apple Segmented Pill Switcher */}
          <div className="p-1 bg-muted/70 backdrop-blur-md rounded-full border border-border/60 flex items-center shadow-inner">
            <button
              type="button"
              onClick={() => { setActiveTab("employee"); setError(""); }}
              className={`flex-1 py-2 px-3 text-xs font-bold rounded-full transition-all duration-300 ${
                activeTab === "employee"
                  ? "bg-card text-foreground shadow-apple-sm border border-border/50 scale-[1.01]"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Employee Login
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab("vendor"); setError(""); }}
              className={`flex-1 py-2 px-3 text-xs font-bold rounded-full transition-all duration-300 ${
                activeTab === "vendor"
                  ? "bg-card text-foreground shadow-apple-sm border border-border/50 scale-[1.01]"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Supplier Partner
            </button>
          </div>

          {activeTab === "employee" ? (
            <div className="space-y-4 animate-fade-in">
              <div className="text-center space-y-1">
                <p className="text-xs text-muted-foreground">
                  Authenticate securely using your corporate Google Workspace account.
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium animate-fade-in">
                  {error}
                </div>
              )}

              {/* Primary Google OAuth Action */}
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={handleGoogleSignInClick}
                  disabled={isSubmitting}
                  className="w-full py-3 px-4 rounded-2xl bg-card hover:bg-muted/80 text-foreground border border-border shadow-apple-sm hover:shadow-apple-md transition-all duration-300 font-semibold text-sm flex items-center justify-center gap-3 group active:scale-[0.99] cursor-pointer"
                >
                  <GoogleIcon className="w-5 h-5 shrink-0 group-hover:scale-105 transition-transform" />
                  <span>{isSubmitting ? "Authenticating..." : "Sign in with Google"}</span>
                </button>

                {/* Custom Google Workspace Email Drawer */}
                {!showEmailInput ? (
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => setShowEmailInput(true)}
                      className="text-[11px] text-primary font-semibold hover:underline"
                    >
                      Or enter Google Workspace email (@dataeko.ai)
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleCustomGoogleEmailSubmit} className="space-y-2 p-3 bg-muted/40 rounded-2xl border border-border/60 animate-fade-in">
                    <div className="flex gap-2">
                      <Input
                        type="email"
                        placeholder="yourname@dataeko.ai"
                        value={employeeEmail}
                        onChange={(e) => setEmployeeEmail(e.target.value)}
                        className="text-xs flex-1"
                        autoFocus
                      />
                      <Button type="submit" size="sm" disabled={isSubmitting}>
                        Login
                      </Button>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-muted-foreground px-1">
                      <span>Must be registered corporate domain</span>
                      <button
                        type="button"
                        onClick={() => setShowEmailInput(false)}
                        className="text-muted-foreground hover:text-foreground underline"
                      >
                        Hide
                      </button>
                    </div>
                  </form>
                )}
                
                {/* Fallback container for Google SDK render if available */}
                <div id="google-signin-btn" className="w-full flex justify-center empty:hidden"></div>

                <div className="relative flex py-1 items-center">
                  <div className="flex-grow border-t border-border/60"></div>
                  <span className="flex-shrink mx-3 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                    Quick Access Profiles
                  </span>
                  <div className="flex-grow border-t border-border/60"></div>
                </div>
                
                {/* Apple Interactive Profile Tiles Grid */}
                <div className="grid grid-cols-2 gap-2.5">
                  {testAccounts.map((acc, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleCredentialResponse({ credential: acc.email })}
                      disabled={isSubmitting}
                      className="apple-user-tile p-2.5 rounded-xl flex items-center justify-between text-left group cursor-pointer"
                    >
                      <div className="min-w-0 pr-1">
                        <p className="text-xs font-bold text-foreground truncate group-hover:text-primary transition-colors">
                          {acc.name}
                        </p>
                        <span className={`inline-block px-1.5 py-0.5 rounded-md text-[9px] font-extrabold uppercase tracking-wider border mt-0.5 ${acc.badgeColor}`}>
                          {acc.role}
                        </span>
                      </div>
                      <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={otpSent ? handleVerifyOtp : handleRequestOtp} className="space-y-4 animate-fade-in">
              <div className="text-center space-y-1">
                <p className="text-xs text-muted-foreground">
                  {mfaSetupData
                    ? "Scan QR code with your Authenticator App."
                    : isMfaRequired 
                    ? "Enter your 6-digit Authenticator code." 
                    : "Enter your registered vendor email address."}
                </p>
              </div>

              {mfaSetupData && (
                <div className="apple-card p-4 rounded-2xl text-center animate-spring-in">
                  <p className="text-xs text-muted-foreground mb-3">
                    Scan using Google Authenticator or Apple Passwords:
                  </p>
                  <div className="flex justify-center bg-white p-3 rounded-2xl mx-auto w-fit mb-3 shadow-inner">
                    <QRCodeSVG value={mfaSetupData.uri} size={120} />
                  </div>
                </div>
              )}

              <Input
                id="vendorEmail"
                type="email"
                label="Registered Vendor Email"
                placeholder="vendor@company.com"
                value={vendorEmail}
                onChange={(e) => setVendorEmail(e.target.value)}
                disabled={otpSent}
              />

              {otpSent && (
                <div className="space-y-2 animate-spring-in">
                  <Input
                    id="otp"
                    type="text"
                    label={isMfaRequired ? "Authenticator Code" : "Verification Code (OTP)"}
                    placeholder="••••••"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="text-center tracking-[0.4em] font-bold text-lg font-mono"
                  />
                </div>
              )}

              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full py-2.5 text-xs font-bold"
                disabled={sendingOtp || isSubmitting}
              >
                {sendingOtp
                  ? "Checking..."
                  : isSubmitting
                  ? "Verifying..."
                  : otpSent
                  ? "Verify & Continue"
                  : "Continue"}
              </Button>
              
              <div className="space-y-2 pt-1">
                <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest text-center">
                  Mock Supplier Accounts
                </span>
                
                <div className="space-y-1.5">
                  {[
                    { name: "Apex Systems", email: "vendor@example.com" },
                    { name: "Nexus Tech Solutions", email: "vendor2@example.com" },
                    { name: "Global Supply Co", email: "vendor3@example.com" }
                  ].map((v, i) => (
                    <button 
                      key={i}
                      type="button"
                      className="w-full apple-user-tile py-2 px-3 rounded-xl text-xs font-semibold text-foreground flex items-center justify-between" 
                      onClick={async () => {
                        try {
                          await vendorLogin(v.email, "123456");
                          setTimeout(() => navigate("/vendor-portal"), 100);
                        } catch (err) {
                          console.error("Mock Vendor Login failed:", err);
                        }
                      }}
                    >
                      <span className="flex items-center gap-2">
                        <Building2 className="w-3.5 h-3.5 text-primary" />
                        {v.name}
                      </span>
                      <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
                    </button>
                  ))}
                </div>
              </div>

              {otpSent && (
                <button
                  type="button"
                  onClick={() => { setOtpSent(false); setOtp(""); setMfaSetupData(null); }}
                  className="w-full text-center text-xs text-primary hover:underline pt-1"
                >
                  Change Email Address
                </button>
              )}
            </form>
          )}

          <div className="text-center text-[10.5px] text-muted-foreground font-medium pt-2 border-t border-border/40">
            Restricted access for authorized personnel only.
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
