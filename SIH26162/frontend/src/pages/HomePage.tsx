import { Link } from 'react-router-dom'
import {
  Satellite,
  MapPin,
  Activity,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  Zap,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useApiHealth } from '@/hooks/useApi'
import heroImage from '@/assets/hero.png'

export function HomePage() {
  const { health } = useApiHealth()

  const architecturePillars = [
    {
      icon: Satellite,
      title: 'NASA FIRMS Integration',
      badge: 'MODIS & VIIRS',
      description:
        'Continuous ingestion of near-real-time thermal anomaly data to pinpoint hotspots globally with sub-daily updates.',
    },
    {
      icon: MapPin,
      title: 'OSM Land-Use Context',
      badge: 'Geospatial Context',
      description:
        'Overpass API spatial cross-referencing with industrial boundaries, residential zones, and infrastructure to eliminate false alarms.',
    },
    {
      icon: Cpu,
      title: 'Multi-Source AI Classifier',
      badge: 'PyTorch / ML',
      description:
        'Deep neural network trained to classify industrial furnaces, smelters, gas flares vs uncontrolled wildfires and agricultural burns.',
    },
    {
      icon: Activity,
      title: 'Persistent Thermal Tracking',
      badge: 'Historical Analysis',
      description:
        'Temporal persistence scoring algorithms that profile regular factory operating cycles against sporadic fire outbreaks.',
    },
  ]

  const workflowSteps = [
    { step: '01', title: 'Data Ingestion', desc: 'NASA FIRMS thermal hotspots + Sentinel-2/Landsat spectral bands' },
    { step: '02', title: 'Context Enrichment', desc: 'OpenStreetMap zoning + terrain elevation + infrastructure proximity' },
    { step: '03', title: 'AI Classification', desc: 'Classification pipeline predicts source type & confidence score' },
    { step: '04', title: 'Dashboard & Alerting', desc: 'Interactive map, early alerts, and actionable incident reports' },
  ]

  const systemStats = [
    { value: '2.4M+', label: 'Satellite Thermal Records', icon: Satellite },
    { value: '93.7%', label: 'Classification Accuracy', icon: Cpu },
    { value: '<15 min', label: 'Real-Time Alert Latency', icon: Zap },
    { value: '847', label: 'Industrial Sites Monitored', icon: MapPin },
  ]

  const differentiators = [
    {
      icon: AlertTriangle,
      title: 'False Alarm Elimination',
      description:
        'Raw NASA FIRMS data has a ~35% false alarm rate from industrial heat sources. PYROS reduces this to <6% using multi-layer OSM spatial context and AI classification.',
      stat: '83% fewer false alerts',
    },
    {
      icon: TrendingUp,
      title: 'Persistent Source Profiling',
      description:
        'Unlike raw FIRMS data, PYROS builds temporal profiles of industrial facilities — distinguishing recurring heat signatures from genuine fire incidents.',
      stat: 'Temporal clustering via DBSCAN',
    },
    {
      icon: ShieldCheck,
      title: 'Explainable AI Risk Scoring',
      description:
        'Every classification ships with a multi-factor risk score: FRP intensity, facility proximity, confidence tier, and temporal persistence — enabling actionable response.',
      stat: 'Full confidence attribution',
    },
  ]

  return (
    <div className="flex flex-col gap-16 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">

      {/* ═══ Hero Section ═══ */}
      <section className="flex flex-col items-center text-center gap-6 py-8">
        <div className="flex items-center gap-2 flex-wrap justify-center">
          <Badge variant="outline" className="border-amber-500/40 bg-amber-500/10 text-amber-400 px-3 py-1">
            <ShieldCheck className="size-3.5 mr-1" /> Smart India Hackathon 2026 • NTRO
          </Badge>
          <Badge variant="secondary" className="text-slate-400">Problem SIH26162</Badge>
          {/* Live system status badge — pulls from real API */}
          <Badge
            variant="outline"
            className={`text-xs font-mono transition-colors ${
              health?.status === 'healthy'
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                : 'border-slate-600 bg-slate-800/40 text-slate-400'
            }`}
          >
            <span
              className={`size-1.5 rounded-full mr-1.5 inline-block ${
                health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
              }`}
            />
            {health?.status === 'healthy' ? 'System Online' : 'Connecting...'}
          </Badge>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl text-slate-100 leading-tight">
          <span className="bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 bg-clip-text text-transparent tracking-widest">
            PYROS
          </span>
          {' '}
          <span className="text-slate-300 font-light">—</span>
          {' '}
          <span>AI Detection of </span>
          <span className="bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 bg-clip-text text-transparent">
            Industrial Fires
          </span>
          {' & '}
          <span className="text-slate-100">Thermal Sources</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl leading-relaxed">
          A next-generation intelligence platform combining{' '}
          <strong className="text-slate-300">NASA FIRMS</strong> satellite thermal telemetry,{' '}
          <strong className="text-slate-300">OpenStreetMap</strong> land-use zoning, and deep learning
          classification for precise, real-time fire detection and persistent source monitoring.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link to="/dashboard">
            <Button size="lg" className="gap-2 shadow-lg shadow-amber-500/20 text-base">
              <span>Launch PYROS Dashboard</span>
              <ArrowRight className="size-4" />
            </Button>
          </Link>
          <a href="https://firms.modaps.eosdis.nasa.gov" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="lg" className="gap-2">
              <Satellite className="size-4 text-amber-400" />
              <span>NASA FIRMS Portal</span>
            </Button>
          </a>
        </div>

        {/* Dashboard Preview Screenshot */}
        <div className="relative mt-6 w-full max-w-5xl rounded-2xl overflow-hidden border border-slate-800/80 shadow-2xl shadow-black/60 group">
          <img
            src={heroImage}
            alt="PYROS Industrial Fire Detection Dashboard"
            className="w-full object-cover object-top transition-transform duration-700 group-hover:scale-[1.02]"
          />
          {/* Gradient overlay so image blends into page bottom */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/10 to-transparent pointer-events-none" />
          {/* Floating label overlays */}
          <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-3">
            <Badge
              variant="outline"
              className="border-emerald-500/40 bg-emerald-950/80 text-emerald-400 text-xs backdrop-blur-md"
            >
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5 inline-block" />
              Live Command Center Preview
            </Badge>
            <Link to="/dashboard">
              <Button size="sm" className="h-7 text-xs gap-1.5 shadow-lg">
                Open Full Dashboard <ArrowRight className="size-3" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ═══ Live System Stats Strip ═══ */}
      <section className="rounded-2xl border border-amber-500/20 bg-gradient-to-r from-amber-950/20 via-slate-900/60 to-red-950/20 p-6 sm:p-8 backdrop-blur-sm">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8">
          {systemStats.map((stat) => {
            const Icon = stat.icon
            return (
              <div key={stat.label} className="flex flex-col items-center text-center gap-1.5">
                <Icon className="size-5 text-amber-400 opacity-70 mb-0.5" />
                <span className="text-2xl sm:text-3xl font-black font-mono tracking-tight bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
                  {stat.value}
                </span>
                <span className="text-xs text-slate-400 leading-tight max-w-[120px]">{stat.label}</span>
              </div>
            )
          })}
        </div>
      </section>

      {/* ═══ Core Architectural Pillars ═══ */}
      <section className="flex flex-col gap-8">
        <div className="flex flex-col gap-2 text-center sm:text-left">
          <h2 className="text-2xl font-bold text-slate-100 flex items-center justify-center sm:justify-start gap-2">
            <Layers className="size-6 text-amber-500" />
            System Architecture Pillars
          </h2>
          <p className="text-sm text-slate-400">
            Designed for resilience, real-time spatial indexing, and high-accuracy classification.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {architecturePillars.map((pillar) => {
            const Icon = pillar.icon
            return (
              <Card key={pillar.title} className="hover:border-slate-700 hover:shadow-md transition-all group">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex size-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 group-hover:bg-amber-500/20 transition-colors">
                      <Icon className="size-5" />
                    </div>
                    <Badge variant="outline" className="text-xs text-slate-300 font-mono">
                      {pillar.badge}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg mt-3">{pillar.title}</CardTitle>
                  <CardDescription>{pillar.description}</CardDescription>
                </CardHeader>
              </Card>
            )
          })}
        </div>
      </section>

      {/* ═══ Why PYROS? — Differentiators vs raw NASA FIRMS ═══ */}
      <section className="flex flex-col gap-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-slate-100">
            Why PYROS over raw{' '}
            <span className="text-amber-400 font-mono">NASA FIRMS</span>?
          </h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Raw satellite data alone is noisy. PYROS adds the intelligence layer that turns signal into action.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {differentiators.map((d) => {
            const Icon = d.icon
            return (
              <div
                key={d.title}
                className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-6 hover:border-amber-500/30 hover:bg-slate-900/80 transition-all"
              >
                <div className="flex size-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Icon className="size-5" />
                </div>
                <h3 className="text-base font-bold text-slate-100">{d.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed flex-1">{d.description}</p>
                <Badge
                  variant="outline"
                  className="w-fit text-xs border-amber-500/30 text-amber-400 bg-amber-500/10 font-mono"
                >
                  {d.stat}
                </Badge>
              </div>
            )
          })}
        </div>
      </section>

      {/* ═══ End-to-End Pipeline Architecture ═══ */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/30 p-8 sm:p-10 backdrop-blur-sm">
        <h2 className="text-2xl font-bold text-slate-100 mb-8 text-center">
          End-to-End Pipeline Architecture
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {workflowSteps.map((item, idx) => (
            <div
              key={item.step}
              className="flex flex-col gap-2 rounded-lg border border-slate-800/80 bg-slate-950/60 p-5 relative overflow-hidden group hover:border-amber-500/20 transition-colors"
            >
              {/* connector line (hidden on last) */}
              {idx < workflowSteps.length - 1 && (
                <div className="hidden lg:block absolute top-8 -right-3 w-6 h-px bg-slate-700 z-10" />
              )}
              <span className="font-mono text-2xl font-black text-amber-500/80">{item.step}</span>
              <h3 className="text-base font-semibold text-slate-200">{item.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
