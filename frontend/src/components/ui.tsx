import React from "react";

// --- Button Component ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}) => {
  const baseStyle = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  
  const variants = {
    primary: "gradient-accent text-white hover:opacity-90 focus:ring-violet shadow-sm",
    secondary: "bg-card-2 text-foreground hover:bg-accent/50 focus:ring-violet border border-border",
    danger: "bg-pink text-white hover:opacity-90 focus:ring-pink shadow-sm",
    outline: "border border-border bg-transparent text-foreground hover:bg-accent/50 focus:ring-violet",
    ghost: "bg-transparent text-foreground hover:bg-accent/50 focus:ring-violet",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// --- Input Component ---
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className = "",
  id,
  ...props
}) => {
  return (
    <div className="w-full space-y-1">
      {label && (
        <label htmlFor={id} className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          {label}
        </label>
      )}
      <input
        id={id}
        className={`w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all duration-200 placeholder:text-muted-foreground/60 ${
          error ? "border-destructive focus:ring-destructive" : ""
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-destructive font-medium">{error}</p>}
    </div>
  );
};

// --- Select Component ---
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { label: string; value: string | number }[];
}

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  className = "",
  id,
  options,
  ...props
}) => {
  return (
    <div className="w-full space-y-1">
      {label && (
        <label htmlFor={id} className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          {label}
        </label>
      )}
      <select
        id={id}
        className={`w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all duration-200 ${
          error ? "border-destructive focus:ring-destructive" : ""
        } ${className}`}
        {...props}
      >
        <option value="" disabled>Select an option</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-destructive font-medium">{error}</p>}
    </div>
  );
};

// --- Card Components ---
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", children, ...props }) => (
  <div className={`rounded-lg border border-border bg-card text-foreground transition-all duration-200 ${className}`} {...props}>
    {children}
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", children, ...props }) => (
  <div className={`flex flex-col space-y-1.5 p-6 border-b border-border/40 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className = "", children, ...props }) => (
  <h3 className={`text-lg font-semibold leading-none tracking-tight ${className}`} {...props}>
    {children}
  </h3>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", children, ...props }) => (
  <div className={`p-6 ${className}`} {...props}>
    {children}
  </div>
);

// --- Badge Component ---
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "success" | "warning" | "error" | "info" | "neutral";
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "neutral",
  className = "",
  children,
  ...props
}) => {
  const styles = {
    success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20",
    error: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20",
    info: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20",
    neutral: "bg-muted text-muted-foreground border border-border",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full font-mono text-[10px] font-semibold uppercase tracking-wider transition-colors duration-200 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

// --- Modal/Dialog Component ---
interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  maxWidthClass?: string;
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children, maxWidthClass = "max-w-lg" }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className={`relative w-full ${maxWidthClass} bg-card text-card-foreground rounded-xl border border-border shadow-2xl p-6 overflow-hidden animate-slide-up`}>
        <div className="flex items-center justify-between pb-4 border-b border-border/40">
          <h2 className="text-lg font-bold font-display tracking-tight">{title}</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            &#x2715;
          </button>
        </div>
        <div className="mt-4 max-h-[70vh] overflow-y-auto pr-1">{children}</div>
      </div>
    </div>
  );
};

// --- Tabs Components ---
interface TabsProps {
  defaultValue: string;
  children: React.ReactNode;
  className?: string;
}

export const TabsContext = React.createContext<{
  activeTab: string;
  setActiveTab: (val: string) => void;
} | null>(null);

export const Tabs: React.FC<TabsProps> = ({ defaultValue, children, className = "" }) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={`space-y-4 ${className}`}>{children}</div>
    </TabsContext.Provider>
  );
};

export const TabsList: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = "",
}) => (
  <div className={`flex space-x-1 p-1 bg-muted rounded-lg border border-border ${className}`}>
    {children}
  </div>
);

export const TabsTrigger: React.FC<{ value: string; children: React.ReactNode; className?: string }> = ({
  value,
  children,
  className = "",
}) => {
  const ctx = React.useContext(TabsContext);
  if (!ctx) return null;
  const isActive = ctx.activeTab === value;

  return (
    <button
      onClick={() => ctx.setActiveTab(value)}
      className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${
        isActive
          ? "bg-card text-foreground shadow-sm border border-border/40"
          : "text-muted-foreground hover:text-foreground"
      } ${className}`}
    >
      {children}
    </button>
  );
};

export const TabsContent: React.FC<{ value: string; children: React.ReactNode }> = ({
  value,
  children,
}) => {
  const ctx = React.useContext(TabsContext);
  if (!ctx || ctx.activeTab !== value) return null;
  return <div className="space-y-4">{children}</div>;
};

// --- Loading Skeleton Component ---
export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", ...props }) => (
  <div className={`animate-pulse rounded bg-muted/60 ${className}`} {...props} />
);

export const HeroTimestamp: React.FC = () => {
  const [time, setTime] = React.useState(new Date());
  
  React.useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="text-[10px] font-mono text-muted-foreground font-semibold uppercase tracking-[1.6px] border border-border px-3 py-1.5 rounded-lg bg-card-2/50 shadow-sm whitespace-nowrap">
      AS OF {time.toLocaleString()}
    </div>
  );
};

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}> = ({ icon, title, description, actionLabel, actionHref, onAction }) => (
  <div className="p-10 flex flex-col items-center justify-center border-2 border-dashed border-border rounded-xl m-4 bg-card/20 backdrop-blur-sm">
    {icon && <div className="text-muted-foreground/50 mb-3">{icon}</div>}
    <p className="text-sm font-semibold text-foreground mb-1">{title}</p>
    <p className="text-xs text-muted-foreground mb-4">{description}</p>
    {(actionLabel || onAction) && (
      actionHref ? (
        <a href={actionHref} className="text-xs font-bold text-cyan hover:text-cyan/80 flex items-center transition-colors">
          {actionLabel} <span className="ml-1">&rarr;</span>
        </a>
      ) : (
        <button onClick={onAction} className="text-xs font-bold text-cyan hover:text-cyan/80 flex items-center transition-colors">
          {actionLabel} <span className="ml-1">&rarr;</span>
        </button>
      )
    )}
  </div>
);
