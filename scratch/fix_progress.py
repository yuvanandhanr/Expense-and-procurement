with open("frontend/src/components/expenses/ReimbursementDetailModal.tsx", "r") as f:
    content = f.read()

# Replace the progress bar colors and lines
old_code = """                  // Connecting line logic
                  const lineCompleted = isCompleted && !isActive;
                  const lineError = isError;

                  return (
                    <React.Fragment key={idx}>
                      <div className="relative z-10 flex flex-col items-center gap-3 shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                          isError 
                            ? "bg-red-500 text-white ring-4 ring-red-500/20" 
                            : isActive 
                              ? "bg-card text-blue-500 border-2 border-blue-500 ring-4 ring-blue-500/20 scale-110" 
                              : isCompleted 
                              ? ["bg-blue-200", "bg-blue-300", "bg-blue-400", "bg-blue-500", "bg-blue-600", "bg-blue-700"][idx] + " text-white shadow-md shadow-blue-500/20" 
                                : "bg-card text-muted-foreground border-2 border-muted"
                        }`}>
                          {idx + 1}
                        </div>
                        <span className={`absolute top-11 text-[9px] uppercase tracking-wider font-bold whitespace-nowrap ${isError ? "text-red-500" : isActive ? "text-blue-500" : isCompleted ? "text-gray-700" : "text-muted-foreground"}`}>{step}</span>
                      </div>
                      
                      {/* Connecting Line Segment */}
                      {idx < arr.length - 1 && (
                        <div className={`flex-1 h-[2px] mx-1 ${lineError ? 'bg-red-400' : lineCompleted ? 'bg-slate-200' : 'bg-transparent'}`} />
                      )}"""

new_code = """                  // Connecting line logic
                  const lineCompleted = isCompleted && idx < currentStepIdx;
                  const lineError = isError;

                  return (
                    <React.Fragment key={idx}>
                      <div className="relative z-10 flex flex-col items-center gap-3 shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                          isError 
                            ? "bg-red-500 text-white ring-4 ring-red-500/20" 
                            : isActive 
                              ? "bg-card text-blue-600 border-2 border-blue-600 ring-4 ring-blue-600/20 scale-110" 
                              : isCompleted 
                              ? "bg-blue-500 text-white shadow-md shadow-blue-500/20" 
                                : "bg-card text-muted-foreground border-2 border-muted"
                        }`}>
                          {idx + 1}
                        </div>
                        <span className={`absolute top-11 text-[9px] uppercase tracking-wider font-bold whitespace-nowrap ${isError ? "text-red-500" : isActive ? "text-blue-600" : isCompleted ? "text-blue-500" : "text-muted-foreground"}`}>{step}</span>
                      </div>
                      
                      {/* Connecting Line Segment */}
                      {idx < arr.length - 1 && (
                        <div className={`flex-1 h-[2px] mx-1 ${lineError ? 'bg-red-400' : lineCompleted ? 'bg-blue-400' : 'bg-slate-200'}`} />
                      )}"""

content = content.replace(old_code, new_code)
with open("frontend/src/components/expenses/ReimbursementDetailModal.tsx", "w") as f:
    f.write(content)
