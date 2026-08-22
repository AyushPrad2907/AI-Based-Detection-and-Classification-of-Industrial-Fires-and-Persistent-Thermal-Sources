import { Link, useLocation } from 'react-router-dom'
import { Flame, Activity, LayoutDashboard } from 'lucide-react'
import { useApiHealth } from '@/hooks/useApi'
import { Badge } from '@/components/ui/badge'

export function Header() {
  const location = useLocation()
  const { health, loading } = useApiHealth()

  const navLinks = [
    { name: 'Home', path: '/', icon: Flame },
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500 to-red-600 shadow-md shadow-amber-500/20">
            <Flame className="size-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-100">SIH26162</span>
              <Badge variant="outline" className="text-[10px] uppercase font-mono">NTRO</Badge>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Industrial Fire & Thermal AI Detector</p>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-4">
          {navLinks.map((link) => {
            const Icon = link.icon
            const isActive = location.pathname === link.path
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-slate-800 text-amber-400'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <Icon className="size-4" />
                <span>{link.name}</span>
              </Link>
            )
          })}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs border border-slate-800 rounded-full px-3 py-1 bg-slate-900/60">
            <Activity className="size-3 text-amber-500" />
            <span className="text-slate-400">Backend:</span>
            {loading ? (
              <span className="text-slate-500 animate-pulse">Checking...</span>
            ) : health?.status === 'healthy' ? (
              <span className="text-emerald-400 font-medium">Online</span>
            ) : (
              <span className="text-amber-500 font-medium">Standby</span>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
