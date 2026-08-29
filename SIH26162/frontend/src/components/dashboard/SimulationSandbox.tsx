import { useState } from 'react'
import {
  FlaskConical,
  Play,
  RotateCcw,
  Moon,
  Sun,
  Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ApiService } from '@/lib/api'
import type { FireClassificationResult } from '@/types'

const PRESETS = [
  {
    name: 'Industrial Refinery Flare',
    lat: 28.6139,
    lon: 77.209,
    frp: 85.5,
    brightness: 380.0,
    confidence: 95,
    daynight: 'N',
    desc: 'Critical nocturnal anomaly near industrial infrastructure',
  },
  {
    name: 'Agricultural Crop Residue',
    lat: 30.3753,
    lon: 76.7821,
    frp: 12.4,
    brightness: 320.0,
    confidence: 65,
    daynight: 'D',
    desc: 'Daytime transient anomaly in open farmland',
  },
  {
    name: 'Thermal Power Station',
    lat: 22.5726,
    lon: 88.3639,
    frp: 45.0,
    brightness: 345.0,
    confidence: 90,
    daynight: 'N',
    desc: 'Persistent high-temperature energy generation source',
  },
  {
    name: 'Major Wildfire Front',
    lat: 15.7728,
    lon: 73.7036,
    frp: 140.0,
    brightness: 410.0,
    confidence: 92,
    daynight: 'D',
    desc: 'High-intensity widespread vegetation combustion',
  },
]

export function SimulationSandbox() {
  const [lat, setLat] = useState<number>(28.6139)
  const [lon, setLon] = useState<number>(77.209)
  const [frp, setFrp] = useState<number>(65)
  const [brightness, setBrightness] = useState<number>(360)
  const [confidence, setConfidence] = useState<number>(85)
  const [daynight, setDaynight] = useState<'D' | 'N'>('N')
  const [queryOsm, setQueryOsm] = useState<boolean>(true)

  const [loading, setLoading] = useState<boolean>(false)
  const [result, setResult] = useState<FireClassificationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const applyPreset = (p: (typeof PRESETS)[number]) => {
    setLat(p.lat)
    setLon(p.lon)
    setFrp(p.frp)
    setBrightness(p.brightness)
    setConfidence(p.confidence)
    setDaynight(p.daynight as 'D' | 'N')
  }

  const runSimulation = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await ApiService.classifyObservation({
        latitude: lat,
        longitude: lon,
        brightness_primary: brightness,
        brightness_secondary: brightness - 25.0,
        frp,
        confidence,
        daynight,
        query_osm: queryOsm,
        persist: false,
      })
      setResult(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Simulation failed.')
    } finally {
      setLoading(false)
    }
  }

  const resetSimulation = () => {
    setLat(28.6139)
    setLon(77.209)
    setFrp(65)
    setBrightness(360)
    setConfidence(85)
    setDaynight('N')
    setResult(null)
    setError(null)
  }

  const getRiskColor = (level?: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30'
      case 'HIGH':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/30'
      case 'MODERATE':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30'
      case 'LOW':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700'
    }
  }

  return (
    <Card className="bg-slate-900/80 border-slate-800 shadow-xl backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-slate-800/60 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <FlaskConical className="size-5" />
          </div>
          <div>
            <CardTitle className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>AI Anomaly Simulation Sandbox</span>
              <Badge variant="outline" className="text-[10px] bg-purple-500/10 border-purple-500/30 text-purple-300">
                Live Inference
              </Badge>
            </CardTitle>
            <p className="text-xs text-slate-400">
              Test synthetic satellite thermal signatures and verify AI risk decomposition in real-time.
            </p>
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={resetSimulation}
          className="h-8 text-xs bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
        >
          <RotateCcw className="size-3.5 mr-1 text-slate-400" />
          Reset
        </Button>
      </CardHeader>

      <CardContent className="pt-4 space-y-5">
        {/* Quick Presets */}
        <div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="size-3.5 text-purple-400" />
            <span>Preset Thermal Scenarios</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.name}
                onClick={() => applyPreset(p)}
                className="text-left p-2 rounded-lg bg-slate-950 border border-slate-800/80 hover:border-purple-500/50 hover:bg-purple-950/20 transition-all text-xs group"
              >
                <div className="font-semibold text-slate-200 group-hover:text-purple-300 transition-colors">
                  {p.name}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">{p.frp} MW • {p.daynight === 'N' ? '🌙 Night' : '☀️ Day'}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Parameter Sliders & Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          {/* Coordinates & FRP */}
          <div className="space-y-3.5">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Latitude (°N)</label>
                <input
                  type="number"
                  step="0.001"
                  value={lat}
                  onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-2.5 py-1 text-xs text-slate-100 font-mono focus:border-purple-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Longitude (°E)</label>
                <input
                  type="number"
                  step="0.001"
                  value={lon}
                  onChange={(e) => setLon(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-2.5 py-1 text-xs text-slate-100 font-mono focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 font-medium">Fire Radiative Power (FRP):</span>
                <span className="text-amber-400 font-mono font-bold">{frp.toFixed(1)} MW</span>
              </div>
              <input
                type="range"
                min="1"
                max="250"
                step="1"
                value={frp}
                onChange={(e) => setFrp(parseFloat(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 font-medium">Brightness Temperature:</span>
                <span className="text-yellow-400 font-mono font-bold">{brightness.toFixed(1)} K</span>
              </div>
              <input
                type="range"
                min="290"
                max="450"
                step="1"
                value={brightness}
                onChange={(e) => setBrightness(parseFloat(e.target.value))}
                className="w-full accent-yellow-500 cursor-pointer"
              />
            </div>
          </div>

          {/* Confidence & Toggles */}
          <div className="space-y-3.5">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400 font-medium">Satellite Confidence:</span>
                <span className="text-cyan-400 font-mono font-bold">{confidence}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="1"
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between gap-4 pt-1">
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Acquisition Pass</label>
                <div className="flex rounded-lg bg-slate-900 border border-slate-800 p-0.5 text-xs">
                  <button
                    onClick={() => setDaynight('D')}
                    className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                      daynight === 'D' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Sun className="size-3" />
                    Day
                  </button>
                  <button
                    onClick={() => setDaynight('N')}
                    className={`px-3 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                      daynight === 'N' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Moon className="size-3" />
                    Night
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-4">
                <input
                  type="checkbox"
                  id="queryOsm"
                  checked={queryOsm}
                  onChange={(e) => setQueryOsm(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-700 accent-purple-500 cursor-pointer"
                />
                <label htmlFor="queryOsm" className="text-xs text-slate-300 cursor-pointer font-medium">
                  Query Overpass OSM
                </label>
              </div>
            </div>

            <Button
              onClick={runSimulation}
              disabled={loading}
              className="w-full h-9 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-900/30 transition-all"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="size-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Computing AI Inference...</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <Play className="size-3.5 fill-current" />
                  <span>Run Live AI Classification</span>
                </div>
              )}
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Live Simulation Results Display */}
        {result && (
          <div className="p-4 rounded-xl bg-slate-950 border border-purple-500/30 space-y-4 animate-in fade-in duration-300">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block">
                  Predicted Classification
                </span>
                <span className="text-lg font-extrabold text-slate-100 capitalize">
                  {result.predicted_class.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={`text-xs px-2.5 py-1 font-bold ${getRiskColor(result.risk_level)}`}>
                  {result.risk_level} RISK ({result.risk_score.toFixed(0)}/100)
                </Badge>
                <Badge variant="outline" className="text-xs px-2.5 py-1 border-purple-500/30 text-purple-300 bg-purple-500/10">
                  Confidence: {(result.classification_confidence * 100).toFixed(1)}%
                </Badge>
              </div>
            </div>

            {/* Explainable 5-Factor Risk Decomposition */}
            {result.risk_breakdown && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Explainable Multi-Factor Risk Decomposition</span>
                  <span className="text-purple-400 font-mono text-[11px] font-bold">Total: {result.risk_score.toFixed(0)} pts</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
                  <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block">FRP Magnitude</span>
                    <span className="text-sm font-bold text-amber-400 font-mono">
                      {result.risk_breakdown.frp_subscore.toFixed(0)} / 30
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block">Industrial Proximity</span>
                    <span className="text-sm font-bold text-indigo-400 font-mono">
                      {result.risk_breakdown.industrial_proximity_subscore.toFixed(0)} / 25
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block">Cluster Persistence</span>
                    <span className="text-sm font-bold text-cyan-400 font-mono">
                      {result.risk_breakdown.persistence_subscore.toFixed(0)} / 20
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block">Confidence Score</span>
                    <span className="text-sm font-bold text-emerald-400 font-mono">
                      {result.risk_breakdown.confidence_subscore.toFixed(0)} / 15
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block">Nocturnal Detection</span>
                    <span className="text-sm font-bold text-purple-400 font-mono">
                      {result.risk_breakdown.nocturnal_subscore.toFixed(0)} / 10
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* AI Decision Rationale List */}
            {result.reasons && result.reasons.length > 0 && (
              <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-1">
                <span className="font-bold text-slate-200 block mb-1 text-[11px]">Key Risk Rationale:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                  {result.reasons.map((r, i) => (
                    <li key={i} className="text-[11px] text-slate-300">
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
