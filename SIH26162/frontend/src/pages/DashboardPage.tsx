import { Flame, MapPin, ShieldAlert, Cpu } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Placeholder } from '@/components/dashboard/Placeholder'

export function DashboardPage() {
  const statCards = [
    { title: 'Monitored Sources', value: '0', sub: 'Awaiting Phase 1 FIRMS Sync', icon: Flame, color: 'text-amber-500' },
    { title: 'Industrial Zones', value: '0', sub: 'Awaiting Phase 1 OSM Sync', icon: MapPin, color: 'text-blue-400' },
    { title: 'Model Accuracy', value: 'Ready', sub: 'Baseline Classifier Defined', icon: Cpu, color: 'text-emerald-400' },
    { title: 'Active Alerts', value: '0', sub: 'System in Phase 0 Foundation', icon: ShieldAlert, color: 'text-red-400' },
  ]

  return (
    <div className="flex flex-col gap-8 py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-slate-100">Prototype Monitoring Dashboard</h1>
            <Badge variant="outline" className="border-amber-500/40 text-amber-400">Phase 0 Architecture</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time geospatial visualization, FIRMS anomaly feeds, and classification telemetry.
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">{stat.title}</CardTitle>
                <Icon className={`size-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-slate-100">{stat.value}</div>
                <p className="text-xs text-slate-500 mt-1">{stat.sub}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Grid: Interactive Map & Live Feed Placeholders */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Placeholder
            title="Interactive Geospatial Map (Leaflet / Mapbox + PostGIS)"
            description="Geographic map displaying active thermal detections with colour-coded classifications (Industrial vs Wildfire vs Agricultural)."
            phase="Phase 4 Frontend Target"
          />
        </div>
        <div className="flex flex-col gap-6">
          <Placeholder
            title="Live Thermal Anomaly Feed"
            description="Incoming stream of NASA FIRMS detections parsed with confidence, brightness temperature, and estimated FRP."
            phase="Phase 3 Target"
          />
          <Placeholder
            title="AI Classification & Explanation"
            description="Breakdown of spectral indices, OSM proximity checks, and model classification probabilities."
            phase="Phase 3 Target"
          />
        </div>
      </div>
    </div>
  )
}
