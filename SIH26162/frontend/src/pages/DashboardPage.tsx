import { useEffect, useState, useMemo } from 'react'
import {
  Flame,
  Activity,
  Layers,
  Map as MapIcon,
  Table as TableIcon,
  BarChart3,
  RefreshCw,
  AlertCircle,
  Radio,
  FlaskConical,
  Satellite,
  Download,
  Timer,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { KPICards } from '@/components/dashboard/KPICards'
import { FilterBar } from '@/components/dashboard/FilterBar'
import { CommandCenterMap } from '@/components/dashboard/CommandCenterMap'
import { TimelineScrubberBar } from '@/components/dashboard/TimelineScrubberBar'
import { DetailPanel } from '@/components/dashboard/DetailPanel'
import { AnalyticsCharts } from '@/components/dashboard/AnalyticsCharts'
import { ObservationsTable } from '@/components/dashboard/ObservationsTable'
import { SystemHealthModal } from '@/components/dashboard/SystemHealthModal'
import { SimulationSandbox } from '@/components/dashboard/SimulationSandbox'
import { LiveAlertRadar } from '@/components/dashboard/LiveAlertRadar'
import { ApiService } from '@/lib/api'
import { exportToCSV } from '@/lib/exportUtils'
import { useDashboardStore, DEMO_SCENARIOS } from '@/store/useDashboardStore'

export function DashboardPage() {
  const [targetedAlertLocation, setTargetedAlertLocation] = useState<{ lat: number; lon: number; label?: string } | null>(null)

  const observations = useDashboardStore((s) => s.observations)
  const totalObsCount = useDashboardStore((s) => s.totalObsCount)
  const clusters = useDashboardStore((s) => s.clusters)
  const totalClustersCount = useDashboardStore((s) => s.totalClustersCount)
  const classifications = useDashboardStore((s) => s.classifications)
  const facilities = useDashboardStore((s) => s.facilities)
  const selectedEntity = useDashboardStore((s) => s.selectedEntity)

  const viewMode = useDashboardStore((s) => s.viewMode)
  const isHealthModalOpen = useDashboardStore((s) => s.isHealthModalOpen)
  const dbHealth = useDashboardStore((s) => s.dbHealth)

  const autoPulseInterval = useDashboardStore((s) => s.autoPulseInterval)
  const filters = useDashboardStore((s) => s.filters)
  const currentPage = useDashboardStore((s) => s.currentPage)
  const totalPages = useDashboardStore((s) => s.totalPages)

  const loading = useDashboardStore((s) => s.loading)
  const error = useDashboardStore((s) => s.error)
  const isOffline = useDashboardStore((s) => s.isOffline)
  const lastRefreshed = useDashboardStore((s) => s.lastRefreshed)

  const isDemoMode = useDashboardStore((s) => s.isDemoMode)
  const activeDemoScenario = useDashboardStore((s) => s.activeDemoScenario)

  const fetchDashboardData = useDashboardStore((s) => s.fetchDashboardData)
  const setSelectedEntity = useDashboardStore((s) => s.setSelectedEntity)
  const setViewMode = useDashboardStore((s) => s.setViewMode)
  const setAutoPulseInterval = useDashboardStore((s) => s.setAutoPulseInterval)
  const setFilters = useDashboardStore((s) => s.setFilters)
  const resetFilters = useDashboardStore((s) => s.resetFilters)
  const setCurrentPage = useDashboardStore((s) => s.setCurrentPage)
  const setIsHealthModalOpen = useDashboardStore((s) => s.setIsHealthModalOpen)
  const setDemoMode = useDashboardStore((s) => s.setDemoMode)
  const activateDemoScenario = useDashboardStore((s) => s.activateDemoScenario)
  const handleMapBoundsChange = useDashboardStore((s) => s.handleMapBoundsChange)

  const [countdown, setCountdown] = useState<number>(autoPulseInterval)

  // Temporal Playback State (Fix B: Lifted from map)
  const [selectedDateIndex, setSelectedDateIndex] = useState<number | null>(null)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1200)

  // Unique chronological observation frames (multi-day or hourly satellite passes)
  const uniqueFrames = useMemo(() => {
    const dates = new Set<string>()
    observations.forEach((o) => {
      if (o.acq_datetime) {
        dates.add(o.acq_datetime.slice(0, 10))
      }
    })
    const dateArr = Array.from(dates).sort()
    if (dateArr.length > 1) {
      return dateArr
    }

    // If single calendar day, cluster by satellite pass hours
    const hourFrames = new Set<string>()
    observations.forEach((o) => {
      if (o.acq_datetime) {
        hourFrames.add(o.acq_datetime.slice(5, 13) + ':00')
      }
    })
    const hourArr = Array.from(hourFrames).sort()
    return hourArr.length > 0 ? hourArr : ['All Telemetry']
  }, [observations])

  // Active observations filtered by selected timeline frame
  const activeObservations = useMemo(() => {
    if (selectedDateIndex === null || !uniqueFrames[selectedDateIndex]) {
      return observations
    }
    const targetFrame = uniqueFrames[selectedDateIndex]
    if (targetFrame === 'All Telemetry') return observations
    return observations.filter((o) => {
      if (!o.acq_datetime) return true
      return (
        o.acq_datetime.startsWith(targetFrame) ||
        o.acq_datetime.includes(targetFrame.replace(':00', ''))
      )
    })
  }, [observations, selectedDateIndex, uniqueFrames])

  // Timeline Playback Timer Effect
  useEffect(() => {
    if (!isPlaying || uniqueFrames.length === 0) return
    const timer = setInterval(() => {
      setSelectedDateIndex((prev) => {
        if (prev === null || prev >= uniqueFrames.length - 1) {
          return 0
        }
        return prev + 1
      })
    }, playbackSpeed)
    return () => clearInterval(timer)
  }, [isPlaying, uniqueFrames, playbackSpeed])

  // Initial Data Fetch
  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  // Live Auto-Pulse Polling Effect
  useEffect(() => {
    if (autoPulseInterval <= 0) return

    setCountdown(autoPulseInterval)
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          fetchDashboardData()
          return autoPulseInterval
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [autoPulseInterval, fetchDashboardData])

  return (
    // FIX C: Full-width layout container with generous maximum width, eliminating dead side gutters
    <div className="flex flex-col gap-5 py-5 px-3 sm:px-5 lg:px-7 max-w-[1850px] w-full mx-auto min-h-screen">

      {/* ═══════════════════════════════════════════════════
          PYROS — 2-Row Command Header (Fix D: Crisp Hierarchy)
      ═══════════════════════════════════════════════════ */}
      <div className="flex flex-col gap-3 border-b border-slate-800 pb-4">

        {/* ── Row 1: Brand Title + Primary Controls ── */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">

          {/* Brand */}
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight flex items-center gap-2.5">
                <span className="tracking-widest bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                  PYROS
                </span>
                {isDemoMode ? (
                  <span className="text-purple-400 font-mono text-xs font-bold px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 animate-pulse">
                    ⚗ DEMO MODE
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-emerald-400 font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">
                    <span className="relative flex size-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                      <span className="relative inline-flex size-2 rounded-full bg-red-500" />
                    </span>
                    LIVE TELEMETRY
                  </span>
                )}
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
              <span className="font-medium text-slate-300">Industrial Fire &amp; Thermal AI Detection System</span>
              <span className="text-slate-600 hidden sm:inline">•</span>
              <span className="text-slate-500 font-mono text-xs">
                Updated {lastRefreshed.toLocaleTimeString()}
              </span>
            </p>
          </div>

          {/* Primary Controls: Pulse + Refresh + View Switcher */}
          <div className="flex flex-wrap items-center gap-2">

            {/* Live Auto-Pulse Ticker */}
            <div className="flex items-center rounded-lg bg-slate-900 border border-slate-800 p-0.5 text-xs font-mono shadow-sm">
              <button
                onClick={() => {
                  const next = autoPulseInterval === 0 ? 30 : autoPulseInterval === 30 ? 15 : autoPulseInterval === 15 ? 60 : 0
                  setAutoPulseInterval(next)
                }}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                  autoPulseInterval > 0
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Toggle Live Auto-Pulse Telemetry Polling"
              >
                <Timer className={`size-3.5 ${autoPulseInterval > 0 ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
                <span>{autoPulseInterval > 0 ? `Pulse: ${countdown}s` : 'Auto-Pulse: Off'}</span>
              </button>
            </div>

            {/* Refresh */}
            <Button
              size="sm"
              variant="outline"
              onClick={fetchDashboardData}
              disabled={loading}
              className="h-8 text-xs bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800 shadow-sm font-semibold"
            >
              <RefreshCw className={`size-3.5 mr-1.5 text-amber-500 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </Button>

            {/* View Mode Switcher */}
            <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-xs shadow-sm">
              <button
                onClick={() => setViewMode('split')}
                className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
                  viewMode === 'split'
                    ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Split View: Map and Telemetry Side-by-Side"
              >
                <Layers className="size-3.5" />
                <span className="hidden sm:inline">Split</span>
              </button>
              <button
                onClick={() => setViewMode('map')}
                className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
                  viewMode === 'map'
                    ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Full Map View"
              >
                <MapIcon className="size-3.5" />
                <span className="hidden sm:inline">Map</span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Data Table View"
              >
                <TableIcon className="size-3.5" />
                <span className="hidden sm:inline">Table</span>
              </button>
              <button
                onClick={() => setViewMode('analytics')}
                className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
                  viewMode === 'analytics'
                    ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Analytics &amp; Charts"
              >
                <BarChart3 className="size-3.5" />
                <span className="hidden sm:inline">Analytics</span>
              </button>
              <button
                onClick={() => setViewMode('simulator')}
                className={`flex items-center gap-1 px-3 py-1 rounded-md font-medium transition-all ${
                  viewMode === 'simulator'
                    ? 'bg-purple-600 text-white font-bold shadow-sm'
                    : 'text-purple-400 hover:text-purple-300'
                }`}
                title="Interactive AI Anomaly Sandbox Simulator"
              >
                <FlaskConical className="size-3.5" />
                <span className="hidden sm:inline">AI Sandbox</span>
              </button>
            </div>
          </div>
        </div>

        {/* ── Row 2: Status Badge + Secondary Actions ── */}
        <div className="flex flex-wrap items-center justify-between gap-2">

          {/* Status: Data Source */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono bg-slate-900/90 border border-slate-800 text-slate-300">
            <Radio className="size-3 text-emerald-400 animate-pulse" />
            <span className="text-emerald-400 font-bold">NASA FIRMS NRT</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-300 font-medium">PostGIS Spatial Engine</span>
            <span className="text-slate-600">|</span>
            <span className="text-cyan-400 font-medium">PyTorch AI</span>
          </div>

          {/* Secondary Actions */}
          <div className="flex flex-wrap items-center gap-2">

            {/* Live / Demo Mode Toggle */}
            <button
              onClick={() => setDemoMode(!isDemoMode)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-mono border transition-all ${
                isDemoMode
                  ? 'bg-purple-900/30 border-purple-500/40 text-purple-300 hover:bg-purple-900/50 font-bold'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
              title={isDemoMode ? 'Switch to Live Mode' : 'Switch to Demo Mode — controlled SIH presentation'}
            >
              {isDemoMode ? (
                <>
                  <Satellite className="size-3 text-emerald-400" />
                  <span className="text-emerald-400 font-bold">→ SWITCH TO LIVE</span>
                </>
              ) : (
                <>
                  <FlaskConical className="size-3 text-purple-400" />
                  <span className="text-purple-300">DEMO MODE</span>
                </>
              )}
            </button>

            {/* Export CSV Intelligence Report */}
            <Button
              size="sm"
              variant="outline"
              onClick={() => exportToCSV(observations, classifications, clusters)}
              disabled={observations.length === 0}
              className="h-7 text-xs bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
              title="Download Full Intelligence Report in CSV format"
            >
              <Download className="size-3.5 mr-1 text-cyan-400" />
              <span>Export CSV</span>
            </Button>

            {/* System Diagnostics Trigger */}
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsHealthModalOpen(true)}
              className="h-7 text-xs bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
            >
              <Activity className="size-3.5 mr-1.5 text-cyan-400" />
              <span>Diagnostics</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Offline / Backend Error Banner */}
      {isOffline && (
        <div className="bg-rose-950/40 border border-rose-500/40 rounded-xl p-4 flex items-center justify-between gap-4 text-rose-200 text-xs shadow-lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="size-5 text-rose-400 shrink-0" />
            <div>
              <span className="font-bold text-rose-300">Backend Connection Notice: </span>
              <span>{error || 'Cannot reach FastAPI backend server on http://localhost:8000.'}</span>
            </div>
          </div>
          <Button
            size="sm"
            onClick={fetchDashboardData}
            className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs h-7 px-3"
          >
            Retry Connection
          </Button>
        </div>
      )}

      {/* Demo Mode Banner & Scenario Selector */}
      {isDemoMode && (
        <div className="bg-purple-950/30 border border-purple-500/30 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <FlaskConical className="size-4 text-purple-400" />
              <span className="text-sm font-bold text-purple-300">SIH DEMO MODE — Controlled Presentation Scenarios</span>
              <Badge variant="outline" className="text-[10px] border-purple-500/30 text-purple-400 bg-purple-500/10">
                Real DB Records
              </Badge>
            </div>
            <span className="text-[11px] text-purple-400/70 font-mono">Production data is read-only. No records are modified.</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {DEMO_SCENARIOS.map((s, idx) => (
              <button
                key={s.id}
                onClick={() => activateDemoScenario(idx)}
                className={`text-left p-2.5 rounded-lg border text-xs transition-all ${
                  activeDemoScenario === idx
                    ? 'bg-purple-600/20 border-purple-500/60 text-purple-200'
                    : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-purple-500/40 hover:text-slate-200'
                }`}
              >
                <div className="font-bold text-[10px] font-mono mb-0.5 text-purple-400">Scenario {s.id}</div>
                <div className="font-semibold text-slate-200 leading-tight">{s.label}</div>
                <div className="text-[10px] text-slate-500 mt-1 leading-tight">{s.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Live SSE Alert Radar Bar */}
      <LiveAlertRadar
        onFocusCoordinates={(lat, lon, alert) => {
          setTargetedAlertLocation({
            lat,
            lon,
            label: `${alert.risk_level}: ${alert.predicted_class} (${alert.frp_mw} MW) - ${alert.nearest_facility || alert.location_name}`,
          })
        }}
      />

      {/* Near-Real-Time KPI Telemetry Cards */}
      <KPICards
        observations={observations}
        clusters={clusters}
        classifications={classifications}
        totalObservationsCount={totalObsCount}
        totalClustersCount={totalClustersCount}
        loading={loading}
        isDatabaseConnected={dbHealth?.database_connected ?? true}
      />

      {/* Sensor & Spatial Filter Console */}
      <FilterBar
        filters={filters}
        onFiltersChange={(newFilters) => setFilters(newFilters)}
        onReset={resetFilters}
        totalCount={totalObsCount}
        loading={loading}
      />

      {/* AI Simulation Sandbox Mode */}
      {viewMode === 'simulator' && (
        <div className="space-y-6">
          <SimulationSandbox />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          Main Workspace: Split View Mode (Fix C & Fix B)
      ═══════════════════════════════════════════════════ */}
      {viewMode === 'split' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Interactive Map & Timeline Scrubber (7 cols lg, 8 cols xl for maximum map visibility) */}
          <div className="lg:col-span-7 xl:col-span-8 space-y-3">
            {/* Map Canvas with generous height */}
            <div className="w-full h-[540px] sm:h-[600px] lg:h-[640px] xl:h-[680px]">
              <CommandCenterMap
                observations={observations}
                clusters={clusters}
                facilities={facilities}
                selectedEntity={selectedEntity}
                onSelectEntity={(entity) => setSelectedEntity(entity)}
                onBoundsChange={handleMapBoundsChange}
                useMapBounds={filters.useMapBounds}
                loading={loading}
                targetedAlertLocation={targetedAlertLocation}
                activeObservations={activeObservations}
              />
            </div>

            {/* FIX B: Dedicated Timeline Scrubber Bar outside the map */}
            <TimelineScrubberBar
              uniqueFrames={uniqueFrames}
              selectedDateIndex={selectedDateIndex}
              setSelectedDateIndex={setSelectedDateIndex}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              activeCount={activeObservations.length}
              totalCount={observations.length}
              playbackSpeed={playbackSpeed}
              onSpeedToggle={() => setPlaybackSpeed((s) => (s <= 600 ? 1200 : 600))}
            />

            {/* Inline Analytics Preview */}
            <AnalyticsCharts
              observations={observations}
              classifications={classifications}
              clusters={clusters}
            />
          </div>

          {/* Detail Telemetry & AI Inspection Panel (5 cols lg, 4 cols xl) */}
          <div className="lg:col-span-5 xl:col-span-4 space-y-4">
            {selectedEntity ? (
              <DetailPanel
                selectedEntity={selectedEntity}
                onClose={() => setSelectedEntity(null)}
                onClassificationComplete={() => {
                  ApiService.getClassifications(filters, 1, 100).then((res) => {
                    useDashboardStore.setState({ classifications: res.classifications || [] })
                  })
                }}
              />
            ) : (
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-7 text-center space-y-3 backdrop-blur shadow-xl">
                <div className="size-12 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
                  <Flame className="size-6" />
                </div>
                <h3 className="text-base font-bold text-slate-100">Select an Anomaly on the Map</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  Click any active NASA FIRMS observation marker or persistent industrial cluster to inspect
                  multi-factor explainable risk scores, spectral telemetry, and real-time AI classification.
                </p>
                <div className="pt-2">
                  {observations.length > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setSelectedEntity({ type: 'observation', data: observations[0] })
                      }
                      className="text-xs bg-slate-950 border-slate-800 text-amber-400 hover:bg-slate-800 shadow-sm font-semibold"
                    >
                      Inspect First Available Observation
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Quick Data Feed preview */}
            <ObservationsTable
              observations={observations.slice(0, 10)}
              clusters={clusters.slice(0, 10)}
              classifications={classifications.slice(0, 10)}
              selectedEntity={selectedEntity}
              onSelectEntity={(entity) => setSelectedEntity(entity)}
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={totalObsCount}
              onPageChange={(page) => setCurrentPage(page)}
              loading={loading}
            />
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          Full Map View Mode
      ═══════════════════════════════════════════════════ */}
      {viewMode === 'map' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          <div className={`${selectedEntity ? 'lg:col-span-8' : 'lg:col-span-12'} space-y-3`}>
            <div className="w-full h-[620px] sm:h-[700px] lg:h-[780px]">
              <CommandCenterMap
                observations={observations}
                clusters={clusters}
                facilities={facilities}
                selectedEntity={selectedEntity}
                onSelectEntity={(entity) => setSelectedEntity(entity)}
                onBoundsChange={handleMapBoundsChange}
                useMapBounds={filters.useMapBounds}
                loading={loading}
                targetedAlertLocation={targetedAlertLocation}
                activeObservations={activeObservations}
              />
            </div>

            {/* Timeline Scrubber Bar */}
            <TimelineScrubberBar
              uniqueFrames={uniqueFrames}
              selectedDateIndex={selectedDateIndex}
              setSelectedDateIndex={setSelectedDateIndex}
              isPlaying={isPlaying}
              setIsPlaying={setIsPlaying}
              activeCount={activeObservations.length}
              totalCount={observations.length}
              playbackSpeed={playbackSpeed}
              onSpeedToggle={() => setPlaybackSpeed((s) => (s <= 600 ? 1200 : 600))}
            />
          </div>
          {selectedEntity && (
            <div className="lg:col-span-4">
              <DetailPanel
                selectedEntity={selectedEntity}
                onClose={() => setSelectedEntity(null)}
                onClassificationComplete={() => {
                  ApiService.getClassifications(filters, 1, 100).then((res) => {
                    useDashboardStore.setState({ classifications: res.classifications || [] })
                  })
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          Table View Mode
      ═══════════════════════════════════════════════════ */}
      {viewMode === 'table' && (
        <div className="space-y-6">
          <ObservationsTable
            observations={observations}
            clusters={clusters}
            classifications={classifications}
            selectedEntity={selectedEntity}
            onSelectEntity={(entity) => {
              setSelectedEntity(entity)
              setViewMode('split')
            }}
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalObsCount}
            onPageChange={(page) => setCurrentPage(page)}
            loading={loading}
          />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          Analytics View Mode
      ═══════════════════════════════════════════════════ */}
      {viewMode === 'analytics' && (
        <div className="space-y-6">
          <AnalyticsCharts
            observations={observations}
            classifications={classifications}
            clusters={clusters}
          />
        </div>
      )}

      {/* System Diagnostics Modal */}
      <SystemHealthModal
        isOpen={isHealthModalOpen}
        onClose={() => setIsHealthModalOpen(false)}
      />
    </div>
  )
}
