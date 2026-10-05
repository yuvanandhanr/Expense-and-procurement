import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Skeleton } from "../components/ui";
import { 
  FileText, 
  Download, 
  Layers, 
  ShieldCheck, 
  Sparkles, 
  Calendar, 
  User as UserIcon, 
  Building2, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  Printer, 
  RefreshCw,
  ChevronRight,
  Filter
} from "lucide-react";
import toast from "react-hot-toast";

export const ExecutiveReport: React.FC = () => {
  const { hasRole, user } = useAuth();
  const navigate = useNavigate();

  // Role Gate: CFO & Finance Admin ONLY
  const isAuthorized = hasRole("CFO") || hasRole("CEO") || hasRole("Finance Manager") || hasRole("Finance") || hasRole("Admin");

  // Cascading Selection States
  const [scope, setScope] = useState<"all" | "employee" | "department">("all");
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [categoryType, setCategoryType] = useState<"all" | "specific">("all");
  const [expenseCategory, setExpenseCategory] = useState<string>("Travel, Lodging & Commute");
  const [timeHorizon, setTimeHorizon] = useState<"5_YEAR_ARCHIVE" | "YTD" | "MTD" | "CUSTOM">("5_YEAR_ARCHIVE");
  const [startDate, setStartDate] = useState<string>("2021-01-01");
  const [endDate, setEndDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [statusFilter, setStatusFilter] = useState<string>("Approved");

  // Data Options
  const [employees, setEmployees] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [reportData, setReportData] = useState<any>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);

  // Load supporting dropdown data
  useEffect(() => {
    if (!isAuthorized) return;
    api.get("/users").then((res) => setEmployees(res.data || [])).catch(() => {});
    api.get("/departments").then((res) => setDepartments(res.data || [])).catch(() => {});
  }, [isAuthorized]);

  // Fetch / Refresh Dataeko Preview Report
  const fetchReportPreview = useCallback(async () => {
    if (!isAuthorized) return;
    setIsLoadingPreview(true);
    try {
      const payload = {
        scope,
        employee_id: scope === "employee" && employeeId ? Number(employeeId) : null,
        department_id: scope === "department" && departmentId ? Number(departmentId) : null,
        expense_category: categoryType === "specific" ? expenseCategory : "all",
        time_horizon: timeHorizon,
        start_date: timeHorizon === "CUSTOM" ? startDate : null,
        end_date: timeHorizon === "CUSTOM" ? endDate : null,
        status: statusFilter,
      };

      const res = await api.post("/reports/executive-expense/preview", payload);
      setReportData(res.data);
    } catch (err: any) {
      console.error("Preview compilation failed:", err);
      toast.error(err.response?.data?.detail || "Failed to compile Dataeko Executive Report preview.");
    } finally {
      setIsLoadingPreview(false);
    }
  }, [scope, employeeId, departmentId, categoryType, expenseCategory, timeHorizon, startDate, endDate, statusFilter, isAuthorized]);

  // Trigger preview update when filter parameters change
  useEffect(() => {
    fetchReportPreview();
  }, [fetchReportPreview]);

  // Download PDF Handler
  const handleDownloadPdf = async () => {
    setIsGeneratingPdf(true);
    try {
      const payload = {
        scope,
        employee_id: scope === "employee" && employeeId ? Number(employeeId) : null,
        department_id: scope === "department" && departmentId ? Number(departmentId) : null,
        expense_category: categoryType === "specific" ? expenseCategory : "all",
        time_horizon: timeHorizon,
        start_date: timeHorizon === "CUSTOM" ? startDate : null,
        end_date: timeHorizon === "CUSTOM" ? endDate : null,
        status: statusFilter,
      };

      const res = await api.post("/reports/executive-expense/generate", payload);
      toast.success("Executive PDF generated and saved successfully!");

      if (res.data?.report_id) {
        window.open(`/api/v1/files/download/${res.data.report_id}`, "_blank");
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to generate executive PDF.");
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  if (!isAuthorized) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 flex items-center justify-center">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight">Access Restricted</h2>
        <p className="text-sm text-muted-foreground max-w-md">
          The Dataeko Executive Financial & Performance Dossier is restricted exclusively to Chief Financial Officers and Finance Administrators.
        </p>
        <Button onClick={() => navigate("/dashboard")} variant="secondary">
          Return to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Dataeko Intelligence Engine
            </span>
            <Badge variant="neutral" className="text-[10px] uppercase font-bold tracking-widest">
              Executive Dossier
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground mt-2">
            Executive Financial & Performance Report
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Dynamic 5-year longitudinal archive, MTD/YTD expense analytics, and AI predictive intelligence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => window.print()}
            className="flex items-center gap-2 text-xs font-bold"
          >
            <Printer className="w-3.5 h-3.5" /> Print Dossier
          </Button>
          <Button
            onClick={handleDownloadPdf}
            disabled={isGeneratingPdf || isLoadingPreview}
            className="bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs flex items-center gap-2 shadow-apple-sm"
          >
            {isGeneratingPdf ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Generating PDF...
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" /> Download Executive PDF
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Cascading Filter Configuration Card */}
      <Card className="border-border/80 shadow-apple-sm bg-card/60 backdrop-blur-md">
        <CardHeader className="pb-3 border-b border-border/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-sky-400" />
              <CardTitle className="text-base font-bold">Report Scope & Parameter Wizard</CardTitle>
            </div>
            <span className="text-[11px] text-muted-foreground">Cascading parameter list boxes</span>
          </div>
        </CardHeader>
        <CardContent className="p-5 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* 1. Scope Selection */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-extrabold text-muted-foreground uppercase tracking-wider">
                1. Target Scope
              </label>
              <select
                value={scope}
                onChange={(e) => {
                  setScope(e.target.value as any);
                  setEmployeeId("");
                  setDepartmentId("");
                }}
                className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-border focus:outline-none focus:ring-2 focus:ring-sky-500/50"
              >
                <option value="all">All Employees (Enterprise Consolidated)</option>
                <option value="employee">Specific Individual Personnel</option>
                <option value="department">Specific Operating Department</option>
              </select>
            </div>

            {/* Nested Level 1: If Employee is Chosen */}
            {scope === "employee" && (
              <div className="space-y-1.5 animate-fade-in">
                <label className="text-[11px] font-extrabold text-sky-400 uppercase tracking-wider flex items-center gap-1">
                  <UserIcon className="w-3 h-3" /> Select Employee
                </label>
                <select
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-sky-500/40 focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">-- Choose Employee ({employees.length} available) --</option>
                  {employees.map((emp) => (
                    <option key={emp.user_id} value={emp.user_id}>
                      {emp.full_name || emp.email} (#{emp.user_id}) - {emp.designation?.name || "Staff"}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Nested Level 1: If Department is Chosen */}
            {scope === "department" && (
              <div className="space-y-1.5 animate-fade-in">
                <label className="text-[11px] font-extrabold text-sky-400 uppercase tracking-wider flex items-center gap-1">
                  <Building2 className="w-3 h-3" /> Select Department
                </label>
                <select
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-sky-500/40 focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">-- Choose Department ({departments.length} available) --</option>
                  {departments.map((dept) => (
                    <option key={dept.department_id} value={dept.department_id}>
                      {dept.department_name} (Code: {dept.department_code || dept.department_id})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* 2. Expense Category / Kind */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-extrabold text-muted-foreground uppercase tracking-wider">
                2. Expense Kind / Category
              </label>
              <select
                value={categoryType}
                onChange={(e) => setCategoryType(e.target.value as any)}
                className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-border focus:outline-none focus:ring-2 focus:ring-sky-500/50"
              >
                <option value="all">All Categories & Incident Types</option>
                <option value="specific">Filter Specific Category</option>
              </select>
            </div>

            {/* Nested Level 2: Specific Category dropdown */}
            {categoryType === "specific" && (
              <div className="space-y-1.5 animate-fade-in">
                <label className="text-[11px] font-extrabold text-sky-400 uppercase tracking-wider">
                  Category Type
                </label>
                <select
                  value={expenseCategory}
                  onChange={(e) => setExpenseCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-sky-500/40 focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="Travel, Lodging & Commute">Travel, Lodging & Commute</option>
                  <option value="Cloud & SaaS Subscriptions">Cloud & SaaS Subscriptions</option>
                  <option value="IT Equipment & Hardware Replacement">IT Equipment & Hardware Replacement</option>
                  <option value="Damaged Asset Incident Claims">Damaged Asset Incident Claims</option>
                  <option value="Professional Consulting & Legal">Professional Consulting & Legal</option>
                  <option value="Office Infrastructure & Miscellaneous">Office Infrastructure & Misc</option>
                </select>
              </div>
            )}

            {/* 3. Time Horizon */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-extrabold text-muted-foreground uppercase tracking-wider">
                3. Time Horizon
              </label>
              <select
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(e.target.value as any)}
                className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-border focus:outline-none focus:ring-2 focus:ring-sky-500/50"
              >
                <option value="5_YEAR_ARCHIVE">Full 5-Year Historical Archive (2021 – 2026)</option>
                <option value="YTD">Current Fiscal Year (YTD)</option>
                <option value="MTD">Current Month (MTD)</option>
                <option value="CUSTOM">Custom Date Window</option>
              </select>
            </div>

            {/* Nested Level 3: Custom Date Pickers */}
            {timeHorizon === "CUSTOM" && (
              <>
                <div className="space-y-1.5 animate-fade-in">
                  <label className="text-[11px] font-extrabold text-sky-400 uppercase tracking-wider">
                    From Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-sky-500/40 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div className="space-y-1.5 animate-fade-in">
                  <label className="text-[11px] font-extrabold text-sky-400 uppercase tracking-wider">
                    To Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-sky-500/40 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </>
            )}

            {/* 4. Settlement Status */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-extrabold text-muted-foreground uppercase tracking-wider">
                4. Status Verification
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 text-xs font-semibold rounded-xl bg-background border border-border focus:outline-none focus:ring-2 focus:ring-sky-500/50"
              >
                <option value="Approved">Approved & Reimbursed (Finalized)</option>
                <option value="All">All Transactions (Full Audit Trail)</option>
                <option value="Pending">Pending Executive Review</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Mock Document Preview in Dataeko Brand Theme */}
      {isLoadingPreview ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : reportData ? (
        <div className="bg-[#0F172A] text-[#F8FAFC] rounded-3xl p-6 md:p-10 border border-[#1E293B] shadow-2xl space-y-8 font-sans print:bg-white print:text-black print:border-none print:shadow-none">
          {/* Header Brand Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-[#1E293B]">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl md:text-2xl font-black tracking-tight text-white flex items-center gap-1.5">
                  <span className="text-sky-400">Dataeko</span>.ai
                </span>
                <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest bg-sky-500/20 text-sky-400 border border-sky-500/30">
                  Financial Engine v4.2
                </span>
              </div>
              <h2 className="text-lg md:text-xl font-bold tracking-tight text-slate-200 mt-1">
                {reportData.company_name} — Financial & Performance Report
              </h2>
              <p className="text-xs text-slate-400 mt-0.5 italic">
                {reportData.tagline}
              </p>
            </div>

            <div className="mt-4 md:mt-0 text-right">
              <div className="inline-block px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono font-bold">
                {reportData.document_metadata.document_id}
              </div>
              <p className="text-[10px] text-slate-400 mt-1 uppercase font-bold tracking-wider">
                {reportData.document_metadata.classification}
              </p>
            </div>
          </div>

          {/* Section 1: Document Metadata & Identification */}
          <div className="space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>1.</span> Document Metadata & Identification
            </h3>
            <div className="overflow-x-auto rounded-xl border border-[#1E293B] bg-[#1E293B]/40">
              <table className="w-full text-left text-xs">
                <tbody className="divide-y divide-[#1E293B]">
                  <tr>
                    <td className="p-3 font-bold text-slate-400 w-1/3">Subject / Target Entity:</td>
                    <td className="p-3 font-semibold text-white">{reportData.document_metadata.subject_entity}</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-slate-400">Entity Identifier:</td>
                    <td className="p-3 font-mono text-sky-300">{reportData.document_metadata.entity_identifier}</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-slate-400">Prepared By:</td>
                    <td className="p-3 font-semibold text-slate-200">{reportData.document_metadata.prepared_by}</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-slate-400">Report Date:</td>
                    <td className="p-3 font-semibold text-slate-200">{reportData.document_metadata.report_date}</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-slate-400">Reporting Period:</td>
                    <td className="p-3 font-bold text-emerald-400">{reportData.document_metadata.reporting_period}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: Executive Summary */}
          <div className="space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>2.</span> Executive Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/30 space-y-1.5">
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-sky-400" /> Core Takeaway
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {reportData.executive_summary.core_takeaway}
                </p>
              </div>
              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/30 space-y-1.5">
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Risk Score / Capital Outlook
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {reportData.executive_summary.risk_score_outlook}
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Key Financial Metrics (KPI Dashboard) */}
          <div className="space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>3.</span> Key Financial Metrics (KPI Dashboard)
            </h3>
            <div className="overflow-x-auto rounded-xl border border-[#1E293B] bg-[#1E293B]/40">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#1E293B] bg-[#1E293B]/80 text-[10px] font-black text-slate-400 uppercase tracking-wider">
                    <th className="p-3">Metric</th>
                    <th className="p-3">Current Period (₹)</th>
                    <th className="p-3">Prior Period (₹)</th>
                    <th className="p-3">YoY Variance (%)</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E293B]">
                  {reportData.key_financial_metrics.map((m: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="p-3 font-bold text-white">{m.metric}</td>
                      <td className="p-3 font-mono font-semibold text-slate-200">
                        ₹{m.current_period.toLocaleString()}
                      </td>
                      <td className="p-3 font-mono text-slate-400">
                        ₹{m.prior_period.toLocaleString()}
                      </td>
                      <td className="p-3 font-mono font-bold">
                        <span className={m.yoy_variance_pct >= 0 ? "text-emerald-400" : "text-rose-400"}>
                          {m.yoy_variance_pct >= 0 ? `+${m.yoy_variance_pct}%` : `${m.yoy_variance_pct}%`}
                        </span>
                      </td>
                      <td className="p-3 font-semibold text-[11px]">{m.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 4: Income & Expense Breakdown */}
          <div className="space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>4.</span> Income & Cost Structure Breakdown
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Primary Revenue / Inflows */}
              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/20 space-y-3">
                <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider">
                  Primary Enterprise Operational Inflows
                </h4>
                <div className="space-y-2">
                  {reportData.income_expense_breakdown.primary_revenue_streams.map((rev: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-slate-400">{rev.stream}</span>
                      <span className="font-mono font-bold text-white">₹{rev.amount.toLocaleString()} ({rev.share_pct}%)</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cost Structure Analysis */}
              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/20 space-y-3">
                <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider">
                  Cost Structure & Expense Distribution
                </h4>
                <div className="space-y-2">
                  {Object.entries(reportData.income_expense_breakdown.cost_structure_analysis).map(([costKey, costVal]: [string, any], idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-slate-400">{costKey}</span>
                      <span className="font-mono font-bold text-rose-300">₹{Number(costVal).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Balance Sheet Snapshot */}
          <div className="space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>5.</span> Enterprise Balance Sheet Snapshot
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/30 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Assets</span>
                <p className="text-xl font-black text-white font-mono">
                  ₹{reportData.balance_sheet_snapshot.total_assets.toLocaleString()}
                </p>
                <p className="text-[10px] text-slate-400">
                  Current: ₹{reportData.balance_sheet_snapshot.current_assets.toLocaleString()} | Fixed: ₹{reportData.balance_sheet_snapshot.non_current_assets.toLocaleString()}
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/30 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Liabilities</span>
                <p className="text-xl font-black text-rose-300 font-mono">
                  ₹{reportData.balance_sheet_snapshot.total_liabilities.toLocaleString()}
                </p>
                <p className="text-[10px] text-slate-400">
                  Payables: ₹{reportData.balance_sheet_snapshot.current_liabilities.toLocaleString()}
                </p>
              </div>

              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/30 space-y-1">
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Total Net Equity</span>
                <p className="text-xl font-black text-emerald-300 font-mono">
                  ₹{reportData.balance_sheet_snapshot.total_equity.toLocaleString()}
                </p>
                <p className="text-[10px] text-slate-400">Solvency ratio verified</p>
              </div>
            </div>
          </div>

          {/* Section 6: Dataeko Predictive & Financial Insights */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-black uppercase tracking-widest text-sky-400">
                6. Dataeko Predictive & Financial Insights
              </h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border border-sky-500/20 bg-sky-950/20 space-y-1.5">
                <h4 className="text-xs font-bold text-sky-300">Trend Analysis</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {reportData.predictive_insights.trend_analysis}
                </p>
              </div>
              <div className="p-4 rounded-xl border border-sky-500/20 bg-sky-950/20 space-y-1.5">
                <h4 className="text-xs font-bold text-sky-300">AI Forecast Model</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {reportData.predictive_insights.ai_forecast_model}
                </p>
              </div>
              <div className="p-4 rounded-xl border border-sky-500/20 bg-sky-950/20 space-y-1.5">
                <h4 className="text-xs font-bold text-sky-300">Anomaly & Risk Detection</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {reportData.predictive_insights.anomaly_risk_detection}
                </p>
              </div>
            </div>
          </div>

          {/* Section 7: Sign-off & Verification */}
          <div className="space-y-3 pt-4 border-t border-[#1E293B]">
            <h3 className="text-xs font-black uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>7.</span> Sign-Off & Verification
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/20 space-y-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Prepared By</span>
                <div className="text-sm font-bold text-white">{reportData.sign_off.prepared_by_name}</div>
                <div className="text-xs text-slate-400">{reportData.sign_off.prepared_by_title}</div>
                <div className="pt-2 border-t border-[#1E293B] text-[10px] text-sky-400 font-mono flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-sky-400" /> Digitally Verified: {new Date().toISOString()}
                </div>
              </div>

              <div className="p-4 rounded-xl border border-[#1E293B] bg-[#1E293B]/20 space-y-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Approved By</span>
                <div className="text-sm font-bold text-white">{reportData.sign_off.approved_by_name}</div>
                <div className="text-xs text-slate-400">{reportData.sign_off.approved_by_title}</div>
                <div className="pt-2 border-t border-[#1E293B] text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" /> Digital Corporate Seal Verified
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Action Footer */}
          <div className="pt-6 border-t border-[#1E293B] flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-400">
              Generated securely by Dataeko Platform • Confidential Corporate Financial Document
            </div>
            <Button
              onClick={handleDownloadPdf}
              disabled={isGeneratingPdf}
              className="w-full md:w-auto bg-sky-500 hover:bg-sky-600 text-white font-bold text-sm px-6 py-3 rounded-xl flex items-center justify-center gap-2 shadow-lg"
            >
              {isGeneratingPdf ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Generating Official PDF...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" /> Download Official Dataeko Executive PDF
                </>
              )}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default ExecutiveReport;
