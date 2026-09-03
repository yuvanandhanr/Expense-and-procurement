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
      // Poll every 60 seconds
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

    // Deduplicate any items that might appear multiple times due to role overlap (like expenses)
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

  // Derive breadcrumbs from path
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
    <div className="min-h-screen bg-background flex text-foreground transition-colors duration-300">
      {/* Sidebar - Desktop */}
      <aside
        className={`hidden md:flex flex-col border-r border-border bg-card/65 backdrop-blur-md transition-all duration-300 w-64`}
      >
        <div className="h-16 flex items-center justify-between px-6 border-b border-border/40">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-[34px] h-[34px] rounded-[11px] gradient-accent flex items-center justify-center text-white font-bold text-lg shadow-sm">
              E
            </div>
            <span className="font-bold text-md tracking-wider uppercase font-sans text-foreground">
              ProcureEnt
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-6">
          {sidebarItems.map((group, groupIdx) => {
            const visibleItems = group.items.filter(item => item.show);
            if (visibleItems.length === 0) return null;

            return (
              <div key={groupIdx} className="space-y-2">
                <span className="block text-[10.5px] font-semibold text-muted-foreground uppercase tracking-[1.6px] px-2 mb-2">
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
                        className={`flex items-center justify-between px-3 py-2.5 rounded-[10px] text-sm font-semibold transition-all duration-200 ${
                          isActive
                            ? "gradient-accent text-white shadow-lg shadow-violet/20"
                            : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <Icon className="w-5 h-5 flex-shrink-0" />
                          <span>{item.label}</span>
                        </div>
                        {isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-lime animate-pulse mr-1" />
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

      {/* Sidebar - Mobile Hamburger */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsMobileSidebarOpen(false)} />
          <aside className="relative w-64 bg-card text-card-foreground flex flex-col h-full border-r border-border p-4 animate-slide-right">
            <div className="flex items-center justify-between pb-6 border-b border-border/40">
              <span className="font-bold text-lg">PROCURMENT</span>
              <button onClick={() => setIsMobileSidebarOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-6 h-6" />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto space-y-6 pt-4">
              {sidebarItems.map((group, groupIdx) => {
                const visibleItems = group.items.filter(item => item.show);
                if (visibleItems.length === 0) return null;
                return (
                  <div key={groupIdx} className="space-y-2">
                    <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
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
                            className={`flex items-center justify-between px-3 py-2.5 rounded-[10px] text-sm font-semibold ${
                              isActive ? "gradient-accent text-white shadow-lg shadow-violet/20" : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <Icon className="w-5 h-5" />
                              <span>{item.label}</span>
                            </div>
                            {isActive && (
                              <span className="w-1.5 h-1.5 rounded-full bg-lime animate-pulse mr-1" />
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

      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-border/40 bg-card/65 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center space-x-4">
            <button onClick={() => setIsMobileSidebarOpen(true)} className="md:hidden text-muted-foreground hover:text-foreground">
              <Menu className="w-6 h-6" />
            </button>
            
            {/* Breadcrumb (Desktop) */}
            <nav className="hidden sm:flex items-center space-x-2 text-xs font-semibold text-muted-foreground">
              {breadcrumbs.map((crumb, idx) => (
                <div key={idx} className="flex items-center space-x-2">
                  {idx > 0 && <ChevronRight className="w-3.5 h-3.5" />}
                  <Link to={crumb.path} className="hover:text-foreground transition-colors">
                    {crumb.label}
                  </Link>
                </div>
              ))}
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            {/* Quick Search Input */}
            <form onSubmit={handleGlobalSearch} className="hidden lg:flex items-center relative">
              <Search className="w-4 h-4 absolute left-3 text-muted-foreground/60" />
              <input
                type="text"
                placeholder="Quick search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-1.5 w-60 rounded-full bg-card/50 backdrop-blur-md border border-border text-xs focus:outline-none focus:ring-1 focus:ring-violet focus:w-72 transition-all duration-300 shadow-sm"
              />
            </form>

            {/* Theme Toggle */}
            <button onClick={toggleTheme} className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
              {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* Notification Center */}
            <div className="relative">
              <button
                onClick={() => setIsNotificationOpen(!isNotificationOpen)}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent relative transition-colors"
              >
                <Bell className="w-5 h-5" />
                {notifications.some(n => n.status === "Unread") && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full" />
                )}
              </button>

              {isNotificationOpen && (
                <div className="absolute right-0 mt-3 w-80 bg-card border border-border rounded-xl shadow-xl overflow-hidden z-50 animate-slide-up">
                  <div className="p-4 border-b border-border flex items-center justify-between bg-accent/40">
                    <span className="font-bold text-xs uppercase tracking-wider">Notifications</span>
                    <button onClick={markAllRead} className="text-[10px] text-primary font-bold hover:underline">
                      Mark all read
                    </button>
                  </div>
                  <div className="divide-y divide-border max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-xs text-muted-foreground">No new alerts.</div>
                    ) : (
                      notifications.map((n) => (
                        <div key={n.notification_id} className={`p-4 text-xs transition-colors hover:bg-accent/30 ${n.status === "Unread" ? "bg-primary/5 font-medium" : ""}`}>
                          <p className="font-bold text-foreground/90">{n.title}</p>
                          <p className="text-muted-foreground mt-0.5">{n.message}</p>
                          <span className="text-[9px] text-muted-foreground/60 block mt-1">{new Date(n.created_at).toLocaleTimeString()}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Role Display */}
            <div className="hidden md:flex items-center border border-border rounded-lg bg-card overflow-hidden">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-3 border-r border-border bg-accent/30 flex items-center h-full">Role</span>
              <span className="bg-transparent text-xs font-semibold py-1.5 px-3">
                {user?.roles && user.roles.length > 0 ? user.roles[0].role_name : "User"}
              </span>
            </div>

            {/* User Profile Menu */}
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-2 p-1.5 rounded-full hover:bg-accent/50 transition-colors"
              >
                <div className="w-[34px] h-[34px] rounded-full gradient-accent text-white font-bold flex items-center justify-center text-sm shadow-sm border border-white/10">
                  {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || "U"}
                </div>
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 mt-3 w-56 bg-card border border-border rounded-xl shadow-xl overflow-hidden z-50 animate-slide-up">
                  <div className="p-4 border-b border-border">
                    <p className="font-bold text-sm">{user?.first_name} {user?.last_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-primary mt-1">
                      {user?.roles[0]?.role_name || "Employee"}
                    </p>
                  </div>
                  <div className="p-1">
                    <button
                      onClick={logout}
                      className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-semibold text-destructive hover:bg-destructive/10 transition-colors"
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

        {/* Content Panel */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          {children}
        </main>

        {/* Footer */}
        <footer className="h-12 border-t border-border/40 px-6 flex items-center justify-between text-xs text-muted-foreground bg-card/20 backdrop-blur-md">
          <span>&copy; 2026 Enterprise Procurement Corp. All rights reserved.</span>
          <div className="flex space-x-4">
            <a href="#" className="hover:text-foreground">Support</a>
            <a href="#" className="hover:text-foreground">Documentation</a>
          </div>
        </footer>
      </div>
    </div>
  );
};
