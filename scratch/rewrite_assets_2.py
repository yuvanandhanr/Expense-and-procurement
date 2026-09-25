import re

with open("scratch/Assets.tsx", "r") as f:
    content = f.read()

# 1. Add helper functions and counts before filteredAssets
helper_funcs = """
  const isAssignedAsset = (a: Asset) => (a.assigned_to_name && a.assigned_to_name !== "Unassigned") || a.status === "Assigned" || a.status === "Transferred";
  const isOutOfServiceAsset = (a: Asset) => ["Out of Service", "Retired", "Damaged", "Disposed", "Lost", "Under Maintenance", "Reported"].includes(a.status);
  const isUnassignedAsset = (a: Asset) => !isAssignedAsset(a) && !isOutOfServiceAsset(a);

  // We only count based on the current category filter so the counts are accurate for the current view
  const categoryFilteredAssets = assets.filter(a => activeCategory === "All Categories" || a.category === activeCategory);
  const counts = {
    "All Assets": categoryFilteredAssets.length,
    "Assigned": categoryFilteredAssets.filter(isAssignedAsset).length,
    "Unassigned": categoryFilteredAssets.filter(isUnassignedAsset).length,
    "Out of Service": categoryFilteredAssets.filter(isOutOfServiceAsset).length,
  };

  const filteredAssigneeUsers = users"""

content = content.replace("  const filteredAssigneeUsers = users", helper_funcs)

# 2. Update filteredAssets logic to match the new status filters
old_filtered_assets_logic = """    const matchesStatus = statusFilter === "All" || a.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;"""
new_filtered_assets_logic = """    let matchesStatus = true;
    if (statusFilter === "Assigned") matchesStatus = isAssignedAsset(a);
    else if (statusFilter === "Unassigned") matchesStatus = isUnassignedAsset(a);
    else if (statusFilter === "Out of Service") matchesStatus = isOutOfServiceAsset(a);
    
    return matchesSearch && matchesCategory && matchesStatus;"""

content = content.replace(old_filtered_assets_logic, new_filtered_assets_logic)

# 3. Remove the flex-row gap-6 and Sidebar, and add the new filter rows
sidebar_pattern = re.compile(r'<div className="flex flex-col md:flex-row gap-6">.*?<div className="w-full md:w-64 flex-shrink-0">.*?</div>\s*<!-- Main Content -->\s*<div className="flex-1 space-y-4">', re.DOTALL)

new_filters = """
      {/* Filters (Categories & Status) */}
      <div className="space-y-4">
        {/* Category Filters */}
        <div className="flex flex-wrap items-center gap-2 bg-muted/40 p-1.5 rounded-xl w-full border border-border/50">
          <button
            onClick={() => setActiveCategory("All Categories")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
              activeCategory === "All Categories"
                ? "bg-primary text-primary-foreground shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }`}
          >
            All
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setActiveCategory(c.name)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
                activeCategory === c.name
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap items-center gap-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50">
          {(["All Assets", "Assigned", "Unassigned", "Out of Service"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status === "All Assets" ? "All" : status)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
                (statusFilter === "All" && status === "All Assets") || statusFilter === status
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              }`}
            >
              <span>{status}</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                (statusFilter === "All" && status === "All Assets") || statusFilter === status
                  ? "bg-primary-foreground/20 text-primary-foreground font-bold"
                  : "bg-muted text-muted-foreground"
              }`}>
                {counts[status]}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 space-y-4">"""

content = re.sub(sidebar_pattern, new_filters, content)

# 4. Remove the dropdown from the Filters Bar
old_filters_bar = """                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <select 
                    value={statusFilter}
                    onChange={e => setStatusFilter(e.target.value)}
                    className="px-3 py-2 text-sm rounded-lg border border-border bg-background outline-none focus:ring-2 focus:ring-violet"
                  >
                    <option value="All">All Statuses</option>
                    <option value="Unassigned">Unassigned</option>
                    <option value="Assigned">Assigned</option>
                    <option value="Retired">Retired</option>
                    <option value="Out of Service">Out of Service</option>
                  </select>
                </div>"""
content = content.replace(old_filters_bar, "")

# 5. Remove the closing </div> for the flex row that we removed
# The closing </div> is right before {/* Add / Edit Asset Modal */}
content = content.replace("</div>\n\n      {/* Add / Edit Asset Modal */}", "{/* Add / Edit Asset Modal */}")

with open("scratch/Assets_updated.tsx", "w") as f:
    f.write(content)
