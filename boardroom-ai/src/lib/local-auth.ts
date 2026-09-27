export type LocalRole = "admin" | "candidate";

export type LocalUser = {
  id: string;
  email: string;
  name: string;
  role: LocalRole;
};

const STORAGE_KEY = "boardroom.localUser";

export const DEMO_USERS: LocalUser[] = [
  {
    id: "demo-vikram-sharma",
    email: "vikram.sharma@demo.local",
    name: "Dr. Vikram Sharma",
    role: "candidate",
  },
  {
    id: "demo-arjun-mehta",
    email: "arjun.mehta@demo.local",
    name: "Arjun Mehta",
    role: "candidate",
  },
  {
    id: "demo-priya-nair",
    email: "priya.nair@demo.local",
    name: "Priya Nair",
    role: "candidate",
  },
  {
    id: "demo-panel",
    email: "panel@demo.local",
    name: "DRDO Selection Panel",
    role: "admin",
  },
];

export function getLocalUser(): LocalUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as LocalUser) : null;
  } catch {
    return null;
  }
}

export function setLocalUser(user: LocalUser) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

export function clearLocalUser() {
  localStorage.removeItem(STORAGE_KEY);
}
