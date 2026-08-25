import { useMemo, useState } from 'react'
import {
  TrendingUp,
  PieChart,
  ShieldAlert,
  Satellite,
  BarChart3,
  Flame,
  Zap,
} from 'lucide-react'
import type {
  FIRMSObservation,
  ClassificationRecord,
  PersistentThermalCluster,
} from '@/types'

interface AnalyticsChartsProps {
  observations: FIRMSObservation[]
  classifications: ClassificationRecord[]
  clusters: PersistentThermalCluster[]
}

export function AnalyticsCharts({
  observations,
  classifications,
  clusters,
}: AnalyticsChartsProps) {
  const [activeTab, setActiveTab] = useState<'timeline' | 'distribution' | 'sensors'>('timeline')

  // 1. Time series data: Group observations by date
  const timelineData = useMemo(() => {
    const countsByDate: Record<string, { count: number; totalFRP: number }> = {}

    observations.forEach((obs) => {
      const dateStr = obs.acq_datetime ? obs.acq_datetime.split('T')[0] : 'Unknown'
      if (!countsByDate[dateStr]) {
        countsByDate[dateStr] = { count: 0, totalFRP: 0 }
      }
      countsByDate[dateStr].count += 1
      countsByDate[dateStr].totalFRP += obs.frp || 0
    })

    const sortedDates = Object.keys(countsByDate).sort()
    return sortedDates.map((date) => ({
      date,
      count: countsByDate[date].count,
      avgFRP:
        countsByDate[date].count > 0
          ? countsByDate[date].totalFRP / countsByDate[date].count
          : 0,
    }))
  }, [observations])

  // 2. Classification Breakdown
  const classBreakdown = useMemo(() => {
    const counts: Record<string, number> = {
      persistent_industrial: 0,
      industrial_fire: 0,
      wildfire: 0,
      agricultural_burn: 0,
      uncertain_anomaly: 0,
    }

    classifications.forEach((c) => {
      const cls = c.predicted_class || 'uncertain_anomaly'
      counts[cls] = (counts[cls] || 0) + 1
    })

    // If no stored classifications yet, classify observations using heuristic estimate
    if (classifications.length === 0 && observations.length > 0) {
      observations.forEach((obs) => {
        if (obs.cluster_id !== null && obs.cluster_id !== undefined) {
          counts['persistent_industrial'] += 1
        } else if (obs.frp > 60 && obs.daynight === 'N') {
          counts['industrial_fire'] += 1
        } else if (obs.frp > 40) {
          counts['wildfire'] += 1
        } else if (obs.daynight === 'D' && obs.frp < 25) {
          counts['agricultural_burn'] += 1
        } else {
          counts['uncertain_anomaly'] += 1
        }
      })
    }

    const total = Math.max(1, Object.values(counts).reduce((a, b) => a + b, 0))

    const colors: Record<string, { label: string; color: string; bg: string }> = {
      persistent_industrial: { label: 'Persistent Industrial', color: '#06b6d4', bg: 'bg-cyan-500' },
      industrial_fire: { label: 'Industrial Fire Incident', color: '#f97316', bg: 'bg-orange-500' },
      wildfire: { label: 'Wildfire / Forest Fire', color: '#ef4444', bg: 'bg-rose-500' },
      agricultural_burn: { label: 'Agricultural Crop Burn', color: '#eab308', bg: 'bg-yellow-500' },
      uncertain_anomaly: { label: 'Uncertain Anomaly', color: '#94a3b8', bg: 'bg-slate-500' },
    }

    return Object.entries(counts).map(([key, count]) => ({
      key,
      label: colors[key]?.label || key,
      count,
      percentage: ((count / total) * 100).toFixed(1),
      color: colors[key]?.color || '#cbd5e1',
      bg: colors[key]?.bg || 'bg-slate-500',
    }))
  }, [classifications, observations])

  // 3. Risk Level Breakdown
  const riskBreakdown = useMemo(() => {
    const counts: Record<string, number> = {
      CRITICAL: 0,
      HIGH: 0,
      MODERATE: 0,
      LOW: 0,
    }

    classifications.forEach((c) => {
      const lvl = c.risk_level?.toUpperCase() || 'LOW'
      if (counts[lvl] !== undefined) counts[lvl] += 1
      else counts['LOW'] += 1
    })

    // Fallback if no classifications stored yet
    if (classifications.length === 0 && observations.length > 0) {
      observations.forEach((obs) => {
        if (obs.frp >= 80) counts['CRITICAL'] += 1
        else if (obs.frp >= 35) counts['HIGH'] += 1
        else if (obs.frp >= 15) counts['MODERATE'] += 1
        else counts['LOW'] += 1
      })
    }

    const total = Math.max(1, Object.values(counts).reduce((a, b) => a + b, 0))

    return [
      { level: 'CRITICAL', count: counts['CRITICAL'], color: '#ef4444', bg: 'bg-rose-500', pct: ((counts['CRITICAL'] / total) * 100).toFixed(1) },
      { level: 'HIGH', count: counts['HIGH'], color: '#f97316', bg: 'bg-orange-500', pct: ((counts['HIGH'] / total) * 100).toFixed(1) },
      { level: 'MODERATE', count: counts['MODERATE'], color: '#f59e0b', bg: 'bg-amber-500', pct: ((counts['MODERATE'] / total) * 100).toFixed(1) },
      { level: 'LOW', count: counts['LOW'], color: '#10b981', bg: 'bg-emerald-500', pct: ((counts['LOW'] / total) * 100).toFixed(1) },
    ]
  }, [classifications, observations])

  // 4. Satellite & Sensor distribution
  const sensorData = useMemo(() => {
    const counts: Record<string, number> = {}
    observations.forEach((obs) => {
      const sat = obs.satellite || 'Unknown'
      counts[sat] = (counts[sat] || 0) + 1
    })
    const total = Math.max(1, observations.length)
    return Object.entries(counts).map(([sat, count]) => ({
      satellite: sat,
      count,
      percentage: ((count / total) * 100).toFixed(1),
    }))
  }, [observations])

  const maxTimelineCount = Math.max(1, ...timelineData.map((d) => d.count))

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-5">
      {/* Header with View Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="size-4 text-amber-500" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-100">
            Thermal Anomaly Analytics & Trends
          </h3>
        </div>

        <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'timeline'
                ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="size-3.5" />
            <span>Timeline</span>
          </button>
          <button
            onClick={() => setActiveTab('distribution')}
            className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'distribution'
                ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <PieChart className="size-3.5" />
            <span>Classes & Risk</span>
          </button>
          <button
            onClick={() => setActiveTab('sensors')}
            className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
              activeTab === 'sensors'
                ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Satellite className="size-3.5" />
            <span>Telemetry</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Timeline & FRP Trend */}
      {activeTab === 'timeline' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Detections Volume & Radiative Power over Time</span>
            <span className="font-mono text-amber-400">{timelineData.length} observation cycles</span>
          </div>

          {timelineData.length > 0 ? (
            <div className="space-y-3">
              {/* Responsive SVG Histogram / Bar Chart */}
              <div className="h-44 flex items-end gap-2 pt-4 px-2 bg-slate-950/60 rounded-xl border border-slate-800/80">
                {timelineData.slice(-14).map((d) => {
                  const heightPercent = Math.max(8, (d.count / maxTimelineCount) * 100)
                  return (
                    <div
                      key={d.date}
                      className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group relative cursor-pointer"
                    >
                      {/* Tooltip on Hover */}
                      <div className="absolute -top-12 hidden group-hover:flex flex-col items-center z-20 bg-slate-900 border border-slate-700 px-2 py-1 rounded text-[10px] text-slate-200 whitespace-nowrap shadow-xl">
                        <span className="font-bold text-amber-400">{d.date}</span>
                        <span>{d.count} detections • {d.avgFRP.toFixed(1)} MW mean</span>
                      </div>

                      {/* Bar Column */}
                      <div className="w-full flex flex-col items-center justify-end h-full">
                        <div
                          className="w-full max-w-[28px] rounded-t-sm bg-gradient-to-t from-amber-600 to-amber-400 group-hover:from-amber-500 group-hover:to-yellow-300 transition-all shadow-sm"
                          style={{ height: `${heightPercent}%` }}
                        />
                      </div>

                      {/* Date label */}
                      <span className="text-[9px] font-mono text-slate-500 group-hover:text-slate-300 truncate w-full text-center">
                        {d.date.slice(5)}
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                <div className="flex items-center gap-1.5">
                  <span className="size-2 bg-amber-500 rounded-sm" />
                  <span>Observation Frequency</span>
                </div>
                <span>Hover over bars for daily telemetry details</span>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No historical timeline observations recorded.
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Classification & Risk Severity Distribution */}
      {activeTab === 'distribution' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Classification Distribution */}
          <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Flame className="size-3.5 text-amber-400" />
                AI Classification Breakdown
              </span>
            </div>

            <div className="space-y-2.5 pt-1">
              {classBreakdown.map((item) => (
                <div key={item.key} className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-300">{item.label}</span>
                    <span className="font-mono text-slate-400">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${item.bg}`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Risk Level Distribution */}
          <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <ShieldAlert className="size-3.5 text-rose-400" />
                Risk Severity Breakdown
              </span>
            </div>

            <div className="space-y-2.5 pt-1">
              {riskBreakdown.map((item) => (
                <div key={item.level} className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-300 font-semibold">{item.level} Severity</span>
                    <span className="font-mono text-slate-400">
                      {item.count} ({item.pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${item.bg}`}
                      style={{ width: `${item.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Satellite Telemetry Sensors */}
      {activeTab === 'sensors' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {sensorData.map((s) => (
            <div
              key={s.satellite}
              className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-cyan-300 font-bold">
                  {s.satellite}
                </span>
                <Satellite className="size-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-mono font-bold text-slate-100">{s.count}</div>
              <p className="text-xs text-slate-400 mt-1">{s.percentage}% of ingested observations</p>
            </div>
          ))}

          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs text-amber-300 font-bold">
                Persistent Clusters
              </span>
              <Zap className="size-4 text-amber-400" />
            </div>
            <div className="text-2xl font-mono font-bold text-slate-100">{clusters.length}</div>
            <p className="text-xs text-slate-400 mt-1">Multi-pass DBSCAN spatio-temporal nodes</p>
          </div>
        </div>
      )}
    </div>
  )
}
