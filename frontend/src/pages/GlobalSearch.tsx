import React, { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { api } from "../services/api";
import { SearchResult } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge, Input, Button } from "../components/ui";
import { formatDate } from "../utils/helpers";
import { Search } from "lucide-react";

export const GlobalSearch: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  
  const [inputValue, setInputValue] = useState(query);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchResults = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const response = await api.get(`/search?q=${encodeURIComponent(q)}`);
      setResults(response.data);
    } catch (err) {
      console.error("Search query failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setInputValue(query);
    fetchResults(query);
  }, [query]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      setSearchParams({ q: inputValue });
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Global Index Search</h1>
        <p className="text-xs text-muted-foreground mt-1">Cross-entity searches over Requisitions, Orders, Vendors, Contracts, and Invoices.</p>
      </div>

      <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2 bg-card p-3 rounded-lg border border-border">
        <div className="flex items-center flex-1 bg-background border border-border rounded-lg focus-within:ring-2 focus-within:ring-ring transition-all">
          <Search className="w-5 h-5 ml-3 text-muted-foreground/60 shrink-0 pointer-events-none" />
          <input
            type="text"
            placeholder="Type query keywords (e.g. Acme, server, PO-)..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full pl-2 pr-4 py-2.5 text-sm bg-transparent focus:outline-none"
          />
        </div>
        <Button type="submit" className="font-bold text-xs uppercase px-6 py-2.5">
          Search Index
        </Button>
      </form>

      <div className="space-y-4">
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : results.length === 0 ? (
          query && (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider bg-card border border-border rounded-lg">
              No matching records found in the search index for query "{query}".
            </div>
          )
        ) : (
          <div className="space-y-4">
            <div className="text-xs text-muted-foreground font-semibold uppercase">
              Found {results.length} matching entries:
            </div>
            <div className="grid grid-cols-1 gap-4">
              {results.map((res) => (
                <Card key={res.index_id} className="hover:border-primary/50 transition-colors">
                  <CardHeader className="py-4 flex flex-row items-start justify-between border-none">
                    <div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="info">{res.entity_type}</Badge>
                        <span className="text-xs font-semibold text-muted-foreground">ID: #{res.entity_id}</span>
                      </div>
                      <CardTitle className="text-md font-bold text-foreground/95 mt-2">
                        {res.title}
                      </CardTitle>
                    </div>
                    <span className="text-[10px] text-muted-foreground font-semibold uppercase">
                      Updated: {formatDate(res.updated_at)}
                    </span>
                  </CardHeader>
                  <CardContent className="py-2 text-xs text-muted-foreground/90 font-medium border-t border-border/30">
                    <p>{res.content}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default GlobalSearch;
