
import { Link } from 'react-router-dom'
import { Satellite, MapPin, Activity, ArrowRight, ShieldCheck, Cpu, Layers } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function HomePage() {
  const architecturePillars = [
    {
      icon: Satellite,
      title: 'NASA FIRMS Integration',
      badge: 'MODIS & VIIRS',
      description: 'Continuous ingestion of near-real-time thermal anomaly data to pinpoint hotspots globally with sub-daily updates.',
    },
    {
      icon: MapPin,
      title: 'OSM Land-Use Context',
      badge: 'Geospatial Context',
      description: 'Overpass API spatial cross-referencing with industrial boundaries, residential zones, and infrastructure to eliminate false alarms.',
    },
    {
      icon: Cpu,
      title: 'Multi-Source AI Classifier',
      badge: 'PyTorch / ML',
      description: 'Deep neural network trained to classify industrial furnaces, smelters, gas flares vs uncontrolled wildfires and agricultural burns.',
    },
    {
      icon: Activity,
      title: 'Persistent Thermal Tracking',
      badge: 'Historical Analysis',
      description: 'Temporal persistence scoring algorithms that profile regular factory operating cycles against sporadic fire outbreaks.',
    },
  ]

  const workflowSteps = [
    { step: '01', title: 'Data Ingestion', desc: 'NASA FIRMS thermal hotspots + Sentinel-2/Landsat spectral bands' },
    { step: '02', title: 'Context Enrichment', desc: 'OpenStreetMap zoning + terrain elevation + infrastructure proximity' },
    { step: '03', title: 'AI Classification', desc: 'Classification pipeline predicts source type & confidence score' },
    { step: '04', title: 'Dashboard & Alerting', desc: 'Interactive map, early alerts, and actionable incident reports' },
  ]

  return (
    <div className="flex flex-col gap-16 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="flex flex-col items-center text-center gap-6 py-8">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-amber-500/40 bg-amber-500/10 text-amber-400 px-3 py-1">
            <ShieldCheck className="size-3.5 mr-1" /> Smart India Hackathon 2026 • NTRO
          </Badge>
          <Badge variant="secondary" className="text-slate-400">Problem SIH26162</Badge>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl text-slate-100 leading-tight">
          AI-Powered Detection of <span className="bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 bg-clip-text text-transparent">Industrial Fires</span> & Persistent Thermal Sources
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-3xl leading-relaxed">
          A next-generation intelligence platform combining <strong>NASA FIRMS</strong> satellite thermal telemetry, <strong>OpenStreetMap</strong> land-use zoning, and deep learning classification for precise, real-time fire detection and persistent source monitoring.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link to="/dashboard">
            <Button size="lg" className="gap-2 shadow-lg shadow-amber-500/20 text-base">
              <span>Launch Prototype Dashboard</span>
              <ArrowRight className="size-4" />
            </Button>
          </Link>
          <a
            href="https://firms.modaps.eosdis.nasa.gov"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" size="lg" className="gap-2">
              <Satellite className="size-4 text-amber-400" />
              <span>NASA FIRMS Portal</span>
            </Button>
          </a>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section className="flex flex-col gap-8">
        <div className="flex flex-col gap-2 text-center sm:text-left">
          <h2 className="text-2xl font-bold text-slate-100 flex items-center justify-center sm:justify-start gap-2">
            <Layers className="size-6 text-amber-500" />
            System Architecture Pillars
          </h2>
          <p className="text-sm text-slate-400">Designed for resilience, real-time spatial indexing, and high-accuracy classification.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {architecturePillars.map((pillar) => {
            const Icon = pillar.icon
            return (
              <Card key={pillar.title} className="hover:border-slate-700 transition-colors">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex size-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
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

      {/* Planned Pipeline Workflow */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/30 p-8 sm:p-10 backdrop-blur-sm">
        <h2 className="text-2xl font-bold text-slate-100 mb-8 text-center">End-to-End Pipeline Architecture</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {workflowSteps.map((item) => (
            <div key={item.step} className="flex flex-col gap-2 rounded-lg border border-slate-800/80 bg-slate-950/60 p-5">
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
