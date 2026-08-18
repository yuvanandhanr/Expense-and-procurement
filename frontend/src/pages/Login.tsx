import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from "../components/ui";
import { api } from "../services/api";
import toast from "react-hot-toast";
import { QRCodeSVG } from 'qrcode.react';

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
      if (window.google && activeTab === "employee") {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "542387192661-placeholder.apps.googleusercontent.com",
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

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden p-4">
      <Card className="w-full max-w-md relative z-10 glass-panel shadow-2xl p-4">
        <CardHeader className="text-center pb-2 border-b-0">
          <div className="w-[48px] h-[48px] rounded-[16px] gradient-accent flex items-center justify-center text-white font-bold text-2xl mx-auto shadow-lg shadow-violet/20">
            E
          </div>
          <CardTitle className="text-2xl font-bold font-display tracking-tight mt-4">
            Portal Access
          </CardTitle>
          <p className="text-[10.5px] font-semibold text-muted-foreground uppercase tracking-[1.6px] mt-1">
            Enterprise Procurement Suite
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6 pt-4">
          {/* Tab Selector */}
          <div className="grid grid-cols-2 p-1 bg-card-2 border border-border rounded-lg">
            <button
              type="button"
              onClick={() => { setActiveTab("employee"); setError(""); }}
              className={`py-2 text-xs font-bold rounded-md transition-all ${
                activeTab === "employee"
                  ? "gradient-accent text-white shadow"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Employee Login
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab("vendor"); setError(""); }}
              className={`py-2 text-xs font-bold rounded-md transition-all ${
                activeTab === "vendor"
                  ? "gradient-accent text-white shadow"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Vendor Login
            </button>
          </div>

          {activeTab === "employee" ? (
            <div className="space-y-6">
              <div className="text-center space-y-2">
                <h3 className="text-sm font-semibold text-foreground">Sign in using Google Workspace</h3>
                <p className="text-xs text-muted-foreground">Use your corporate @dataeko.ai credentials to authenticate securely.</p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <div id="google-signin-btn" className="w-full flex justify-center min-h-[40px] pb-2"></div>
                
                <div className="text-center">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Test Environments</span>
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full text-xs font-semibold py-2"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_y.raja@dataeko.ai" })}
                  >
                    Admin
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full text-xs font-semibold py-2"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_ceo@dataeko.ai" })}
                  >
                    CEO
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full text-xs font-semibold py-2"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_cfo@dataeko.ai" })}
                  >
                    CFO
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full text-xs font-semibold py-2"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_finance@dataeko.ai" })}
                  >
                    Finance Mgr
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full text-xs font-semibold py-2 col-span-2"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_manager@dataeko.ai" })}
                  >
                    Manager
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full text-xs font-semibold py-2 col-span-2"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_employee@dataeko.ai" })}
                  >
                    Employee
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={otpSent ? handleVerifyOtp : handleRequestOtp} className="space-y-4">
              <div className="text-center space-y-1">
                <h3 className="text-sm font-semibold text-foreground">Supplier Partner Access</h3>
                <p className="text-xs text-muted-foreground">
                  {mfaSetupData
                    ? "Set up your Authenticator App to secure your account."
                    : isMfaRequired 
                    ? "Enter the code from your Authenticator App." 
                    : "Enter your registered email to login."}
                </p>
              </div>

              {mfaSetupData && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center animate-in fade-in zoom-in duration-300">
                  <p className="text-xs text-slate-300 mb-4">
                    1. Scan this QR code using an Authenticator app (like Google Authenticator or Authy).
                  </p>
                  <div className="flex justify-center bg-white p-3 rounded-xl mx-auto w-fit mb-4">
                    <QRCodeSVG value={mfaSetupData.uri} size={130} />
                  </div>
                  <p className="text-xs text-slate-400">
                    2. Then enter the 6-digit code below to log in.
                  </p>
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
                className="bg-card-2 border-border text-foreground placeholder:text-muted-foreground"
              />

              {otpSent && (
                <div className="space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <Input
                    id="otp"
                    type="text"
                    label={isMfaRequired ? "Authenticator Code" : "One-Time Verification Code (OTP)"}
                    placeholder="Enter 6-digit code"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="bg-card-2 border-border text-foreground placeholder:text-muted-foreground text-center tracking-[0.5em] font-bold text-lg font-mono"
                  />
                </div>
              )}

              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full font-bold text-sm tracking-wider uppercase py-3"
                disabled={sendingOtp || isSubmitting}
              >
                {sendingOtp
                  ? "Checking Email..."
                  : isSubmitting
                  ? "Verifying..."
                  : otpSent
                  ? "Verify & Login"
                  : "Continue"}
              </Button>

              {otpSent && (
                <button
                  type="button"
                  onClick={() => { setOtpSent(false); setOtp(""); setMfaSetupData(null); }}
                  className="w-full text-center text-xs text-slate-400 hover:text-white underline"
                >
                  Change Email Address
                </button>
              )}
            </form>
          )}

          <div className="text-center text-[10px] text-muted-foreground font-semibold uppercase tracking-[1.6px] pt-2">
            Restricted System access for authorized personnel only.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
