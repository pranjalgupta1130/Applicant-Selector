import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

/** Panel staff only — candidates are sent to their own dashboard. */
export const Route = createFileRoute("/_authenticated/_admin")({
  ssr: false,
  beforeLoad: async ({ context }) => {
    if (context.user?.role !== "admin") throw redirect({ to: "/dashboard" });
  },
  component: () => <Outlet />,
});
