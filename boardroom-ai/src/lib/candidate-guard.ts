import { redirect } from "@tanstack/react-router";
import { getLocalUser } from "@/lib/local-auth";

/** Candidate-only pages: panel staff are sent to their own review area. */
export function requireCandidate(_userId?: string) {
  const user = getLocalUser();
  if (!user) {
    throw redirect({ to: "/auth" });
  }
  if (user.role === "admin") {
    throw redirect({ to: "/panel" });
  }
}
