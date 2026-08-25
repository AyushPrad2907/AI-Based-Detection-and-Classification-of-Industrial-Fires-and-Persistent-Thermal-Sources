import { useState, useEffect } from 'react'
import {
  Activity,
  Database,
  Cpu,
  CheckCircle2,
  XCircle,
  RotateCw,
  Server,
  X,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ApiService } from '@/lib/api'
import type { HealthStatus, DatabaseHealth, ModelStatus } from '@/types'

interface SystemHealthModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SystemHealthModal({ isOpen, onClose }: SystemHealthModalProps) {
  const [apiHealth, setApiHealth] = useState<HealthStatus | null>(null)
  const [dbHealth, setDbHealth] = useState<DatabaseHealth | null>(null)
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDiagnostics = async () => {
    try {
      setLoading(true)
      setError(null)
      const [api, db, model] = await Promise.all([
        ApiService.getHealth().catch(() => null),
        ApiService.getDatabaseHealth().catch(() => null),
        ApiService.getModelStatus().catch(() => null),
      ])
      setApiHealth(api)
      setDbHealth(db)
      setModelStatus(model)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Diagnostics query failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchDiagnostics()
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[2000] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 text-slate-100 max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Activity className="size-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">System Diagnostics & Infrastructure</h2>
              <p className="text-xs text-slate-400">
                Live operational health of FastAPI backend, PostgreSQL + PostGIS, and ML inference pipelines.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Error notification if any */}
        {error && (
          <div className="bg-rose-950/40 border border-rose-500/40 rounded-lg p-3 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="size-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Action button */}
        <div className="flex justify-end">
          <Button
            size="sm"
            variant="outline"
            onClick={fetchDiagnostics}
            disabled={loading}
            className="h-8 text-xs bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
          >
            <RotateCw className={`size-3.5 mr-1.5 ${loading ? 'animate-spin text-amber-500' : ''}`} />
            Refresh Telemetry
          </Button>
        </div>

        {/* 1. FastAPI Backend Health */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="size-4 text-cyan-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                FastAPI Backend Service
              </span>
            </div>
            {apiHealth?.status === 'healthy' ? (
              <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10 text-xs">
                <CheckCircle2 className="size-3 mr-1" />
                ONLINE (v{apiHealth.version})
              </Badge>
            ) : (
              <Badge variant="outline" className="border-rose-500/40 text-rose-400 bg-rose-500/10 text-xs">
                <XCircle className="size-3 mr-1" />
                OFFLINE / STANDBY
              </Badge>
            )}
          </div>
          <div className="text-xs text-slate-400 flex justify-between">
            <span>Service Name: <strong className="text-slate-200">{apiHealth?.service || 'SIH26162 API'}</strong></span>
            <span>Protocols: <strong className="text-slate-200">REST / OpenAPI 3.1</strong></span>
          </div>
        </div>

        {/* 2. PostgreSQL + PostGIS Spatial Database */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="size-4 text-amber-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                PostgreSQL + PostGIS Database
              </span>
            </div>
            {dbHealth?.database_connected ? (
              <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10 text-xs">
                <CheckCircle2 className="size-3 mr-1" />
                CONNECTED
              </Badge>
            ) : (
              <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/10 text-xs">
                FILE-SYSTEM ENGINE FALLBACK
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs pt-1">
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px]">PostGIS Engine:</span>
              <div className="font-mono font-bold text-slate-200">
                {dbHealth?.postgis_version || (dbHealth?.postgis_installed ? 'Installed' : 'Standard Fallback')}
              </div>
            </div>
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px]">Database Name:</span>
              <div className="font-mono font-bold text-slate-200">
                {dbHealth?.database_name || 'sih26162_fire_db'}
              </div>
            </div>
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px]">FIRMS Records:</span>
              <div className="font-mono font-bold text-amber-400">
                {dbHealth?.table_counts?.firms_observations ?? 0}
              </div>
            </div>
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px]">Persistent Clusters:</span>
              <div className="font-mono font-bold text-cyan-400">
                {dbHealth?.table_counts?.persistent_thermal_sources ?? 0}
              </div>
            </div>
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px]">Industrial Sites:</span>
              <div className="font-mono font-bold text-indigo-400">
                {dbHealth?.table_counts?.industrial_facilities ?? 0}
              </div>
            </div>
            <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px]">ML Classifications:</span>
              <div className="font-mono font-bold text-rose-400">
                {dbHealth?.table_counts?.classifications ?? 0}
              </div>
            </div>
          </div>
        </div>

        {/* 3. AI Classifier & Feature Pipeline Status */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="size-4 text-purple-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Random Forest ML Classifier
              </span>
            </div>
            {modelStatus?.ready ? (
              <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10 text-xs">
                <CheckCircle2 className="size-3 mr-1" />
                MODEL LOADED & READY
              </Badge>
            ) : (
              <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/10 text-xs">
                RULE-BASED / COLD LOAD
              </Badge>
            )}
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Model Architecture:</span>
              <span className="font-mono text-slate-200 font-bold">{modelStatus?.model_type || 'RandomForestClassifier'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Trained Feature Dimensions:</span>
              <span className="font-mono text-slate-200">{modelStatus?.features_count || 8} engineered features</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Known Industrial Clusters Index:</span>
              <span className="font-mono text-cyan-400">{modelStatus?.persistent_clusters_known || 0} spatial centroids</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Supported Target Classes:</span>
              <span className="font-mono text-amber-400">5 distinct anomaly categories</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <Button onClick={onClose} className="bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs">
            Close Diagnostics
          </Button>
        </div>
      </div>
    </div>
  )
}
