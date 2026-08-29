import React, { useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Flame,
  Cpu,
  Shield,
  Eye,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type {
  FIRMSObservation,
  PersistentThermalCluster,
  ClassificationRecord,
  SelectedEntity,
} from '@/types'

interface ObservationsTableProps {
  observations: FIRMSObservation[]
  clusters: PersistentThermalCluster[]
  classifications: ClassificationRecord[]
  selectedEntity: SelectedEntity | null
  onSelectEntity: (entity: SelectedEntity) => void
  currentPage: number
  totalPages: number
  totalItems: number
  onPageChange: (page: number) => void
  loading?: boolean
}

function ObservationsTableInner({
  observations,
  clusters,
  classifications,
  selectedEntity,
  onSelectEntity,
  currentPage,
  totalPages,
  totalItems,
  onPageChange,
  loading = false,
}: ObservationsTableProps) {
  const [activeTab, setActiveTab] = useState<'observations' | 'clusters' | 'classifications'>(
    'observations'
  )
  const [searchTerm, setSearchTerm] = useState('')

  // Export visible data to CSV
  const handleExportCSV = () => {
    let headers: string[] = []
    let rows: string[][] = []
    let filename = 'sih26162_telemetry_export.csv'

    if (activeTab === 'observations') {
      filename = 'firms_observations.csv'
      headers = ['ID', 'Latitude', 'Longitude', 'FRP_MW', 'Brightness_K', 'Confidence_%', 'DayNight', 'Satellite', 'Acq_Date']
      rows = observations.map((o) => [
        o.id?.toString() || '',
        o.latitude.toString(),
        o.longitude.toString(),
        o.frp.toString(),
        o.brightness_primary.toString(),
        o.confidence_score.toString(),
        o.daynight,
        o.satellite,
        o.acq_datetime,
      ])
    } else if (activeTab === 'clusters') {
      filename = 'persistent_thermal_clusters.csv'
      headers = ['Cluster_ID', 'Centroid_Lat', 'Centroid_Lon', 'Observation_Count', 'Mean_FRP_MW', 'Max_FRP_MW', 'Duration_Days', 'Is_Persistent']
      rows = clusters.map((c) => [
        c.cluster_id.toString(),
        c.centroid_latitude.toString(),
        c.centroid_longitude.toString(),
        c.observation_count.toString(),
        c.mean_frp_mw.toString(),
        c.max_frp_mw.toString(),
        c.persistence_duration_days.toString(),
        c.is_persistent ? 'TRUE' : 'FALSE',
      ])
    } else {
      filename = 'ml_classifications.csv'
      headers = ['ID', 'Latitude', 'Longitude', 'Predicted_Class', 'Confidence', 'Risk_Score', 'Risk_Level', 'Created_At']
      rows = classifications.map((c) => [
        c.id.toString(),
        c.latitude.toString(),
        c.longitude.toString(),
        c.predicted_class,
        c.confidence.toString(),
        c.risk_score?.toString() || '',
        c.risk_level || '',
        c.created_at,
      ])
    }

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Filter observations by search query
  const filteredObs = observations.filter((o) => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      o.id?.toString().includes(term) ||
      o.satellite.toLowerCase().includes(term) ||
      o.latitude.toString().includes(term) ||
      o.longitude.toString().includes(term)
    )
  })

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur space-y-4">
      {/* Header with Table Switcher, Search, and Export */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          {/* Tabs */}
          <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('observations')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'observations'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Flame className="size-3.5" />
              <span>FIRMS Detections ({observations.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('clusters')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'clusters'
                  ? 'bg-cyan-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="size-3.5" />
              <span>Persistent Sources ({clusters.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('classifications')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'classifications'
                  ? 'bg-rose-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Shield className="size-3.5" />
              <span>Classifications ({classifications.length})</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Search bar */}
          <div className="relative">
            <Search className="size-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search coords, ID, sat..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 focus:outline-none focus:border-amber-500 w-44 sm:w-56"
            />
          </div>

          {/* Export CSV */}
          <Button
            size="sm"
            variant="outline"
            onClick={handleExportCSV}
            className="h-8 bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800 text-xs"
          >
            <Download className="size-3.5 mr-1.5 text-amber-500" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto rounded-lg border border-slate-800/80">
        {activeTab === 'observations' && (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">ID / Source</th>
                <th className="py-2.5 px-3">Coordinates (Lat, Lon)</th>
                <th className="py-2.5 px-3">FRP (MW)</th>
                <th className="py-2.5 px-3">Brightness (K)</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Pass</th>
                <th className="py-2.5 px-3">Acquisition UTC</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
              {filteredObs.length > 0 ? (
                filteredObs.map((obs) => {
                  const isSelected =
                    selectedEntity?.type === 'observation' &&
                    (selectedEntity.data as FIRMSObservation).id === obs.id

                  return (
                    <tr
                      key={`${obs.latitude}-${obs.longitude}-${obs.acq_datetime}-${obs.id}`}
                      className={`hover:bg-slate-800/50 transition-colors ${
                        isSelected ? 'bg-amber-500/10 border-l-2 border-amber-500' : ''
                      }`}
                    >
                      <td className="py-2.5 px-3 font-mono">
                        <div className="font-bold text-slate-200">#{obs.id ?? 'NRT'}</div>
                        <div className="text-[10px] text-slate-500">{obs.satellite}</div>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {obs.latitude.toFixed(4)}°, {obs.longitude.toFixed(4)}°
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold">
                        <span
                          className={
                            obs.frp >= 50
                              ? 'text-red-400'
                              : obs.frp >= 20
                              ? 'text-amber-400'
                              : 'text-yellow-400'
                          }
                        >
                          {obs.frp.toFixed(1)} MW
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {obs.brightness_primary.toFixed(1)} K
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        <Badge
                          variant="outline"
                          className={`text-[10px] px-1.5 py-0 ${
                            obs.confidence_score >= 80
                              ? 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10'
                              : 'border-amber-500/40 text-amber-400 bg-amber-500/10'
                          }`}
                        >
                          {obs.confidence_score.toFixed(0)}%
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3">
                        {obs.daynight === 'N' ? (
                          <span className="text-blue-400 font-medium">🌙 Night</span>
                        ) : (
                          <span className="text-amber-400 font-medium">☀️ Day</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400 text-[11px]">
                        {new Date(obs.acq_datetime).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onSelectEntity({ type: 'observation', data: obs })}
                          className="h-7 text-xs text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 px-2"
                        >
                          <Eye className="size-3 mr-1" />
                          <span>Inspect</span>
                        </Button>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    {loading ? 'Fetching FIRMS observations...' : 'No satellite detections match the active filter criteria.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {activeTab === 'clusters' && (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Cluster ID</th>
                <th className="py-2.5 px-3">Centroid (Lat, Lon)</th>
                <th className="py-2.5 px-3">Pass Count</th>
                <th className="py-2.5 px-3">Mean FRP (MW)</th>
                <th className="py-2.5 px-3">Active Duration</th>
                <th className="py-2.5 px-3">Nocturnal Ratio</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
              {clusters.length > 0 ? (
                clusters.map((c) => {
                  const isSelected =
                    selectedEntity?.type === 'cluster' &&
                    (selectedEntity.data as PersistentThermalCluster).cluster_id === c.cluster_id

                  return (
                    <tr
                      key={c.cluster_id}
                      className={`hover:bg-slate-800/50 transition-colors ${
                        isSelected ? 'bg-cyan-500/10 border-l-2 border-cyan-500' : ''
                      }`}
                    >
                      <td className="py-2.5 px-3 font-mono font-bold text-cyan-300">
                        #{c.cluster_id}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {c.centroid_latitude.toFixed(4)}°, {c.centroid_longitude.toFixed(4)}°
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-100 font-bold">
                        {c.observation_count} passes
                      </td>
                      <td className="py-2.5 px-3 font-mono text-amber-400 font-bold">
                        {c.mean_frp_mw.toFixed(1)} MW
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {c.persistence_duration_days.toFixed(1)} days
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300">
                        {(c.night_observation_ratio * 100).toFixed(0)}%
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        <Badge
                          variant="outline"
                          className={
                            c.is_persistent
                              ? 'border-cyan-500/40 text-cyan-300 bg-cyan-500/10'
                              : 'border-slate-700 text-slate-400'
                          }
                        >
                          {c.is_persistent ? 'PERSISTENT INDUSTRIAL' : 'TRANSIENT'}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onSelectEntity({ type: 'cluster', data: c })}
                          className="h-7 text-xs text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10 px-2"
                        >
                          <Eye className="size-3 mr-1" />
                          <span>Inspect</span>
                        </Button>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No persistent spatio-temporal clusters discovered.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {activeTab === 'classifications' && (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Record ID</th>
                <th className="py-2.5 px-3">Coordinates (Lat, Lon)</th>
                <th className="py-2.5 px-3">Predicted Class</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Risk Level</th>
                <th className="py-2.5 px-3">Risk Score</th>
                <th className="py-2.5 px-3">Inference Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
              {classifications.length > 0 ? (
                classifications.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-200">
                      #{rec.id}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">
                      {rec.latitude.toFixed(4)}°, {rec.longitude.toFixed(4)}°
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-amber-400">
                      {rec.predicted_class}
                    </td>
                    <td className="py-2.5 px-3 font-mono">
                      {(rec.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge
                        variant="outline"
                        className={
                          rec.risk_level === 'CRITICAL'
                            ? 'border-rose-500/40 text-rose-400 bg-rose-500/10'
                            : rec.risk_level === 'HIGH'
                            ? 'border-orange-500/40 text-orange-400 bg-orange-500/10'
                            : rec.risk_level === 'MODERATE'
                            ? 'border-amber-500/40 text-amber-400 bg-amber-500/10'
                            : 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10'
                        }
                      >
                        {rec.risk_level || 'LOW'}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-slate-100">
                      {rec.risk_score?.toFixed(1) || 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400 text-[11px]">
                      {new Date(rec.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No ML classifications stored yet. Select an observation to run live classification.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
          <span>
            Showing Page <strong className="text-slate-200">{currentPage}</strong> of{' '}
            <strong className="text-slate-200">{totalPages}</strong> ({totalItems} total records)
          </span>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1 || loading}
              className="h-8 px-2 bg-slate-950 border-slate-800 text-slate-300"
            >
              <ChevronLeft className="size-4" />
            </Button>
            <span className="font-mono text-xs text-slate-300 px-2">{currentPage} / {totalPages}</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage >= totalPages || loading}
              className="h-8 px-2 bg-slate-950 border-slate-800 text-slate-300"
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export const ObservationsTable = React.memo(ObservationsTableInner)
