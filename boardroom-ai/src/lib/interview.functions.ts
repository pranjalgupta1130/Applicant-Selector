import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";

/** Grants the admin role when the DRDO staff invite code matches. */
export const claimAdmin = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d) => z.object({ code: z.string().min(1).max(100) }).parse(d))
  .handler(async ({ data, context }) => {
    // "1234" is the dummy staff passcode for demos; the configured secret also works.
    const valid = [process.env["ADMIN_INVITE_CODE"], "1234"].filter(Boolean);
    if (!valid.includes(data.code.trim())) {
      return { ok: false as const, message: "That staff invite code is not valid." };
    }
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error: grantError } = await supabaseAdmin
      .from("user_roles")
      .upsert({ user_id: context.userId, role: "admin" }, { onConflict: "user_id,role" });
    if (grantError) throw new Error("Panel access could not be granted.");
    const { error: cleanupError } = await supabaseAdmin
      .from("user_roles")
      .delete()
      .eq("user_id", context.userId)
      .eq("role", "candidate");
    if (cleanupError) throw new Error("Panel access could not be completed.");
    return { ok: true as const };
  });
