import { useState, useEffect } from 'react'
import {
  X,
  Flame,
  Cpu,
  Shield,
  Factory,
  Play,
  RotateCw,
  ArrowDown,
  Info,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ApiService } from '@/lib/api'
import type {
  SelectedEntity,
  FIRMSObservation,
  PersistentThermalCluster,
  FireClassificationResult,
  IndustrialContextResponse,
} from '@/types'

interface DetailPanelProps {
  selectedEntity: SelectedEntity | null
  onClose: () => void
  onClassificationComplete?: (result: FireClassificationResult) => void
}

function getRiskBadge(level?: string) {
  switch (level?.toUpperCase()) {
    case 'CRITICAL':
      return { bg: 'bg-rose-500/20 text-rose-300 border-rose-500/40', label: 'CRITICAL RISK' }
    case 'HIGH':
      return { bg: 'bg-orange-500/20 text-orange-300 border-orange-500/40', label: 'HIGH RISK' }
    case 'MODERATE':
      return { bg: 'bg-amber-500/20 text-amber-300 border-amber-500/40', label: 'MODERATE RISK' }
    case 'LOW':
      return { bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40', label: 'LOW RISK' }
    default:
      return { bg: 'bg-slate-800 text-slate-400 border-slate-700', label: 'UNASSESSED' }
  }
}

function formatClassName(className?: string) {
  if (!className) return 'Unclassified'
  return className
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Maps OSM fallback status codes to human-readable UI labels. */
function getOsmStatusLabel(status?: string): { label: string; color: string } {
  if (!status || status === 'success') {
    return { label: 'Industrial facility verified within radius', color: 'text-indigo-300' }
  }
  if (status === 'no_facilities_found' || status.startsWith('offline_fallback') || status.startsWith('service_unavailable')) {
    return { label: 'No industrial facilities located within 5 km', color: 'text-slate-400' }
  }
  return { label: 'Spatial query completed', color: 'text-slate-400' }
}

export function DetailPanel({
  selectedEntity,
  onClose,
  onClassificationComplete,
}: DetailPanelProps) {
  const [classification, setClassification] = useState<FireClassificationResult | null>(null)
  const [industrialContext, setIndustrialContext] = useState<IndustrialContextResponse | null>(null)
  const [isInferencing, setIsInferencing] = useState(false)
  const [isQueryingOSM, setIsQueryingOSM] = useState(false)
  const [persistToDB, setPersistToDB] = useState(false)
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null)

  const isObservation = selectedEntity?.type === 'observation'
  const isCluster = selectedEntity?.type === 'cluster'

  const obs = isObservation ? (selectedEntity?.data as FIRMSObservation) : null
  const cluster = isCluster ? (selectedEntity?.data as PersistentThermalCluster) : null

  const lat = obs ? obs.latitude : cluster ? cluster.centroid_latitude : 0
  const lon = obs ? obs.longitude : cluster ? cluster.centroid_longitude : 0

  const runLiveClassification = async (obsData: FIRMSObservation, forcePersist = false) => {
    try {
      setIsInferencing(true)
      setSaveSuccessMessage(null)
      const res = await ApiService.classifyObservation({
        latitude: obsData.latitude,
        longitude: obsData.longitude,
        brightness_primary: obsData.brightness_primary,
        brightness_secondary: obsData.brightness_secondary,
        frp: obsData.frp,
        confidence: obsData.confidence_score,
        daynight: obsData.daynight,
        acq_datetime: obsData.acq_datetime,
        satellite: obsData.satellite,
        instrument: obsData.instrument,
        query_osm: true,
        persist: forcePersist || persistToDB,
      })

      setClassification(res)
      if (res.industrial_context) {
        setIndustrialContext(res.industrial_context as unknown as IndustrialContextResponse)
      }
      if (forcePersist || (persistToDB && res.classification_id)) {
        setSaveSuccessMessage(`Persisted to database with ID #${res.classification_id}`)
      }
      if (onClassificationComplete) {
        onClassificationComplete(res)
      }
    } catch (err) {
      console.error('Classification error:', err)
    } finally {
      setIsInferencing(false)
    }
  }

  // Reset state and trigger classification when entity changes
  useEffect(() => {
    setClassification(null)
    setIndustrialContext(null)
    setSaveSuccessMessage(null)

    if (selectedEntity?.type === 'observation') {
      const obsData = selectedEntity.data as FIRMSObservation
      runLiveClassification(obsData)
    }
  }, [selectedEntity])

  if (!selectedEntity) return null

  const queryOsmContext = async () => {
    try {
      setIsQueryingOSM(true)
      const res = await ApiService.getIndustrialContext(lat, lon, 5000)
      setIndustrialContext(res)
    } catch (err) {
      console.error('OSM Query error:', err)
    } finally {
      setIsQueryingOSM(false)
    }
  }

  const riskBadge = getRiskBadge(classification?.risk_level)

  return (
    <div className="bg-slate-900/95 border border-slate-800 rounded-xl p-5 shadow-2xl backdrop-blur flex flex-col gap-5 text-slate-100 max-h-[850px] overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
            {isObservation ? <Flame className="size-5" /> : <Cpu className="size-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100">
                {isObservation
                  ? `FIRMS Observation #${obs?.id ?? 'NRT'}`
                  : `Persistent Cluster #${cluster?.cluster_id}`}
              </h2>
              <Badge variant="outline" className="text-[10px] uppercase font-mono border-slate-700 bg-slate-800/80">
                {isObservation ? obs?.satellite : 'DBSCAN CLUSTER'}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Lat: {lat.toFixed(5)}° | Lon: {lon.toFixed(5)}°
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Observation Telemetry Summary */}
      {isObservation && obs && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
          <div>
            <span className="text-slate-400">Fire Radiative Power:</span>
            <div className="text-amber-400 font-mono font-bold text-sm mt-0.5">{obs.frp.toFixed(1)} MW</div>
          </div>
          <div>
            <span className="text-slate-400">Brightness Temp:</span>
            <div className="text-slate-200 font-mono font-bold text-sm mt-0.5">{obs.brightness_primary.toFixed(1)} K</div>
          </div>
          <div>
            <span className="text-slate-400">Confidence Score:</span>
            <div className="text-cyan-400 font-mono font-bold text-sm mt-0.5">{obs.confidence_score.toFixed(0)}%</div>
          </div>
          <div>
            <span className="text-slate-400">Satellite Pass:</span>
            <div className="text-slate-200 font-medium text-sm mt-0.5">
              {obs.daynight === 'N' ? '🌙 Nocturnal' : '☀️ Diurnal'}
            </div>
          </div>
        </div>
      )}

      {/* Cluster Telemetry Summary */}
      {isCluster && cluster && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
          <div>
            <span className="text-slate-400">Satellite Passes:</span>
            <div className="text-cyan-400 font-mono font-bold text-sm mt-0.5">{cluster.observation_count} detections</div>
          </div>
          <div>
            <span className="text-slate-400">Mean FRP:</span>
            <div className="text-amber-400 font-mono font-bold text-sm mt-0.5">{cluster.mean_frp_mw.toFixed(1)} MW</div>
          </div>
          <div>
            <span className="text-slate-400">Active Duration:</span>
            <div className="text-slate-200 font-mono font-bold text-sm mt-0.5">{cluster.persistence_duration_days.toFixed(1)} days</div>
          </div>
          <div>
            <span className="text-slate-400">Spatial Radius:</span>
            <div className="text-slate-200 font-mono font-bold text-sm mt-0.5">{cluster.spatial_radius_meters.toFixed(0)} m</div>
          </div>
        </div>
      )}

      {/* Pipeline Flow Arrow: Telemetry → AI */}
      {isObservation && (
        <div className="flex justify-center">
          <ArrowDown className="size-4 text-slate-600" />
        </div>
      )}

      {/* AI Classification & Probabilities */}
      <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="size-4 text-cyan-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              AI Classification
            </h3>
          </div>
          {classification && (
            <Badge variant="outline" className="text-[10px] font-mono text-cyan-300 border-cyan-500/30 bg-cyan-500/10">
              {(classification.classification_confidence * 100).toFixed(1)}% Confidence
            </Badge>
          )}
        </div>

        {/* Disclaimer */}
        <div className="flex items-start gap-1.5 text-[10px] text-slate-500 bg-slate-900/40 px-2 py-1.5 rounded border border-slate-800/50">
          <Info className="size-3 shrink-0 mt-0.5" />
          <span>Random Forest model prediction (29 features, 150 estimators). Not a human expert assessment.</span>
        </div>

        {isInferencing ? (
          <div className="py-4 flex flex-col items-center justify-center gap-2 text-slate-400">
            <RotateCw className="size-5 text-amber-500 animate-spin" />
            <span className="text-xs">Running Random Forest Classifier &amp; Feature Engineering...</span>
          </div>
        ) : classification ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400">Predicted Class:</span>
              <span className="text-sm font-bold text-amber-400 font-mono">
                {formatClassName(classification.predicted_class)}
              </span>
            </div>

            {/* Class Probabilities Bars */}
            <div className="space-y-2 pt-1">
              <div className="text-[11px] font-medium text-slate-400">Probability Breakdown:</div>
              {Object.entries(classification.class_probabilities || {}).map(([cName, prob]) => {
                const percentage = (prob * 100).toFixed(1)
                const isWinner = cName === classification.predicted_class
                return (
                  <div key={cName} className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className={isWinner ? 'text-amber-400 font-semibold' : 'text-slate-400'}>
                        {formatClassName(cName)}
                      </span>
                      <span className="font-mono text-slate-300">{percentage}%</span>
                    </div>
                    <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isWinner ? 'bg-amber-500' : 'bg-slate-600'
                        }`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="py-3 text-center text-xs text-slate-500">
            Select an observation or click "Run Inference" to compute ML predictions.
          </div>
        )}
      </div>

      {/* Pipeline Flow Arrow: AI → Risk */}
      {classification && (
        <div className="flex justify-center">
          <ArrowDown className="size-4 text-slate-600" />
        </div>
      )}

      {/* Explainable Multi-Factor Risk Assessment */}
      {classification && (
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="size-4 text-rose-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Risk Assessment
              </h3>
            </div>
            <Badge variant="outline" className={`text-[10px] font-mono font-bold ${riskBadge.bg}`}>
              {riskBadge.label}
            </Badge>
          </div>

          {/* Disclaimer */}
          <div className="flex items-start gap-1.5 text-[10px] text-slate-500 bg-slate-900/40 px-2 py-1.5 rounded border border-slate-800/50">
            <Info className="size-3 shrink-0 mt-0.5" />
            <span>Explainable composite risk score (0–100) from 5 weighted factors. Not an emergency alert system.</span>
          </div>

          {/* Risk Score Gauge */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Composite Risk Score</span>
              <span className={`font-mono font-bold ${riskBadge.bg.split(' ')[1]}`}>
                {classification.risk_score.toFixed(1)} / 100
              </span>
            </div>
            <div className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  classification.risk_score >= 75 ? 'bg-rose-500' :
                  classification.risk_score >= 55 ? 'bg-orange-500' :
                  classification.risk_score >= 35 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(classification.risk_score, 100)}%` }}
              />
            </div>
          </div>

          {/* Subscores as Percentage Bars */}
          {classification.risk_breakdown && (
            <div className="space-y-2 pt-1">
              <div className="text-[11px] font-medium text-slate-400">Risk Factor Breakdown:</div>
              {[
                { label: 'Fire Radiative Power', val: classification.risk_breakdown.frp_subscore, max: 30, color: 'bg-amber-500' },
                { label: 'Industrial Proximity', val: classification.risk_breakdown.industrial_proximity_subscore, max: 25, color: 'bg-cyan-500' },
                { label: 'Source Persistence', val: classification.risk_breakdown.persistence_subscore, max: 20, color: 'bg-purple-500' },
                { label: 'Detection Confidence', val: classification.risk_breakdown.confidence_subscore, max: 15, color: 'bg-emerald-500' },
                { label: 'Nocturnal Activity', val: classification.risk_breakdown.nocturnal_subscore, max: 10, color: 'bg-blue-500' },
              ].map(({ label, val, max, color }) => (
                <div key={label} className="space-y-0.5">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-slate-400">{label}</span>
                    <span className="font-mono text-slate-300">{val.toFixed(1)} / {max}</span>
                  </div>
                  <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${color}`}
                      style={{ width: `${Math.min((val / max) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* WHY? — Explainable Reasons */}
          {classification.reasons && classification.reasons.length > 0 && (
            <div className="space-y-1.5 pt-1 border-t border-slate-800/60">
              <span className="text-[11px] font-semibold text-slate-300">WHY this score?</span>
              <ul className="space-y-1">
                {classification.reasons.map((reason, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold leading-none mt-0.5">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Industrial Infrastructure Context (OSM) */}
      <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Factory className="size-4 text-indigo-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Industrial Infrastructure Proximity (OSM)
            </h3>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={queryOsmContext}
            disabled={isQueryingOSM}
            className="text-[10px] h-6 px-2 text-indigo-300 hover:bg-indigo-500/10"
          >
            <RotateCw className={`size-3 mr-1 ${isQueryingOSM ? 'animate-spin' : ''}`} />
            Query OSM
          </Button>
        </div>

        {isQueryingOSM ? (
          <div className="py-3 flex items-center justify-center gap-2 text-xs text-slate-400 font-mono">
            <RotateCw className="size-3.5 text-indigo-400 animate-spin" />
            <span>Querying Overpass API (radius: 5 km)...</span>
          </div>
        ) : industrialContext ? (
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between bg-slate-900/90 p-2 rounded border border-slate-800">
              <span className="text-slate-400">Status:</span>
              <span className={`font-medium ${getOsmStatusLabel(industrialContext.status).color}`}>
                {getOsmStatusLabel(industrialContext.status).label}
              </span>
            </div>

            <div className="flex items-center justify-between bg-slate-900/90 p-2 rounded border border-slate-800">
              <span className="text-slate-400">Industrial Facility Nearby:</span>
              <Badge
                variant="outline"
                className={
                  industrialContext.is_industrial_nearby
                    ? 'border-indigo-500/40 text-indigo-300 bg-indigo-500/10'
                    : 'border-slate-700 text-slate-400'
                }
              >
                {industrialContext.is_industrial_nearby ? 'YES (Within 5km)' : 'NO'}
              </Badge>
            </div>

            {industrialContext.nearest_facility_name && (
              <div className="bg-slate-900/80 p-2.5 rounded border border-slate-800 space-y-1">
                <div className="font-semibold text-indigo-200">
                  {industrialContext.nearest_facility_name}
                </div>
                <div className="text-slate-400 text-[11px] flex justify-between">
                  <span>Type: <strong className="text-slate-200">{industrialContext.nearest_facility_type}</strong></span>
                  <span>Distance: <strong className="text-amber-400">{industrialContext.min_distance_m.toFixed(0)} m</strong></span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-slate-500 py-1">
            Click "Query OSM" to check for power plants, refineries, chemical sites, and industrial parks within 5 km.
          </div>
        )}
      </div>

      {/* Persistence and Action Controls */}
      {isObservation && obs && (
        <div className="pt-2 border-t border-slate-800/80 flex flex-col gap-2.5">
          <div className="flex items-center justify-between text-xs text-slate-300">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={persistToDB}
                onChange={(e) => setPersistToDB(e.target.checked)}
                className="rounded border-slate-700 text-amber-500 focus:ring-amber-500 bg-slate-950"
              />
              <span>Persist classification result to PostgreSQL / PostGIS</span>
            </label>
          </div>

          <Button
            onClick={() => runLiveClassification(obs, true)}
            disabled={isInferencing}
            className="w-full bg-gradient-to-r from-amber-500 to-red-600 hover:from-amber-600 hover:to-red-700 text-slate-950 font-bold text-xs h-9 shadow-lg shadow-amber-500/20"
          >
            <Play className="size-3.5 mr-1.5 fill-slate-950" />
            {isInferencing ? 'Running Inference...' : 'Run Live AI Classification & Risk Assessment'}
          </Button>

          {saveSuccessMessage && (
            <div className="text-[11px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded p-2 text-center">
              ✓ {saveSuccessMessage}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
