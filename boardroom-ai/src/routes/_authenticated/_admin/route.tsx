import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { supabase } from "@/integrations/supabase/client";

/** Panel staff only — candidates are sent to their own dashboard. */
export const Route = createFileRoute("/_authenticated/_admin")({
  ssr: false,
  beforeLoad: async ({ context }) => {
    const { data } = await supabase.rpc("has_role", { _user_id: context.user.id, _role: "admin" });
    if (!data) throw redirect({ to: "/dashboard" });
  },
  component: () => <Outlet />,
});
