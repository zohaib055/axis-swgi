import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Building2,
  Server,
  ScrollText,
  Activity,
  CreditCard,
  Shield,
  Radio,
  KeyRound,
  FileSearch,
  Settings,
  Lock,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";

const operations = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Organizations", url: "/organizations", icon: Building2 },
  { title: "Clusters", url: "/clusters", icon: Server },
  { title: "Receipts", url: "/receipts", icon: ScrollText },
  { title: "Executions", url: "/executions", icon: Activity },
];

const governance = [
  { title: "Usage & Billing", url: "/usage", icon: CreditCard },
  { title: "Policies", url: "/policies", icon: Shield },
  { title: "Operator Events", url: "/operator-events", icon: Radio },
];

const admin = [
  { title: "API Keys", url: "/api-keys", icon: KeyRound },
  { title: "Audit Logs", url: "/audit-logs", icon: FileSearch },
  { title: "Settings", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const currentPath = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (p: string) => (p === "/" ? currentPath === "/" : currentPath.startsWith(p));

  const renderGroup = (label: string, items: typeof operations) => (
    <SidebarGroup>
      <SidebarGroupLabel className="text-[10px] uppercase tracking-wider text-sidebar-foreground/50">
        {label}
      </SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.url}>
              <SidebarMenuButton asChild isActive={isActive(item.url)}>
                <Link to={item.url} className="flex items-center gap-2">
                  <item.icon className="h-4 w-4" />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
            <Lock className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold text-sidebar-foreground">SWGI</span>
            <span className="text-[10px] text-sidebar-foreground/60">Command Center</span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {renderGroup("Operations", operations)}
        {renderGroup("Governance", governance)}
        {renderGroup("Administration", admin)}
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border p-2">
        <div className="flex items-center gap-2 text-[10px] text-sidebar-foreground/60">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          API healthy · v1.8.3
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
