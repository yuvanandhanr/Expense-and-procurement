import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from "../components/ui";
import { api } from "../services/api";
import toast from "react-hot-toast";

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
      await api.post("/auth/vendor/otp-request", { email: vendorEmail });
      setOtpSent(true);
      toast.success("Verification OTP code sent to your email!");
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
      setTimeout(() => {
        navigate("/vendor-portal");
      }, 100);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid or expired OTP code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-950 overflow-hidden font-sans p-4">
      {/* Background graphics */}
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-primary/20 blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-emerald-500/10 blur-[120px]" />

      <Card className="w-full max-w-md relative z-10 glass-panel border border-slate-800 bg-slate-950/80 shadow-2xl p-4">
        <CardHeader className="text-center pb-2 border-b-0">
          <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-bold text-2xl mx-auto shadow-lg shadow-primary/20">
            E
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-white mt-4">
            Portal Access
          </CardTitle>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mt-1">
            Enterprise Procurement Suite
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6 pt-4">
          {/* Tab Selector */}
          <div className="grid grid-cols-2 p-1 bg-slate-900 border border-slate-800 rounded-lg">
            <button
              type="button"
              onClick={() => { setActiveTab("employee"); setError(""); }}
              className={`py-2 text-xs font-bold rounded-md transition-all ${
                activeTab === "employee"
                  ? "bg-primary text-primary-foreground shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Employee Login
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab("vendor"); setError(""); }}
              className={`py-2 text-xs font-bold rounded-md transition-all ${
                activeTab === "vendor"
                  ? "bg-primary text-primary-foreground shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Vendor Login
            </button>
          </div>

          {activeTab === "employee" ? (
            <div className="space-y-6">
              <div className="text-center space-y-2">
                <h3 className="text-sm font-semibold text-slate-200">Sign in using Google Workspace</h3>
                <p className="text-xs text-slate-400">Use your corporate @dataeko.ai credentials to authenticate securely.</p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
                  {error}
                </div>
              )}

              <div className="space-y-3">
                <div id="google-signin-btn" className="w-full flex justify-center min-h-[40px]"></div>
                {import.meta.env.DEV && (
                  <Button
                    type="button"
                    className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold py-2 hover:bg-slate-800 hover:text-white"
                    onClick={() => handleCredentialResponse({ credential: "mock_google_y.raja@dataeko.ai" })}
                  >
                    Mock Google SSO (Dev Only)
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <form onSubmit={otpSent ? handleVerifyOtp : handleRequestOtp} className="space-y-4">
              <div className="text-center space-y-1">
                <h3 className="text-sm font-semibold text-slate-200">Supplier Partner Access</h3>
                <p className="text-xs text-slate-400">Enter your registered email to receive a secure login code.</p>
              </div>

              <Input
                id="vendorEmail"
                type="email"
                label="Registered Vendor Email"
                placeholder="vendor@company.com"
                value={vendorEmail}
                onChange={(e) => setVendorEmail(e.target.value)}
                disabled={otpSent}
                className="bg-slate-900 border-slate-800 text-white placeholder:text-slate-500 focus:ring-primary"
              />

              {otpSent && (
                <div className="space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                  <Input
                    id="otp"
                    type="text"
                    label="One-Time Verification Code (OTP)"
                    placeholder="Enter 6-digit OTP code"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="bg-slate-900 border-slate-800 text-white placeholder:text-slate-500 focus:ring-primary text-center tracking-[0.5em] font-bold text-lg"
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
                  ? "Sending Code..."
                  : isSubmitting
                  ? "Verifying OTP..."
                  : otpSent
                  ? "Verify & Enter Portal"
                  : "Send OTP Verification"}
              </Button>

              {otpSent && (
                <button
                  type="button"
                  onClick={() => { setOtpSent(false); setOtp(""); }}
                  className="w-full text-center text-xs text-slate-400 hover:text-white underline"
                >
                  Change Email Address
                </button>
              )}
            </form>
          )}

          <div className="text-center text-xs text-slate-500 font-semibold uppercase tracking-wider pt-2">
            Restricted System access for authorized personnel only.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
