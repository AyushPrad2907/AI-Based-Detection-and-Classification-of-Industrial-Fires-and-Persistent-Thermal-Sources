import { useEffect, useState, useRef, useCallback } from 'react'
import {
  AlertTriangle,
  Flame,
  Radio,
  Volume2,
  VolumeX,
  X,
  Crosshair,
  Satellite,
  History,
  Play,
  Square,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ApiService } from '@/lib/api'
import type { ThermalAlert, PollerStatus } from '@/types'

interface LiveAlertRadarProps {
  onFocusCoordinates?: (lat: number, lon: number, alert: ThermalAlert) => void
}

/**
 * Tactical audio chirp using HTML5 Web Audio API.
 * Synthesizes a futuristic radar blip without any external audio files.
 */
function playTacticalChirp(isCritical: boolean) {
  try {
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const now = ctx.currentTime

    const osc = ctx.createOscillator()
    const gain = ctx.createGain()

    osc.type = isCritical ? 'sawtooth' : 'sine'
    osc.frequency.setValueAtTime(isCritical ? 880 : 587.33, now) // A5 or D5
    osc.frequency.exponentialRampToValueAtTime(isCritical ? 440 : 880, now + 0.15)

    gain.gain.setValueAtTime(0.08, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.22)
  } catch {
    // AudioContext blocked or not permitted, safe fallback
  }
}

export function LiveAlertRadar({ onFocusCoordinates }: LiveAlertRadarProps) {
  const [activeAlert, setActiveAlert] = useState<ThermalAlert | null>(null)
  const [recentAlerts, setRecentAlerts] = useState<ThermalAlert[]>([])
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true)
  const [showHistory, setShowHistory] = useState<boolean>(false)
  const [pollerStatus, setPollerStatus] = useState<PollerStatus | null>(null)
  const [isTriggeringSim, setIsTriggeringSim] = useState<boolean>(false)

  const eventSourceRef = useRef<EventSource | null>(null)
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Fetch recent alerts buffer on load
  useEffect(() => {
    ApiService.getRecentAlerts(10)
      .then((alerts) => setRecentAlerts(alerts))
      .catch(() => {})

    ApiService.getPollerStatus()
      .then((status) => setPollerStatus(status))
      .catch(() => {})
  }, [])

  // Establish SSE Connection
  useEffect(() => {
    const streamUrl = ApiService.getAlertStreamUrl()
    const es = new EventSource(streamUrl)
    eventSourceRef.current = es

    es.addEventListener('open', () => {
      setIsConnected(true)
    })

    es.addEventListener('ping', () => {
      setIsConnected(true)
    })

    es.addEventListener('heartbeat', () => {
      setIsConnected(true)
    })

    es.addEventListener('thermal_alert', (e: MessageEvent) => {
      try {
        const alert: ThermalAlert = JSON.parse(e.data)
        setActiveAlert(alert)
        setRecentAlerts((prev) => [alert, ...prev.slice(0, 19)])

        if (soundEnabled) {
          playTacticalChirp(alert.risk_level === 'CRITICAL')
        }

        // Auto-dismiss current floating toast after 14 seconds
        if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current)
        dismissTimerRef.current = setTimeout(() => {
          setActiveAlert((curr) => (curr?.alert_id === alert.alert_id ? null : curr))
        }, 14000)
      } catch (err) {
        console.error('Failed to parse thermal alert SSE:', err)
      }
    })

    es.addEventListener('error', () => {
      setIsConnected(false)
    })

    return () => {
      es.close()
      if (dismissTimerRef.current) clearTimeout(dismissTimerRef.current)
    }
  }, [soundEnabled])

  // Instant simulation trigger for demos
  const handleTriggerSim = useCallback(async (zoneName?: string) => {
    try {
      setIsTriggeringSim(true)
      const res = await ApiService.simulateAlert(zoneName, true)
      if (res.alert) {
        setActiveAlert(res.alert)
        setRecentAlerts((prev) => [res.alert, ...prev.slice(0, 19)])
        if (soundEnabled) playTacticalChirp(true)
      }
    } catch (err) {
      console.error('Simulation trigger error:', err)
    } finally {
      setIsTriggeringSim(false)
    }
  }, [soundEnabled])

  // Toggle Background Poller
  const handleTogglePoller = useCallback(async () => {
    try {
      if (pollerStatus?.running) {
        const res = await ApiService.stopPoller()
        setPollerStatus(res.poller)
      } else {
        const res = await ApiService.startPoller(20)
        setPollerStatus(res.poller)
      }
    } catch (err) {
      console.error('Failed to toggle poller:', err)
    }
  }, [pollerStatus])

  return (
    <>
      {/* Mini Tactical Bar in Command Center */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2.5 shadow-lg backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center">
            <Radio className={`w-4 h-4 ${isConnected ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
            {isConnected && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-75" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Live Alert Radar
              </span>
              <Badge
                variant="outline"
                className={`text-[10px] px-1.5 py-0 uppercase font-mono ${
                  isConnected
                    ? 'border-emerald-500/40 text-emerald-400 bg-emerald-950/30'
                    : 'border-amber-500/40 text-amber-400 bg-amber-950/30'
                }`}
              >
                {isConnected ? 'SSE STREAM ACTIVE' : 'RECONNECTING'}
              </Badge>
            </div>
            <p className="text-[11px] text-slate-400">
              Near real-time NASA FIRMS & Industrial Anomaly Stream
            </p>
          </div>
        </div>

        {/* Poller Controls & Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            variant="outline"
            onClick={handleTogglePoller}
            className={`h-7 text-xs px-2.5 gap-1.5 border-slate-700 ${
              pollerStatus?.running
                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-700 hover:bg-emerald-900/50'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {pollerStatus?.running ? (
              <>
                <Square className="w-3 h-3 fill-emerald-400 text-emerald-400" />
                <span>Auto-Poller: ON (20s)</span>
              </>
            ) : (
              <>
                <Play className="w-3 h-3 text-slate-300" />
                <span>Auto-Poller: OFF</span>
              </>
            )}
          </Button>

          <Button
            size="sm"
            variant="default"
            disabled={isTriggeringSim}
            onClick={() => handleTriggerSim()}
            className="h-7 text-xs px-3 gap-1.5 bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-500 hover:to-red-500 text-white font-medium shadow"
          >
            <Sparkles className="w-3 h-3" />
            <span>{isTriggeringSim ? 'Simulating...' : '⚡ Simulate Pass'}</span>
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="h-7 w-7 p-0 text-slate-400 hover:text-slate-200"
            title={soundEnabled ? 'Mute radar audio' : 'Enable radar audio'}
          >
            {soundEnabled ? <Volume2 className="w-3.5 h-3.5 text-cyan-400" /> : <VolumeX className="w-3.5 h-3.5" />}
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowHistory(!showHistory)}
            className="h-7 text-xs px-2 gap-1 text-slate-400 hover:text-slate-200"
          >
            <History className="w-3.5 h-3.5" />
            <span>Alerts ({recentAlerts.length})</span>
            {showHistory ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </Button>
        </div>
      </div>

      {/* Floating Active Tactical Alert Card */}
      {activeAlert && (
        <div className="fixed bottom-6 right-6 z-50 max-w-md w-full animate-in slide-in-from-bottom-5 duration-300">
          <div
            className={`rounded-2xl p-4 shadow-2xl backdrop-blur-xl border ${
              activeAlert.risk_level === 'CRITICAL'
                ? 'bg-red-950/90 border-red-500/60 text-red-100 shadow-red-950/50'
                : 'bg-amber-950/90 border-amber-500/60 text-amber-100 shadow-amber-950/50'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <div
                  className={`p-2 rounded-xl ${
                    activeAlert.risk_level === 'CRITICAL' ? 'bg-red-500/20 text-red-400 animate-pulse' : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-extrabold uppercase tracking-wide">
                      {activeAlert.risk_level} THERMAL DETECTED
                    </span>
                    <Badge variant="outline" className="text-[10px] uppercase font-mono border-current">
                      {activeAlert.predicted_class.replace('_', ' ')}
                    </Badge>
                  </div>
                  <p className="text-xs font-semibold text-white mt-0.5">
                    {activeAlert.location_name || activeAlert.nearest_facility || 'Active Hotspot'}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setActiveAlert(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-3 gap-2 my-3 p-2.5 rounded-xl bg-black/40 border border-white/10 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 block">Radiative Power</span>
                <span className="font-bold text-amber-300 font-mono">{activeAlert.frp_mw} MW</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Facility Dist</span>
                <span className="font-bold text-cyan-300 font-mono">
                  {activeAlert.facility_distance_km !== undefined ? `${activeAlert.facility_distance_km} km` : 'Co-located'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Risk Score</span>
                <span className="font-bold text-red-400 font-mono">{activeAlert.risk_score} / 100</span>
              </div>
            </div>

            {activeAlert.nearest_facility && (
              <p className="text-[11px] text-slate-300 mb-3 line-clamp-1">
                🏭 Near: <span className="text-white font-medium">{activeAlert.nearest_facility}</span>
              </p>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between gap-2 pt-1 border-t border-white/10">
              <span className="text-[10px] text-slate-400 font-mono">
                {new Date(activeAlert.timestamp).toLocaleTimeString()}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveAlert(null)}
                  className="h-7 text-xs px-2.5 bg-black/20 hover:bg-black/40 border-white/20 text-slate-300"
                >
                  Dismiss
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    if (onFocusCoordinates) {
                      onFocusCoordinates(activeAlert.latitude, activeAlert.longitude, activeAlert)
                    }
                  }}
                  className="h-7 text-xs px-3 gap-1 bg-white text-slate-950 hover:bg-slate-200 font-semibold shadow"
                >
                  <Crosshair className="w-3.5 h-3.5" />
                  <span>Pan to Fire</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Expandable Alert History Drawer */}
      {showHistory && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl animate-in fade-in-50 duration-200">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Satellite className="w-4 h-4 text-cyan-400" />
              <span>Recent Ingested Satellite Alerts ({recentAlerts.length})</span>
            </h4>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowHistory(false)}
              className="h-6 text-xs text-slate-400"
            >
              Close
            </Button>
          </div>

          {recentAlerts.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">
              No recent thermal alerts recorded. Trigger a simulation or start the poller.
            </p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {recentAlerts.map((alt) => (
                <div
                  key={alt.alert_id}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition"
                >
                  <div className="flex items-center gap-2.5">
                    <Flame
                      className={`w-4 h-4 ${
                        alt.risk_level === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-semibold text-slate-200">
                          {alt.location_name || alt.nearest_facility || 'Unknown Hotspot'}
                        </span>
                        <Badge variant="outline" className="text-[9px] py-0 px-1 font-mono">
                          {alt.predicted_class}
                        </Badge>
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {alt.frp_mw} MW • {alt.confidence}% conf • {new Date(alt.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (onFocusCoordinates) {
                        onFocusCoordinates(alt.latitude, alt.longitude, alt)
                      }
                    }}
                    className="h-6 text-[11px] px-2 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/40"
                  >
                    Target
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  )
}
