import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { api } from "../services/api";
import { Notification } from "../types";
import {
  LayoutDashboard,
  FileText,
  CheckSquare,
  Users,
  Briefcase,
  Layers,
  Settings,
  ShieldCheck,
  Search,
  Bell,
  Sun,
  Moon,
  LogOut,
  Menu,
  X,
  ChevronRight,
  TrendingUp,
  FileSpreadsheet,
  Package,
  Activity,
  HardDrive,
  CreditCard,
  CheckCircle,
  UserCog,
  Command,
} from "lucide-react";

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout, hasPermission, hasRole } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch in-app notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await api.get("/notifications?limit=5");
        setNotifications(response.data);
      } catch (err) {
        console.error("Failed to load notifications:", err);
      }
    };
    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 60000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const markAllRead = async () => {
    try {
      await api.post("/notifications/read-all");
      setNotifications(prev => prev.map(n => ({ ...n, status: "Read" })));
    } catch (err) {
      console.error("Error marking all read:", err);
    }
  };

  const buildSidebar = () => {
    const isVendor = hasRole("Vendor Portal") || hasRole("Vendor");
    const isEmployee = !isVendor && user?.roles?.some(r => r.role_name === "Employee");
    const isManager = hasRole("Manager");
    const isFinance = hasRole("Finance") || hasRole("Finance Manager");
    const isCFO = hasRole("CFO");
    const isCTO = hasRole("CTO");
    const isAdmin = hasRole("Admin") || hasRole("CEO");
    const isCEO = hasRole("CEO");
    const isProcurement = hasRole("Procurement") || hasRole("Procurement Officer") || hasRole("Procurement Manager");

    if (isVendor) {
      return [
        {
          title: "Vendor Operations",
          items: [
            { label: "Vendor Dashboard", path: "/vendor-portal", icon: LayoutDashboard, show: true },
            { label: "RFQs & Details", path: "/rfqs", icon: Briefcase, show: true },
            { label: "Purchase Orders", path: "/pos", icon: Package, show: true },
            { label: "Delivered Items", path: "/delivered-items", icon: Activity, show: true },
            { label: "Invoices", path: "/invoices", icon: CreditCard, show: true },
          ]
        }
      ];
    }

    type MenuItem = { label: string; path: string; icon: any; show: boolean };
    type MenuGroup = { title: string; items: MenuItem[] };

    const menuConfig: MenuGroup[] = [
      {
        title: "Overview",
        items: [
          { label: isCFO || isCTO ? "Executive Dashboard" : "Dashboard", path: "/", icon: LayoutDashboard, show: true },
        ],
      },
      {
        title: "My Requests",
        items: [
          { label: (isManager || isCEO) ? "Team Reimbursements" : "Employee Reimbursements", path: "/expenses", icon: FileText, show: isEmployee || isManager || isAdmin || isFinance || isCEO },
          { label: "Purchase Requisitions", path: "/prs", icon: FileText, show: isEmployee || isManager || isAdmin || isFinance || isCEO },
          { label: "My Assets", path: "/my-assets", icon: HardDrive, show: isEmployee || isManager || isAdmin || isFinance || isCEO },
        ]
      },
      {
        title: "Approvals",
        items: [
          { label: isCFO ? "Approval Queue" : "Pending Approvals", path: "/approvals", icon: CheckSquare, show: isManager || isFinance || isCFO || isAdmin || isCEO },
        ]
      },
      {
        title: "Financial Operations",
        items: [
          { label: "Expense Verification", path: "/expenses", icon: FileText, show: isFinance && !isAdmin },
          { label: "Reimbursements", path: "/expenses", icon: FileText, show: isCFO || isAdmin },
          { label: isCFO ? "Vendor Payments" : "Vendor Invoices", path: "/invoices", icon: CreditCard, show: isFinance || isCFO || isAdmin },
          { label: "Financial Analytics", path: "/analytics", icon: TrendingUp, show: isFinance || isCFO || isAdmin || isCEO },
          { label: "Reports", path: "/reports", icon: FileSpreadsheet, show: isFinance || isCFO || isAdmin || isCEO },
        ]
      },
      {
        title: "Procurement Cycle",
        items: [
          { label: "Cycle Dashboard", path: "/procurement-dashboard", icon: LayoutDashboard, show: isProcurement || isFinance || isCFO || isAdmin || isCEO },
          { label: "Vendors & Scores", path: "/vendors", icon: Users, show: isProcurement || isFinance || isCFO || isAdmin },
          { label: "RFQs & Invitations", path: "/rfqs", icon: Briefcase, show: isProcurement || isFinance || isCFO || isAdmin },
          { label: "Quotations Inbox", path: "/quotations", icon: Layers, show: isProcurement || isFinance || isCFO || isAdmin },
          { label: "Purchase Orders", path: "/pos", icon: Package, show: isProcurement || isFinance || isCFO || isAdmin },
          { label: "Assets Registry", path: "/assets", icon: HardDrive, show: isProcurement || isFinance || isCFO || isAdmin },
        ]
      },
      {
        title: "Intelligence & Platform",
        items: [
          { label: "Operational Analytics", path: "/analytics", icon: TrendingUp, show: isCTO },
          { label: "User Management", path: "/users", icon: UserCog, show: isAdmin },
        ]
      }
    ];

    const uniquePaths = new Set();
    const finalSidebar = menuConfig.map(group => {
      const filteredItems = group.items.filter(item => {
        if (!item.show) return false;
        if (uniquePaths.has(item.path)) return false;
        uniquePaths.add(item.path);
        return true;
      });
      return { ...group, items: filteredItems };
    }).filter(group => group.items.length > 0);

    return finalSidebar;
  };

  const sidebarItems = buildSidebar();

  const pathParts = location.pathname.split("/").filter(Boolean);
  const breadcrumbs = [
    { label: "Home", path: "/" },
    ...pathParts.map((part, index) => {
      const path = `/${pathParts.slice(0, index + 1).join("/")}`;
      const label = part.toUpperCase().replace("-", " ");
      return { label, path };
    }),
  ];

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="min-h-screen bg-background flex text-foreground transition-colors duration-300 antialiased selection:bg-primary/20">
      {/* Sidebar - Apple Glass Desktop */}
      <aside
        className="hidden md:flex flex-col border-r border-border/70 bg-card/75 backdrop-blur-2xl transition-all duration-300 w-64 shadow-apple-sm z-20"
      >
        {/* macOS Traffic Lights Header & Logo */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-border/50">
          <div className="flex items-center space-x-3 overflow-hidden">
            {/* macOS Dot Accents */}
            <div className="flex items-center gap-1.5 mr-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block" />
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
            </div>
            
            <div className="flex items-center gap-2 pl-1">
              <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-primary to-primary-hover flex items-center justify-center text-white font-bold text-xs shadow-apple-sm">
                ✦
              </div>
              <span className="font-bold text-sm tracking-tight font-sans text-foreground">
                ProcureSync
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto py-5 px-3 space-y-6">
          {sidebarItems.map((group, groupIdx) => {
            const visibleItems = group.items.filter(item => item.show);
            if (visibleItems.length === 0) return null;

            return (
              <div key={groupIdx} className="space-y-1">
                <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-3 mb-1.5 opacity-70">
                  {group.title}
                </span>
                <div className="space-y-0.5">
                  {visibleItems.map((item, itemIdx) => {
                    const isActive = location.pathname === item.path;
                    const Icon = item.icon;
                    return (
                      <Link
                        key={itemIdx}
                        to={item.path}
                        className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-200 group ${
                          isActive
                            ? "bg-primary text-white shadow-apple-sm shadow-primary/25"
                            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground active:scale-[0.98]"
                        }`}
                      >
                        <div className="flex items-center space-x-2.5">
                          <Icon className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 group-hover:scale-105 ${isActive ? "text-white" : "text-muted-foreground group-hover:text-foreground"}`} />
                          <span>{item.label}</span>
                        </div>
                        {isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-white/90 shadow-sm mr-0.5" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>
      </aside>

      {/* Sidebar - Mobile Apple Sheet */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex animate-fade-in">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-md" onClick={() => setIsMobileSidebarOpen(false)} />
          <aside className="relative w-72 bg-card/90 backdrop-blur-2xl text-card-foreground flex flex-col h-full border-r border-border p-4 animate-slide-right shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-border/50">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-xs">
                  ✦
                </div>
                <span className="font-bold text-sm tracking-tight">ProcureSync</span>
              </div>
              <button onClick={() => setIsMobileSidebarOpen(false)} className="w-8 h-8 rounded-full bg-muted/60 flex items-center justify-center text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto space-y-6 pt-4">
              {sidebarItems.map((group, groupIdx) => {
                const visibleItems = group.items.filter(item => item.show);
                if (visibleItems.length === 0) return null;
                return (
                  <div key={groupIdx} className="space-y-1.5">
                    <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-2">
                      {group.title}
                    </span>
                    <div className="space-y-1">
                      {visibleItems.map((item, itemIdx) => {
                        const isActive = location.pathname === item.path;
                        const Icon = item.icon;
                        return (
                          <Link
                            key={itemIdx}
                            to={item.path}
                            onClick={() => setIsMobileSidebarOpen(false)}
                            className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold ${
                              isActive ? "bg-primary text-white shadow-apple-sm shadow-primary/25" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <Icon className="w-4 h-4" />
                              <span>{item.label}</span>
                            </div>
                            {isActive && (
                              <span className="w-1.5 h-1.5 rounded-full bg-white mr-1" />
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* Main Apple Canvas Panel */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Apple Top Navigation Bar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-border/50 bg-card/65 backdrop-blur-xl sticky top-0 z-30 shadow-apple-sm">
          <div className="flex items-center space-x-4">
            <button onClick={() => setIsMobileSidebarOpen(true)} className="md:hidden p-2 rounded-full hover:bg-muted/60 text-muted-foreground hover:text-foreground transition-colors">
              <Menu className="w-5 h-5" />
            </button>
            
            {/* Apple Breadcrumbs */}
            <nav className="hidden sm:flex items-center space-x-2 text-xs font-semibold text-muted-foreground">
              {breadcrumbs.map((crumb, idx) => (
                <div key={idx} className="flex items-center space-x-2">
                  {idx > 0 && <ChevronRight className="w-3 h-3 opacity-50" />}
                  <Link to={crumb.path} className="hover:text-foreground transition-colors">
                    {crumb.label}
                  </Link>
                </div>
              ))}
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            {/* Apple Minimalist Quick Search */}
            <form onSubmit={handleGlobalSearch} className="hidden lg:flex items-center relative">
              <Search className="w-3.5 h-3.5 absolute left-3.5 text-muted-foreground/60" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-8 py-1.5 w-56 rounded-full bg-background/80 backdrop-blur-md border border-border/80 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary focus:w-72 transition-all duration-300 shadow-inner placeholder:text-muted-foreground/50"
              />
              <span className="absolute right-3 text-[10px] font-mono text-muted-foreground/50 flex items-center">
                <Command className="w-2.5 h-2.5 mr-0.5" />K
              </span>
            </form>

            {/* Dark / Light Toggle */}
            <button 
              onClick={toggleTheme} 
              className="p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/60 active:scale-95 transition-all"
              title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
            >
              {theme === "dark" ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-500" />}
            </button>

            {/* Notification Center */}
            <div className="relative">
              <button
                onClick={() => setIsNotificationOpen(!isNotificationOpen)}
                className="p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/60 relative transition-all active:scale-95"
              >
                <Bell className="w-4 h-4" />
                {notifications.some(n => n.status === "Unread") && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-pink rounded-full ring-2 ring-card" />
                )}
              </button>

              {isNotificationOpen && (
                <div className="absolute right-0 mt-3 w-80 apple-glass-heavy border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-50 animate-slide-up">
                  <div className="p-3.5 border-b border-border/50 flex items-center justify-between bg-card/40">
                    <span className="font-bold text-xs tracking-tight">Notifications</span>
                    <button onClick={markAllRead} className="text-[10px] text-primary font-bold hover:underline">
                      Mark all read
                    </button>
                  </div>
                  <div className="divide-y divide-border/40 max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-xs text-muted-foreground">No new alerts.</div>
                    ) : (
                      notifications.map((n) => (
                        <div key={n.notification_id} className={`p-3.5 text-xs transition-colors hover:bg-muted/40 ${n.status === "Unread" ? "bg-primary/5 font-medium" : ""}`}>
                          <p className="font-bold text-foreground/90">{n.title}</p>
                          <p className="text-muted-foreground text-[11px] mt-0.5">{n.message}</p>
                          <span className="text-[9px] text-muted-foreground/60 block mt-1">{new Date(n.created_at).toLocaleTimeString()}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Apple Role Pill Badge */}
            <div className="hidden md:flex items-center px-3 py-1 rounded-full bg-muted/60 border border-border/60">
              <span className="w-1.5 h-1.5 rounded-full bg-primary mr-2" />
              <span className="text-[11px] font-semibold text-foreground/90">
                {user?.roles && user.roles.length > 0 ? user.roles[0].role_name : "User"}
              </span>
            </div>

            {/* Apple User Profile Avatar */}
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-2 p-1 rounded-full hover:ring-2 hover:ring-primary/40 transition-all active:scale-95"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-primary-hover text-white font-bold flex items-center justify-center text-xs shadow-apple-sm border border-white/20">
                  {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || "U"}
                </div>
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 mt-3 w-56 apple-glass-heavy border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-50 animate-slide-up">
                  <div className="p-4 border-b border-border/50 bg-card/40">
                    <p className="font-bold text-sm tracking-tight">{user?.first_name} {user?.last_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                    <div className="mt-2 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/15 text-primary border border-primary/20">
                      {user?.roles[0]?.role_name || "Employee"}
                    </div>
                  </div>
                  <div className="p-1.5">
                    <button
                      onClick={logout}
                      className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-pink hover:bg-pink/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Log Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content Panel with Smooth Apple Spacing */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          {children}
        </main>

        {/* Apple Minimalist Footer */}
        <footer className="h-12 border-t border-border/50 px-6 flex items-center justify-between text-[11px] text-muted-foreground bg-card/30 backdrop-blur-md">
          <span>&copy; 2026 Enterprise Procurement Corp. Apple Human Interface Edition.</span>
          <div className="flex space-x-4">
            <a href="#" className="hover:text-foreground transition-colors">Support</a>
            <a href="#" className="hover:text-foreground transition-colors">Documentation</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
          </div>
        </footer>
      </div>
    </div>
  );
};
