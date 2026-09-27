import { redirect } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";

/** Candidate-only pages: panel staff are sent to their own review area. */
export async function requireCandidate(userId: string) {
  const { data } = await supabase.rpc("has_role", { _user_id: userId, _role: "admin" });
  if (data) throw redirect({ to: "/panel" });
}
