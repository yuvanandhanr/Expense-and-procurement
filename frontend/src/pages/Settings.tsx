import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { SystemSetting } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Skeleton } from "../components/ui";
import toast from "react-hot-toast";

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await api.get("/settings/system");
        setSettings(response.data);
        const initialForm: Record<string, string> = {};
        response.data.forEach((s: SystemSetting) => {
          initialForm[s.key] = s.value;
        });
        setFormData(initialForm);
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleChange = (key: string, val: string) => {
    setFormData((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put("/settings/system", formData);
      toast.success("System configurations successfully saved!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to save system settings.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Group settings by category
  const categories: Record<string, SystemSetting[]> = {};
  settings.forEach((s) => {
    if (!categories[s.category]) {
      categories[s.category] = [];
    }
    categories[s.category].push(s);
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
        <p className="text-xs text-muted-foreground mt-1">Tenant-wide policy configs, upload filters, and SMTP configurations.</p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {Object.entries(categories).map(([catName, items]) => (
          <Card key={catName}>
            <CardHeader>
              <CardTitle>{catName}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {items.map((item) => (
                  <Input
                    key={item.setting_id}
                    id={item.key}
                    label={item.description || item.key}
                    value={formData[item.key] || ""}
                    onChange={(e) => handleChange(item.key, e.target.value)}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}

        <div className="flex justify-end pt-4">
          <Button type="submit" disabled={saving} className="font-bold text-xs uppercase px-8 py-3">
            {saving ? "Saving Configurations..." : "Save System Settings"}
          </Button>
        </div>
      </form>
    </div>
  );
};
export default Settings;
