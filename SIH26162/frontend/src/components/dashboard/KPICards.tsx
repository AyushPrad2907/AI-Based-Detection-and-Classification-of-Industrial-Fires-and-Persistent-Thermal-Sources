import { Flame, ShieldAlert, Cpu, Activity, Zap } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { FIRMSObservation, PersistentThermalCluster, ClassificationRecord } from '@/types'

interface KPICardsProps {
  observations: FIRMSObservation[]
  clusters: PersistentThermalCluster[]
  classifications: ClassificationRecord[]
  totalObservationsCount: number
  totalClustersCount: number
  loading?: boolean
  isDatabaseConnected?: boolean
}

export function KPICards({
  observations,
  clusters,
  classifications,
  totalObservationsCount,
  totalClustersCount,
  loading = false,
  isDatabaseConnected = true,
}: KPICardsProps) {
  // Compute key metrics from real backend data
  const totalObs = totalObservationsCount > 0 ? totalObservationsCount : observations.length
  const totalClust = totalClustersCount > 0 ? totalClustersCount : clusters.length

  // High & Critical Risk Count
  const highRiskCount = classifications.filter(
    (c) => c.risk_level === 'HIGH' || c.risk_level === 'CRITICAL'
  ).length

  // FRP Metrics
  const frpValues = observations.map((o) => o.frp).filter((f) => !isNaN(f) && f > 0)
  const maxFRP = frpValues.length > 0 ? Math.max(...frpValues).toFixed(1) : '0.0'
  const meanFRP =
    frpValues.length > 0
      ? (frpValues.reduce((acc, v) => acc + v, 0) / frpValues.length).toFixed(1)
      : '0.0'

  // Night observations count
  const nightCount = observations.filter((o) => o.daynight === 'N').length

  const stats = [
    {
      title: 'Raw Thermal Detections',
      value: loading ? '...' : totalObs.toLocaleString(),
      sub: `${observations.length} loaded in viewport • NASA FIRMS / PostGIS`,
      icon: Flame,
      color: 'text-amber-500',
      badge: isDatabaseConnected ? 'FIRMS Telemetry' : 'Offline Buffer',
      badgeColor: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
    },
    {
      title: 'Persistent Thermal Clusters',
      value: loading ? '...' : totalClust.toLocaleString(),
      sub: `${clusters.filter((c) => c.is_persistent).length} DBSCAN spatial clusters`,
      icon: Cpu,
      color: 'text-cyan-400',
      badge: 'DBSCAN PostGIS',
      badgeColor: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10',
    },
    {
      title: 'High & Critical Risk Anomalies',
      value: loading ? '...' : highRiskCount.toString(),
      sub: `${classifications.length} AI classified records evaluated`,
      icon: ShieldAlert,
      color: 'text-rose-500',
      badge: highRiskCount > 0 ? 'Elevated Risk' : 'Nominal',
      badgeColor:
        highRiskCount > 0
          ? 'border-rose-500/30 text-rose-400 bg-rose-500/10'
          : 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
    },
    {
      title: 'Peak Radiative Power (FRP)',
      value: loading ? '...' : `${maxFRP} MW`,
      sub: `Mean FRP: ${meanFRP} MW • ${nightCount} Nocturnal`,
      icon: Zap,
      color: 'text-yellow-400',
      badge: 'Spectral Telemetry',
      badgeColor: 'border-yellow-500/30 text-yellow-400 bg-yellow-500/10',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title} className="border-slate-800 bg-slate-900/70 backdrop-blur shadow-sm hover:border-slate-700 transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2 pt-4 px-4">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {stat.title}
              </CardTitle>
              <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50">
                <Icon className={`size-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent className="px-4 pb-4 pt-1">
              <div className="flex items-baseline justify-between gap-2">
                <div className="text-2xl font-black tracking-tight text-slate-100 font-mono">
                  {stat.value}
                </div>
                <Badge variant="outline" className={`text-[10px] px-1.5 py-0 font-mono ${stat.badgeColor}`}>
                  {stat.badge}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-1.5 truncate flex items-center gap-1.5">
                <Activity className="size-3 text-slate-500 shrink-0" />
                <span>{stat.sub}</span>
              </p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
