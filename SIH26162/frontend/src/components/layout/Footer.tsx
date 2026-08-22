import { Flame, Shield } from 'lucide-react'

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-800/80 bg-slate-950/60 py-8 text-slate-400">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <Flame className="size-4 text-amber-500" />
          <span className="text-sm font-semibold text-slate-300">
            SIH26162 — Smart India Hackathon 2026
          </span>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Shield className="size-3.5 text-slate-400" />
          <span>National Technical Research Organisation (NTRO)</span>
        </div>

        <p className="text-xs text-slate-500">
          Prototype Phase 0 Architecture • Production Quality
        </p>
      </div>
    </footer>
  )
}
