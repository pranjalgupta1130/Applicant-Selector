import { Link, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { clearLocalUser } from "@/lib/local-auth";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { BrandLogo } from "@/components/BrandLogo";

type Props = {
  /** Right-hand slot: timer, session indicator, actions. */
  right?: ReactNode;
  /** Candidate interview hides navigation so there is no way out of the interview. */
  showNav?: boolean;
};

export function BoardHeader({ right, showNav = true }: Props) {
  const { user, isAdmin, loading } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const signOut = async () => {
    await queryClient.cancelQueries();
    queryClient.clear();
    clearLocalUser();
    window.dispatchEvent(new Event("boardroom-auth-changed"));
    await navigate({ to: "/auth", replace: true });
  };

  const items = isAdmin
    ? [
        { to: "/panel", label: "Panel Review" },
        { to: "/admin", label: "Administration" },
      ]
    : [
        { to: "/dashboard", label: "My Dashboard" },
        { to: "/apply", label: "Begin Interview" },
      ];

  return (
    <header className="sticky top-0 z-30 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-5 py-4 sm:px-8">
        <Link to="/" className="min-w-0 shrink" aria-label="Boardroom AI home">
          <BrandLogo compact />
        </Link>

        {showNav && user && (
          <nav className="hidden items-center gap-1 md:flex">
            {items.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="rounded-md px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground data-[status=active]:bg-primary/8 data-[status=active]:text-primary"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        )}

        <div className="ml-auto flex items-center gap-3">
          {right}
          {showNav && !loading && (
            user ? (
              <div className="flex items-center gap-3">
                <span className="hidden rounded-full bg-emerald/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald sm:inline">
                  {isAdmin ? "Panel staff" : "Candidate"}
                </span>
                <Button variant="outline" size="sm" onClick={signOut}>
                  Sign out
                </Button>
              </div>
            ) : (
              <Button asChild size="sm">
                <Link to="/auth">Sign in</Link>
              </Button>
            )
          )}
        </div>
      </div>
      <div className="table-edge" />
    </header>
  );
}
