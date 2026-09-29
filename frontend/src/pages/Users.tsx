import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { CurrentUser, Role } from "../types";
import {Button, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Dialog, Input, EmptyState, Select} from "../components/ui";
import toast from "react-hot-toast";
import { getErrorMessage } from "../utils/helpers";
import { useAuth } from "../hooks/useAuth";
import { Plus } from "lucide-react";

export const Users: React.FC = () => {
  const { hasRole } = useAuth();
  const [users, setUsers] = useState<CurrentUser[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Create / Edit User Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [password, setPassword] = useState("");
  const [selectedRoles, setSelectedRoles] = useState<number[]>([]);
  const [departmentName, setDepartmentName] = useState("");
  const [employeeType, setEmployeeType] = useState("pending assignment");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [departments, setDepartments] = useState<any[]>([]);

  const fetchUsersAndRoles = async () => {
    setLoading(true);
    try {
      const [usersRes, rolesRes, deptsRes] = await Promise.all([
        api.get("/users"),
        api.get("/roles"),
        api.get("/departments")
      ]);
      setUsers(usersRes.data);
      setRoles(rolesRes.data);
      setDepartments(deptsRes.data);
    } catch (err) {
      console.error("Failed to load users or roles:", err);
      toast.error("Failed to load user data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndRoles();
  }, []);

  const openCreateModal = () => {
    setIsEditMode(false);
    setEditingUserId(null);
    setEmail("");
    setFullName("");
    setEmployeeCode("");
    setPassword("");
    setSelectedRoles([]);
    setIsModalOpen(true);
  };

  const openEditModal = (user: CurrentUser) => {
    setIsEditMode(true);
    setEditingUserId(user.user_id);
    setEmail(user.email);
    setFullName(`${user.first_name || ""} ${user.last_name || ""}`.trim() || user.full_name || "");
    setEmployeeCode(user.employee_code || "");
    setPassword("");
    setSelectedRoles(user.roles.map(r => r.role_id));
    setDepartmentName(user.department_name || "");
    setEmployeeType(user.employee_type || "pending assignment");
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !fullName || (!isEditMode && (!employeeCode || !password))) {
      toast.error("Please fill in all required fields.");
      return;
    }

    setIsSubmitting(true);
    try {
      const names = fullName.trim().split(" ");
      const firstName = names[0];
      const lastName = names.slice(1).join(" ");

      const payload: any = {
        first_name: firstName,
        last_name: lastName,
        status: "Active",
        role_ids: selectedRoles,
        department_name: departmentName || null,
        employee_type: employeeType || "pending assignment"
      };

      if (isEditMode && editingUserId) {
        if (password) {
          payload.password = password;
        }
        await api.put(`/users/${editingUserId}`, payload);
        toast.success("User updated successfully!");
      } else {
        payload.email = email;
        payload.employee_code = employeeCode;
        payload.password = password;
        await api.post("/users", payload);
        toast.success("User created successfully!");
      }
      setIsModalOpen(false);
      fetchUsersAndRoles();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to save user."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleLock = async (user: CurrentUser) => {
    try {
      if (user.is_locked) {
        await api.post(`/users/${user.user_id}/unlock`);
        toast.success(`User ${user.email} unlocked successfully.`);
      } else {
        await api.post(`/users/${user.user_id}/lock`);
        toast.success(`User ${user.email} locked successfully.`);
      }
      fetchUsersAndRoles();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Action failed."));
    }
  };

  const handleOffboard = async (user: CurrentUser) => {
    if (!confirm(`Are you sure you want to initiate offboarding for ${user.email}?`)) return;
    try {
      await api.post(`/offboarding/${user.user_id}/trigger`);
      toast.success(`Offboarding initiated for ${user.email}. Tasks have been generated.`);
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to initiate offboarding."));
    }
  };

  const toggleRoleSelection = (roleId: number) => {
    setSelectedRoles(prev => 
      prev.includes(roleId) ? [] : [roleId]
    );
  };

  return (
    <div className="space-y-6">
        <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
          <p className="text-xs text-muted-foreground mt-1">Manage system users, assign roles, and control access.</p>
        </div>
        {hasRole("Admin") && (
          <Button onClick={openCreateModal} className="font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 shadow-apple-glow">
            <Plus className="w-4 h-4" /> Add New User
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : users.length === 0 ? (
            <EmptyState title="No users found." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    <th className="p-4">ID</th>
                    <th className="p-4">Full Name</th>
                    <th className="p-4">Email</th>
                    <th className="p-4">Department</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Roles</th>
                    <th className="p-4">Status</th>
                    {hasRole("Admin") && <th className="p-4 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {users.map((user, index) => (
                    <tr key={user.user_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 text-xs font-bold text-primary">{index + 1}</td>
                      <td className="p-4 font-semibold">{`${user.first_name || ""} ${user.last_name || ""}`.trim() || "N/A"}</td>
                      <td className="p-4 text-muted-foreground">{user.email}</td>
                      <td className="p-4 font-medium">{user.department_name || "N/A"}</td>
                      <td className="p-4"><Badge variant="outline">{user.employee_type || "N/A"}</Badge></td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {user.roles.length > 0 ? (
                            user.roles.map(r => (
                              <Badge key={r.role_id} variant="neutral" className="text-[10px]">
                                {r.role_name}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-xs text-muted-foreground italic">No Roles</span>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        {user.status !== "Active" ? (
                          <Badge variant="danger">Inactive</Badge>
                        ) : user.is_locked ? (
                          <Badge variant="warning">Locked</Badge>
                        ) : (
                          <Badge variant="success">Active</Badge>
                        )}
                      </td>
                      {hasRole("Admin") && (
                        <td className="p-4 text-right space-x-2 whitespace-nowrap">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => openEditModal(user)}
                          >
                            Edit
                          </Button>
                          <Button 
                            variant={user.is_locked ? "outline" : "danger"} 
                            size="sm" 
                            onClick={() => handleToggleLock(user)}
                          >
                            {user.is_locked ? "Unlock" : "Lock"}
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleOffboard(user)}
                            disabled={user.status !== "Active"}
                          >
                            Offboard
                          </Button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Creation / Edit Modal */}
      <Dialog isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={isEditMode ? "Edit User" : "Add New User"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            id="employeeCode"
            label="Employee Code"
            placeholder="e.g. EMP123"
            value={employeeCode}
            onChange={(e) => setEmployeeCode(e.target.value)}
            disabled={isEditMode}
          />
          <Input
            id="fullName"
            label="Full Name"
            placeholder="e.g. John Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <Input
            id="email"
            type="email"
            label="Email Address"
            placeholder="e.g. john.doe@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isEditMode}
          />
          <Input
            id="password"
            type="password"
            label={isEditMode ? "New Password (Optional)" : "Password"}
            placeholder="Minimum 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Select
            label="Department"
            value={departmentName}
            onChange={e => setDepartmentName(e.target.value)}
            options={[
              { label: "None", value: "" },
              ...departments.map((d: any) => ({ label: d.department_name, value: d.department_name }))
            ]}
          />
          <Select
            label="Employee Type"
            value={employeeType}
            onChange={e => setEmployeeType(e.target.value)}
            options={[
              { label: "None", value: "" },
              { label: "Intern", value: "Intern" },
              { label: "Consultant", value: "Consultant" },
              { label: "Full-Time", value: "Full-Time" },
              { label: "Part-Time", value: "Part-Time" },
              { label: "Contract", value: "Contract" },
            ]}
          />
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Assign Roles
            </label>
            <div className="flex flex-wrap gap-2">
              {roles.map(role => (
                <button
                  key={role.role_id}
                  type="button"
                  onClick={() => toggleRoleSelection(role.role_id)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full border transition-colors ${
                    selectedRoles.includes(role.role_id) 
                      ? 'bg-primary border-primary text-primary-foreground' 
                      : 'bg-background border-border text-muted-foreground hover:bg-accent'
                  }`}
                >
                  {role.role_name}
                </button>
              ))}
              {roles.length === 0 && (
                <span className="text-xs text-muted-foreground italic">No roles available.</span>
              )}
            </div>
          </div>
          <div className="flex justify-end space-x-2 pt-3 mt-2">
            <Button variant="close" type="button"  onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : (isEditMode ? "Save Changes" : "Create User")}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
};
export default Users;
