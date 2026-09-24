import { Flame, Shield, Zap } from 'lucide-react'

const techStack = [
  { label: 'React 19', color: 'text-cyan-400' },
  { label: 'FastAPI', color: 'text-emerald-400' },
  { label: 'PostGIS', color: 'text-blue-400' },
  { label: 'NASA FIRMS', color: 'text-amber-400' },
  { label: 'PyTorch', color: 'text-orange-400' },
  { label: 'Leaflet', color: 'text-green-400' },
  { label: 'Zustand', color: 'text-purple-400' },
  { label: 'Tailwind CSS', color: 'text-sky-400' },
]

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-800/80 bg-slate-950/60 py-6 text-slate-400">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-4">
        {/* Tech Stack Row */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          {techStack.map((tech) => (
            <span
              key={tech.label}
              className={`text-[11px] font-mono font-semibold px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 ${tech.color}`}
            >
              {tech.label}
            </span>
          ))}
        </div>

        {/* Bottom Row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
          <div className="flex items-center gap-2">
            <Flame className="size-4 text-amber-500" />
            <span className="text-sm font-extrabold text-slate-300 tracking-widest bg-gradient-to-r from-amber-400 to-red-500 bg-clip-text text-transparent">
              PYROS
            </span>
            <span className="text-slate-600">—</span>
            <span className="text-xs text-slate-400">Smart India Hackathon 2026</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Zap className="size-3 text-amber-500/60" />
            <span className="font-mono">Data refreshed every 15 min · NASA FIRMS NRT Feed</span>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Shield className="size-3.5 text-slate-500" />
            <span>National Technical Research Organisation (NTRO)</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
