// ── Utilities ─────────────────────────────────────────────────────────────────
export { cn } from "./lib/utils";

// ── Primitives ────────────────────────────────────────────────────────────────
export { Button, buttonVariants } from "./components/button";
export type { ButtonProps } from "./components/button";

export { Input } from "./components/input";
export type { InputProps } from "./components/input";

export { Label } from "./components/label";

export { Badge, badgeVariants } from "./components/badge";
export type { BadgeProps } from "./components/badge";

export { Separator } from "./components/separator";
export { Switch } from "./components/switch";
export { Skeleton } from "./components/skeleton";

// ── Layout ────────────────────────────────────────────────────────────────────
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./components/card";

// ── Overlay ───────────────────────────────────────────────────────────────────
export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "./components/dialog";

// ── Navigation ────────────────────────────────────────────────────────────────
export { Tabs, TabsList, TabsTrigger, TabsContent } from "./components/tabs";

// ── Forms ─────────────────────────────────────────────────────────────────────
export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from "./components/select";

// ── Data Display ──────────────────────────────────────────────────────────────
export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from "./components/table";

// ── Composite ─────────────────────────────────────────────────────────────────
export { EmptyState } from "./components/empty-state";
export { StatCard } from "./components/stat-card";
export { PageHeader } from "./components/page-header";
