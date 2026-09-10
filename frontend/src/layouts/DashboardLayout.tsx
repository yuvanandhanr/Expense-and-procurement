import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import { api } from "../services/api";
import { Notification, SearchResult } from "../types";
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
  CheckCircle2,
  CheckCheck,
  UserCog,
  Command,
  Clock,
  ArrowRight,
  Sparkles,
  History,
  Trash2,
  CornerDownLeft,
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
  
  // Search and dropdown state
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("procuresync_recent_searches");
      return saved ? JSON.parse(saved) : ["Expense Reports", "Office Supplies", "Vendor Invitations"];
    } catch {
      return ["Expense Reports", "Office Supplies", "Vendor Invitations"];
    }
  });

  const notificationRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Fetch in-app notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await api.get("/notifications?limit=20");
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

  // Click outside listener to close notification, profile, and search dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent | TouchEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(e.target as Node)) {
        setIsNotificationOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setIsProfileOpen(false);
      }
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, []);

  // Keyboard shortcut listener (Cmd+K / Ctrl+K or '/' to focus search, Escape to close)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen(true);
        if (searchInputRef.current) {
          searchInputRef.current.focus();
          searchInputRef.current.select();
        } else {
          navigate("/search");
        }
      }
      // '/' when not in input / textarea
      if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        setIsSearchOpen(true);
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      }
      // Escape key
      if (e.key === "Escape") {
        setIsNotificationOpen(false);
        setIsProfileOpen(false);
        setIsSearchOpen(false);
        searchInputRef.current?.blur();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [navigate]);

  // Live Debounced Search Query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearchLoading(false);
      return;
    }

    setSearchLoading(true);
    const timer = setTimeout(async () => {
      try {
        const response = await api.get(`/search?q=${encodeURIComponent(searchQuery.trim())}&limit=8`);
        setSearchResults(response.data || []);
      } catch (err) {
        console.error("Live search failed:", err);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const saveRecentSearch = (term: string) => {
    if (!term.trim()) return;
    const clean = term.trim();
    const updated = [clean, ...recentSearches.filter(s => s.toLowerCase() !== clean.toLowerCase())].slice(0, 6);
    setRecentSearches(updated);
    try {
      localStorage.setItem("procuresync_recent_searches", JSON.stringify(updated));
    } catch (e) {
      console.error("Error saving recent search", e);
    }
  };

  const removeRecentSearch = (term: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = recentSearches.filter(s => s !== term);
    setRecentSearches(updated);
    try {
      localStorage.setItem("procuresync_recent_searches", JSON.stringify(updated));
    } catch (e) {
      console.error("Error removing recent search", e);
    }
  };

  const clearRecentSearches = (e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentSearches([]);
    try {
      localStorage.removeItem("procuresync_recent_searches");
    } catch (e) {
      console.error("Error clearing recent searches", e);
    }
  };

  const markAllRead = async () => {
    try {
      await api.post("/notifications/read-all");
      setNotifications(prev => prev.map(n => ({ ...n, status: "Read" })));
    } catch (err) {
      console.error("Error marking all read:", err);
    }
  };

  const markAsRead = async (notificationId: number, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      await api.post(`/notifications/${notificationId}/read`);
      setNotifications(prev =>
        prev.map(n => (n.notification_id === notificationId ? { ...n, status: "Read" } : n))
      );
    } catch (err) {
      console.error("Error marking notification read:", err);
    }
  };

  // Quick navigation destinations
  const quickPages = [
    { label: "Employee Reimbursements", path: "/expenses", icon: FileText, category: "Claims" },
    { label: "Purchase Requisitions", path: "/prs", icon: FileText, category: "Requisitions" },
    { label: "Pending Approvals", path: "/approvals", icon: CheckSquare, category: "Approvals" },
    { label: "Vendor Management", path: "/vendors", icon: Users, category: "Procurement" },
    { label: "Requests For Quotations", path: "/rfqs", icon: Briefcase, category: "Sourcing" },
    { label: "Quotations Inbox", path: "/quotations", icon: Layers, category: "Sourcing" },
    { label: "Purchase Orders", path: "/pos", icon: Package, category: "Procurement" },
    { label: "Vendor Invoices", path: "/invoices", icon: CreditCard, category: "Finance" },
    { label: "Financial Analytics", path: "/analytics", icon: TrendingUp, category: "Analytics" },
  ];

  const matchedPages = searchQuery.trim()
    ? quickPages.filter(p => p.label.toLowerCase().includes(searchQuery.toLowerCase()) || p.category.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];

  const getEntityRoute = (entityType: string) => {
    const t = entityType.toUpperCase();
    if (t.includes("PR") || t.includes("REQUISITION")) return "/prs";
    if (t.includes("PO") || t.includes("ORDER")) return "/pos";
    if (t.includes("EXPENSE") || t.includes("REPORT") || t.includes("CLAIM")) return "/expenses";
    if (t.includes("VENDOR")) return "/vendors";
    if (t.includes("RFQ")) return "/rfqs";
    if (t.includes("INVOICE")) return "/invoices";
    if (t.includes("CONTRACT")) return "/contracts";
    if (t.includes("ASSET")) return "/assets";
    return `/search?q=${encodeURIComponent(searchQuery)}`;
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
          { label: "Purchase Requisitions", path: "/prs", icon: FileText, show: isEmployee || isManager || isAdmin || isFinance || isCEO || isCFO },
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
      saveRecentSearch(searchQuery.trim());
      setIsSearchOpen(false);
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-background flex text-foreground transition-colors duration-300 antialiased">
      {/* Sidebar - Apple Glass Desktop */}
      <aside
        className="hidden md:flex flex-col border-r border-border/70 bg-card/75 backdrop-blur-2xl transition-all duration-300 w-64 shadow-apple-sm z-20"
      >
        {/* Apple Sidebar Header & Logo */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-border/60">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#0071E3] to-[#0077ED] flex items-center justify-center text-white font-extrabold text-sm shadow-apple-sm shadow-primary/20">
              ✦
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-sm tracking-tight text-foreground leading-none">
                ProcureSync
              </span>
              <span className="text-[10px] font-semibold text-muted-foreground tracking-wider uppercase mt-1">
                Enterprise Suite
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
                            ? "bg-[#0071E3] text-white shadow-apple-sm shadow-primary/25"
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
                <div className="w-7 h-7 rounded-xl bg-[#0071E3] flex items-center justify-center text-white font-bold text-xs">
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
                              isActive ? "bg-[#0071E3] text-white shadow-apple-sm shadow-primary/25" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
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
            {/* Apple Minimalist Quick Search with Live Dropdown */}
            <div className="hidden lg:block relative" ref={searchContainerRef}>
              <form onSubmit={handleGlobalSearch} className="flex items-center relative">
                <Search className="w-3.5 h-3.5 absolute left-3.5 text-muted-foreground/60" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search anything (⌘K)..."
                  value={searchQuery}
                  onFocus={() => setIsSearchOpen(true)}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setIsSearchOpen(true);
                  }}
                  className="pl-9 pr-8 py-1.5 w-60 rounded-full bg-background/80 backdrop-blur-md border border-border/80 text-xs focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary focus:w-80 transition-all duration-300 shadow-inner placeholder:text-muted-foreground/50"
                />
                <span className="absolute right-3 text-[10px] font-mono text-muted-foreground/50 flex items-center">
                  <Command className="w-2.5 h-2.5 mr-0.5" />K
                </span>
              </form>

              {/* Search Dropdown (Recent Searches & Live Results) */}
              {isSearchOpen && (
                <div className="absolute left-0 mt-2.5 w-80 sm:w-96 apple-glass-heavy border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-50 animate-slide-up">
                  {/* If search query is empty: Show Recent Searches & Quick Nav */}
                  {!searchQuery.trim() ? (
                    <div className="p-3 space-y-3">
                      {/* Recent Searches Header */}
                      {recentSearches.length > 0 && (
                        <div>
                          <div className="flex items-center justify-between px-2 py-1">
                            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                              <History className="w-3 h-3 text-primary" /> Recent Searches
                            </span>
                            <button
                              type="button"
                              onClick={clearRecentSearches}
                              className="text-[10px] text-muted-foreground hover:text-pink transition-colors"
                            >
                              Clear all
                            </button>
                          </div>
                          <div className="flex flex-wrap gap-1.5 mt-1.5 px-1">
                            {recentSearches.map((term, idx) => (
                              <div
                                key={idx}
                                onClick={() => {
                                  setSearchQuery(term);
                                  saveRecentSearch(term);
                                  setIsSearchOpen(false);
                                  navigate(`/search?q=${encodeURIComponent(term)}`);
                                }}
                                className="group flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-muted/60 hover:bg-primary/15 hover:text-primary text-xs font-medium cursor-pointer transition-all border border-border/50 hover:border-primary/30"
                              >
                                <Clock className="w-3 h-3 opacity-60 text-muted-foreground group-hover:text-primary" />
                                <span>{term}</span>
                                <button
                                  type="button"
                                  onClick={(e) => removeRecentSearch(term, e)}
                                  className="w-3.5 h-3.5 rounded-full hover:bg-muted-foreground/20 flex items-center justify-center text-[10px] text-muted-foreground hover:text-foreground opacity-60 group-hover:opacity-100"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Quick Jump Shortcuts */}
                      <div>
                        <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wider px-2 py-1">
                          Quick Navigation
                        </span>
                        <div className="grid grid-cols-2 gap-1.5 mt-1 px-1">
                          {quickPages.slice(0, 6).map((page, idx) => {
                            const Icon = page.icon;
                            return (
                              <div
                                key={idx}
                                onClick={() => {
                                  setIsSearchOpen(false);
                                  navigate(page.path);
                                }}
                                className="flex items-center gap-2 p-2 rounded-xl hover:bg-muted/60 cursor-pointer transition-all border border-transparent hover:border-border/50 group"
                              >
                                <div className="p-1.5 rounded-lg bg-primary/10 text-primary group-hover:scale-105 transition-transform shrink-0">
                                  <Icon className="w-3.5 h-3.5" />
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-xs font-semibold text-foreground truncate">{page.label}</p>
                                  <p className="text-[10px] text-muted-foreground truncate">{page.category}</p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* If search query has text: Show live results & matching pages */
                    <div>
                      {/* Search state loading */}
                      {searchLoading && (
                        <div className="p-6 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
                          <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                          <span>Searching index...</span>
                        </div>
                      )}

                      {!searchLoading && (
                        <div className="divide-y divide-border/40 max-h-80 overflow-y-auto">
                          {/* Matched Pages */}
                          {matchedPages.length > 0 && (
                            <div className="p-2 bg-card/40">
                              <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wider px-2 py-1">
                                Pages & Features
                              </span>
                              {matchedPages.map((page, idx) => {
                                const Icon = page.icon;
                                return (
                                  <div
                                    key={idx}
                                    onClick={() => {
                                      saveRecentSearch(page.label);
                                      setIsSearchOpen(false);
                                      navigate(page.path);
                                    }}
                                    className="flex items-center justify-between p-2 rounded-xl hover:bg-primary/10 hover:text-primary cursor-pointer transition-all group"
                                  >
                                    <div className="flex items-center gap-2.5">
                                      <div className="p-1.5 rounded-lg bg-muted group-hover:bg-primary/20 text-muted-foreground group-hover:text-primary">
                                        <Icon className="w-3.5 h-3.5" />
                                      </div>
                                      <span className="text-xs font-bold text-foreground group-hover:text-primary">
                                        {page.label}
                                      </span>
                                    </div>
                                    <span className="text-[10px] font-semibold text-muted-foreground px-2 py-0.5 rounded-full bg-muted/60">
                                      {page.category}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          )}

                          {/* Matched Entity Records */}
                          {searchResults.length > 0 ? (
                            <div className="p-2">
                              <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wider px-2 py-1">
                                Records Found ({searchResults.length})
                              </span>
                              <div className="space-y-1">
                                {searchResults.map((result) => {
                                  const route = getEntityRoute(result.entity_type);
                                  return (
                                    <div
                                      key={result.index_id || result.entity_id}
                                      onClick={() => {
                                        saveRecentSearch(searchQuery);
                                        setIsSearchOpen(false);
                                        navigate(route);
                                      }}
                                      className="p-2.5 rounded-xl hover:bg-muted/60 cursor-pointer transition-all border border-transparent hover:border-border/50 group"
                                    >
                                      <div className="flex items-center justify-between gap-2">
                                        <p className="text-xs font-bold text-foreground group-hover:text-primary truncate">
                                          {result.title}
                                        </p>
                                        <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-primary/15 text-primary shrink-0">
                                          {result.entity_type}
                                        </span>
                                      </div>
                                      {result.content && (
                                        <p className="text-[11px] text-muted-foreground line-clamp-1 mt-0.5">
                                          {result.content}
                                        </p>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ) : (
                            matchedPages.length === 0 && (
                              <div className="p-6 text-center text-xs text-muted-foreground">
                                No direct matches found for "{searchQuery}".
                              </div>
                            )
                          )}
                        </div>
                      )}

                      {/* Footer: View All in Global Search */}
                      <div
                        onClick={handleGlobalSearch}
                        className="p-3 bg-muted/40 hover:bg-primary/10 border-t border-border/50 flex items-center justify-between cursor-pointer text-xs font-bold text-primary transition-colors group"
                      >
                        <span className="truncate">
                          Search all records for "<span className="text-foreground">{searchQuery}</span>"
                        </span>
                        <div className="flex items-center gap-1 text-[10px] text-muted-foreground group-hover:text-primary shrink-0 ml-2">
                          <CornerDownLeft className="w-3.5 h-3.5" /> Enter
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Dark / Light Toggle */}
            <button 
              onClick={toggleTheme} 
              className="p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/60 active:scale-95 transition-all"
              title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
            >
              {theme === "dark" ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-500" />}
            </button>

            {/* Notification Center */}
            {(() => {
              const unreadCount = notifications.filter(n => n.status === "Unread").length;
              return (
                <div className="relative" ref={notificationRef}>
                  <button
                    onClick={() => setIsNotificationOpen(!isNotificationOpen)}
                    className={`p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/60 relative transition-all active:scale-95 ${
                      isNotificationOpen ? "bg-muted/80 text-foreground ring-2 ring-primary/30" : ""
                    }`}
                    title="Notifications"
                  >
                    <Bell className="w-4 h-4" />
                    {unreadCount > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-gradient-to-r from-pink-500 to-rose-500 text-white text-[10px] font-extrabold flex items-center justify-center rounded-full shadow-md animate-pulse">
                        {unreadCount > 9 ? "9+" : unreadCount}
                      </span>
                    )}
                  </button>

                  {isNotificationOpen && (
                    <div className="absolute right-0 mt-3 w-84 sm:w-96 apple-glass-heavy border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-50 animate-slide-up">
                      <div className="p-3.5 border-b border-border/60 flex items-center justify-between bg-card/70 backdrop-blur-md">
                        <div className="flex items-center gap-2">
                          <span className="font-extrabold text-xs tracking-tight text-foreground">Notifications</span>
                          {unreadCount > 0 ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/15 text-primary border border-primary/25">
                              {unreadCount} unread
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-muted text-muted-foreground">
                              All caught up
                            </span>
                          )}
                        </div>
                        {unreadCount > 0 && (
                          <button
                            onClick={markAllRead}
                            className="text-[10px] text-primary font-bold hover:underline flex items-center gap-1 active:opacity-75 transition-opacity"
                          >
                            <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                          </button>
                        )}
                      </div>

                      <div className="divide-y divide-border/30 max-h-80 overflow-y-auto">
                        {notifications.length === 0 ? (
                          <div className="p-8 text-center text-xs text-muted-foreground">
                            <Bell className="w-8 h-8 mx-auto mb-2 opacity-30 text-muted-foreground" />
                            No notifications yet.
                          </div>
                        ) : (
                          notifications.map((n) => {
                            const isUnread = n.status === "Unread";
                            return (
                              <div
                                key={n.notification_id}
                                onClick={() => isUnread && markAsRead(n.notification_id)}
                                className={`p-3.5 text-xs transition-all duration-200 relative group flex gap-3 ${
                                  isUnread
                                    ? "bg-primary/8 dark:bg-primary/15 hover:bg-primary/12 border-l-4 border-primary cursor-pointer shadow-sm"
                                    : "bg-transparent hover:bg-muted/30 opacity-60 hover:opacity-100 border-l-4 border-transparent"
                                }`}
                              >
                                <div className="mt-0.5 shrink-0">
                                  {isUnread ? (
                                    <span className="w-2.5 h-2.5 rounded-full bg-primary ring-4 ring-primary/20 block animate-pulse mt-0.5" />
                                  ) : (
                                    <CheckCircle2 className="w-3.5 h-3.5 text-muted-foreground/40 mt-0.5" />
                                  )}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-start justify-between gap-1.5">
                                    <p className={`text-xs leading-snug ${isUnread ? "font-extrabold text-foreground" : "font-semibold text-muted-foreground"}`}>
                                      {n.title}
                                    </p>
                                    {isUnread && (
                                      <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.2 rounded bg-primary/20 text-primary shrink-0 tracking-wider">
                                        New
                                      </span>
                                    )}
                                  </div>
                                  <p className={`text-[11px] mt-0.5 leading-relaxed ${isUnread ? "text-foreground/90 font-medium" : "text-muted-foreground/75"}`}>
                                    {n.message}
                                  </p>
                                  <div className="flex items-center justify-between mt-2 text-[9px] text-muted-foreground/60 font-medium">
                                    <span>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    {isUnread && (
                                      <button
                                        onClick={(e) => markAsRead(n.notification_id, e)}
                                        className="opacity-0 group-hover:opacity-100 text-primary font-bold hover:underline transition-opacity flex items-center gap-1"
                                      >
                                        <CheckCircle className="w-2.5 h-2.5" /> Mark read
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Apple Role Pill Badge */}
            <div className="hidden md:flex items-center px-3 py-1 rounded-full bg-muted/60 border border-border/60">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0071E3] mr-2" />
              <span className="text-[11px] font-semibold text-foreground/90">
                {user?.roles && user.roles.length > 0 ? user.roles[0].role_name : "User"}
              </span>
            </div>

            {/* Apple User Profile Avatar */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-2 p-1 rounded-full hover:ring-2 hover:ring-[#0071E3]/40 transition-all active:scale-95"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#0071E3] to-[#0077ED] text-white font-bold flex items-center justify-center text-xs shadow-apple-sm border border-white/20">
                  {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || "U"}
                </div>
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 mt-3 w-56 apple-glass-heavy border border-border/80 rounded-2xl shadow-2xl overflow-hidden z-50 animate-slide-up">
                  <div className="p-4 border-b border-border/50 bg-card/40">
                    <p className="font-bold text-sm tracking-tight">{user?.first_name} {user?.last_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                    <div className="mt-2 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/15 text-primary border border-primary/20">
                      {user?.roles?.[0]?.role_name || "Employee"}
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
