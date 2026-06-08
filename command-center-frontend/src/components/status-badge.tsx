import { cn } from "@/lib/utils";

type Variant =
  | "success"
  | "warning"
  | "destructive"
  | "info"
  | "muted"
  | "allow"
  | "deny"
  | "modify";

const variants: Record<Variant, string> = {
  success: "bg-success/10 text-success border-success/20",
  warning: "bg-warning/15 text-warning-foreground border-warning/30",
  destructive: "bg-destructive/10 text-destructive border-destructive/20",
  info: "bg-info/10 text-info border-info/20",
  muted: "bg-muted text-muted-foreground border-border",
  allow: "bg-success/10 text-success border-success/20",
  deny: "bg-destructive/10 text-destructive border-destructive/20",
  modify: "bg-warning/15 text-warning-foreground border-warning/30",
};

export function StatusBadge({
  variant = "muted",
  children,
  className,
  dot,
}: {
  variant?: Variant;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        variants[variant],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
