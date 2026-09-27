import { useEffect, useState } from "react";
import {
  getLocalUser,
  type LocalRole,
  type LocalUser,
} from "@/lib/local-auth";

export type AppRole = LocalRole;

export function useAuth() {
  const [user, setUser] = useState<LocalUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUser(getLocalUser());
    setLoading(false);

    const handleStorage = () => setUser(getLocalUser());

    window.addEventListener("storage", handleStorage);
    window.addEventListener("boardroom-auth-changed", handleStorage);

    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener("boardroom-auth-changed", handleStorage);
    };
  }, []);

  const roles: AppRole[] = user ? [user.role] : [];

  return {
    session: user ? { user } : null,
    user,
    roles,
    isAdmin: user?.role === "admin",
    loading,
  };
}
