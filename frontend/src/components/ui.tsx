import React from "react";

// --- Apple Button Component ---
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
  const baseStyle = "inline-flex items-center justify-center font-medium rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-1 disabled:opacity-40 disabled:pointer-events-none active:scale-[0.98] select-none";
  
  const variants = {
    primary: "apple-button-primary bg-primary text-white hover:brightness-110 shadow-apple-sm",
    secondary: "bg-card-2/80 hover:bg-card-2 text-foreground border border-border backdrop-blur-md shadow-apple-sm hover:border-line-2",
    danger: "bg-pink text-white hover:brightness-110 shadow-apple-sm active:bg-pink/90",
    outline: "border border-border bg-transparent text-foreground hover:bg-card/60 backdrop-blur-sm",
    ghost: "bg-transparent text-foreground hover:bg-muted/40",
  };

  const sizes = {
    sm: "px-3.5 py-1.5 text-xs font-semibold tracking-tight",
    md: "px-5 py-2 text-sm font-semibold tracking-tight",
    lg: "px-6 py-3 text-base font-semibold tracking-tight",
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

// --- Apple Input Component ---
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
    <div className="w-full space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-1">
          {label}
        </label>
      )}
      <input
        id={id}
        className={`w-full px-3.5 py-2.5 text-sm rounded-xl bg-background/80 backdrop-blur-sm border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200 placeholder:text-muted-foreground/50 shadow-inner ${
          error ? "border-destructive focus:ring-destructive" : ""
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-destructive font-medium pl-1">{error}</p>}
    </div>
  );
};

// --- Apple Select Component ---
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
    <div className="w-full space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider pl-1">
          {label}
        </label>
      )}
      <select
        id={id}
        className={`w-full px-3.5 py-2.5 text-sm rounded-xl bg-background/80 backdrop-blur-sm border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200 ${
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
      {error && <p className="text-xs text-destructive font-medium pl-1">{error}</p>}
    </div>
  );
};

// --- Apple Liquid Glass Card Components ---
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", children, ...props }) => (
  <div className={`apple-card rounded-2xl text-foreground overflow-hidden ${className}`} {...props}>
    {children}
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", children, ...props }) => (
  <div className={`flex flex-col space-y-1.5 p-6 border-b border-border/50 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className = "", children, ...props }) => (
  <h3 className={`text-lg font-bold leading-none tracking-tight text-foreground ${className}`} {...props}>
    {children}
  </h3>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", children, ...props }) => (
  <div className={`p-6 ${className}`} {...props}>
    {children}
  </div>
);

// --- Apple Pill Badge Component ---
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
    success: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25",
    warning: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/25",
    error: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/25",
    info: "bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/25",
    neutral: "bg-muted/80 text-muted-foreground border border-border",
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-0.5 rounded-full text-[11px] font-semibold tracking-tight transition-all duration-200 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

// --- Apple Modal / macOS Dialog Component ---
interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  maxWidthClass?: string;
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children, maxWidthClass = "max-w-2xl" }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xl animate-fade-in">
      <div className={`relative w-full ${maxWidthClass} apple-glass-heavy text-card-foreground rounded-3xl border border-border/90 shadow-2xl p-6 sm:p-8 overflow-hidden animate-spring-in`}>
        {/* Apple Clean Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border/60">
          <h2 className="text-lg font-bold tracking-tight text-foreground">{title}</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-muted/60 text-muted-foreground hover:text-foreground hover:bg-muted transition-all active:scale-95 text-xs font-bold"
            title="Close"
          >
            ✕
          </button>
        </div>
        <div className="mt-5 max-h-[72vh] overflow-y-auto pr-1">{children}</div>
      </div>
    </div>
  );
};

// --- Apple Segmented Controls / Tabs ---
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
  <div className={`flex space-x-1 p-1 bg-muted/60 backdrop-blur-md rounded-full border border-border/60 ${className}`}>
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
      className={`flex-1 py-1.5 px-4 text-xs font-semibold rounded-full transition-all duration-200 ${
        isActive
          ? "bg-card text-foreground shadow-apple-sm border border-border/50"
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
  return <div className="space-y-4 animate-fade-in">{children}</div>;
};

// --- Loading Skeleton Component ---
export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = "", ...props }) => (
  <div className={`animate-pulse rounded-xl bg-muted/50 ${className}`} {...props} />
);

export const HeroTimestamp: React.FC = () => {
  const [time, setTime] = React.useState(new Date());
  
  React.useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="text-[11px] font-mono text-muted-foreground font-semibold uppercase tracking-wider border border-border/80 px-3.5 py-1.5 rounded-full bg-card/60 backdrop-blur-md shadow-apple-sm whitespace-nowrap">
      {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })} • {time.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
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
  <div className="p-12 flex flex-col items-center justify-center border border-dashed border-border/80 rounded-2xl m-4 bg-card/30 backdrop-blur-md text-center">
    {icon && <div className="text-muted-foreground/60 mb-3.5 p-3 rounded-2xl bg-muted/40">{icon}</div>}
    <p className="text-base font-bold text-foreground mb-1">{title}</p>
    <p className="text-xs text-muted-foreground max-w-sm mb-5 leading-relaxed">{description}</p>
    {(actionLabel || onAction) && (
      actionHref ? (
        <a href={actionHref} className="apple-button-primary px-5 py-2 text-xs">
          {actionLabel}
        </a>
      ) : (
        <Button onClick={onAction} size="sm" variant="primary">
          {actionLabel}
        </Button>
      )
    )}
  </div>
);
