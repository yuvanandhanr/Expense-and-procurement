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

export const Login: React.FC = () => {
  const { googleLogin, vendorLogin } = useAuth();
  const navigate = useNavigate();
  
  // Tab controller: "employee" | "vendor"
  const [activeTab, setActiveTab] = React.useState<"employee" | "vendor">("employee");
  
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

  React.useEffect(() => {
    const initializeGoogle = () => {
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "placeholder";
      
      if (window.google && activeTab === "employee" && clientId !== "placeholder" && clientId.length > 20) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
        });
        window.google.accounts.id.renderButton(
          document.getElementById("google-signin-btn"),
          { theme: "filled_blue", size: "large", width: "100%", shape: "rectangular" }
        );
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
            <div className="space-y-5 animate-fade-in">
              <div className="text-center space-y-1">
                <p className="text-xs text-muted-foreground">
                  Authenticate securely using your corporate workspace ID.
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium animate-fade-in">
                  {error}
                </div>
              )}

              <div className="space-y-3">
                <div id="google-signin-btn" className="w-full flex justify-center min-h-[40px]"></div>
                
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
