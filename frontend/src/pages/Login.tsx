import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from "../components/ui";

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }
    setError("");
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Invalid login credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSignIn = async () => {
    const ssoEmail = prompt("Enter your Google Account email:", "y.raja@dataeko.ai");
    if (!ssoEmail) return;
    if (!ssoEmail.toLowerCase().endsWith("@dataeko.ai")) {
      setError("Only corporate @dataeko.ai Google accounts are permitted.");
      return;
    }
    setError("");
    setIsSubmitting(true);
    try {
      await login(ssoEmail, "sso_google_pass");
      navigate("/");
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Google authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4 relative overflow-hidden font-sans">
      {/* Background visual graphics */}
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-primary/20 blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-emerald-500/10 blur-[120px]" />

      <Card className="w-full max-w-md relative z-10 glass-panel border border-slate-800 bg-slate-950/80 shadow-2xl p-4">
        <CardHeader className="text-center pb-2 border-b-0">
          <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-bold text-2xl mx-auto shadow-lg shadow-primary/20">
            E
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-white mt-4">
            Sign In
          </CardTitle>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mt-1">
            Enterprise Procurement Suite
          </p>
        </CardHeader>
        <CardContent className="space-y-6 pt-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="email"
              type="email"
              label="Corporate Email Address"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-slate-900 border-slate-800 text-white placeholder:text-slate-500 focus:ring-primary"
            />
            <Input
              id="password"
              type="password"
              label="Security Credentials"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="bg-slate-900 border-slate-800 text-white placeholder:text-slate-500 focus:ring-primary"
            />

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full font-bold text-sm tracking-wider uppercase py-3"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Authenticating..." : "Access Platform"}
            </Button>
          </form>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-slate-800"></div>
            <span className="flex-shrink mx-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              Or Continue With
            </span>
            <div className="flex-grow border-t border-slate-800"></div>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={handleGoogleSignIn}
            className="w-full flex items-center justify-center border-slate-800 hover:bg-slate-900 text-white font-bold text-xs uppercase tracking-wider py-3"
            disabled={isSubmitting}
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Sign In with Google
          </Button>
          
          <div className="text-center text-xs text-slate-500 font-semibold uppercase tracking-wider">
            Restricted System access for authorized personnel only.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
export default Login;
