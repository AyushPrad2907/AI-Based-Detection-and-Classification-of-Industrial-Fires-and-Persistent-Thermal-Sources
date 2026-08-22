import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "warning" | "success"
}

function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  const base = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
  
  const variants = {
    default: "border-transparent bg-amber-500/20 text-amber-400 border-amber-500/30",
    secondary: "border-transparent bg-slate-800 text-slate-300",
    destructive: "border-transparent bg-red-500/20 text-red-400 border-red-500/30",
    warning: "border-transparent bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    success: "border-transparent bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    outline: "text-slate-300 border-slate-700",
  }

  return (
    <div className={cn(base, variants[variant], className)} {...props} />
  )
}

export { Badge }
