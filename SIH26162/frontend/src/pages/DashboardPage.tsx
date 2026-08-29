import { useEffect, useState } from 'react'
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
import { DetailPanel } from '@/components/dashboard/DetailPanel'
import { AnalyticsCharts } from '@/components/dashboard/AnalyticsCharts'
import { ObservationsTable } from '@/components/dashboard/ObservationsTable'
import { SystemHealthModal } from '@/components/dashboard/SystemHealthModal'
import { SimulationSandbox } from '@/components/dashboard/SimulationSandbox'
import { ApiService } from '@/lib/api'
import { exportToCSV } from '@/lib/exportUtils'
import { useDashboardStore, DEMO_SCENARIOS } from '@/store/useDashboardStore'

export function DashboardPage() {
  const observations = useDashboardStore((s) => s.observations)
  const totalObsCount = useDashboardStore((s) => s.totalObsCount)
  const clusters = useDashboardStore((s) => s.clusters)
  const totalClustersCount = useDashboardStore((s) => s.totalClustersCount)
  const classifications = useDashboardStore((s) => s.classifications)

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
    <div className="flex flex-col gap-6 py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto min-h-screen">
      {/* Top Header & Command Center Status */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2">
              <span>Command Center</span>
              {isDemoMode ? (
                <span className="text-purple-400 font-mono text-sm sm:text-base font-semibold px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 animate-pulse">
                  ⚗ DEMO MODE
                </span>
              ) : (
                <span className="text-emerald-400 font-mono text-sm sm:text-base font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">
                  LIVE
                </span>
              )}
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 flex items-center gap-2">
            <span>Near-Real-Time Thermal Anomaly &amp; Persistent Industrial Fire Detection System</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400 font-mono text-xs">
              Updated {lastRefreshed.toLocaleTimeString()}
            </span>
          </p>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Live Auto-Pulse Ticker */}
          <div className="flex items-center rounded-lg bg-slate-900 border border-slate-800 p-0.5 text-xs font-mono">
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

          {/* Export CSV Intelligence Report */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => exportToCSV(observations, classifications, clusters)}
            disabled={observations.length === 0}
            className="h-8 text-xs bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
            title="Download Full Intelligence Report in CSV format"
          >
            <Download className="size-3.5 mr-1 text-cyan-400" />
            <span className="hidden sm:inline">Export Report</span>
          </Button>

          {/* Live / Demo Mode Toggle */}
          <button
            onClick={() => setDemoMode(!isDemoMode)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono border transition-all ${
              isDemoMode
                ? 'bg-purple-900/30 border-purple-500/40 text-purple-300 hover:bg-purple-900/50'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
            title={isDemoMode ? 'Switch to Live Mode' : 'Switch to Demo Mode — controlled SIH presentation'}
          >
            {isDemoMode ? (
              <>
                <Satellite className="size-3 text-emerald-400" />
                <span className="text-emerald-400 font-bold">Switch to LIVE</span>
              </>
            ) : (
              <>
                <FlaskConical className="size-3 text-purple-400" />
                <span className="text-purple-400 font-bold">DEMO MODE</span>
              </>
            )}
          </button>

          {/* Data Source Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-800 text-slate-300">
            <Radio className="size-3 text-emerald-400 animate-pulse" />
            <span className="text-emerald-400 font-bold">NASA FIRMS</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">PostGIS + AI</span>
          </div>

          {/* System Diagnostics Trigger */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => setIsHealthModalOpen(true)}
            className="h-8 text-xs bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
          >
            <Activity className="size-3.5 mr-1.5 text-cyan-400" />
            <span>Diagnostics</span>
          </Button>

          {/* Refresh Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={fetchDashboardData}
            disabled={loading}
            className="h-8 text-xs bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
          >
            <RefreshCw className={`size-3.5 mr-1.5 text-amber-500 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>

          {/* View Mode Switcher */}
          <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-xs">
            <button
              onClick={() => setViewMode('split')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'split'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Split View: Map and Telemetry Side-by-Side"
            >
              <Layers className="size-3.5" />
              <span className="hidden sm:inline">Split</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'map'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Full Map View"
            >
              <MapIcon className="size-3.5" />
              <span className="hidden sm:inline">Map</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'table'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Data Table View"
            >
              <TableIcon className="size-3.5" />
              <span className="hidden sm:inline">Table</span>
            </button>
            <button
              onClick={() => setViewMode('analytics')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'analytics'
                  ? 'bg-amber-500 text-slate-950 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Analytics & Charts"
            >
              <BarChart3 className="size-3.5" />
              <span className="hidden sm:inline">Analytics</span>
            </button>
            <button
              onClick={() => setViewMode('simulator')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === 'simulator'
                  ? 'bg-purple-600 text-white font-semibold shadow-sm'
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
          <div className="flex items-center justify-between">
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

      {/* Main Workspace Layout */}
      {viewMode === 'split' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Interactive Map (7 cols on large screens) */}
          <div className="lg:col-span-7 space-y-6">
            <CommandCenterMap
              observations={observations}
              clusters={clusters}
              selectedEntity={selectedEntity}
              onSelectEntity={(entity) => setSelectedEntity(entity)}
              onBoundsChange={handleMapBoundsChange}
              useMapBounds={filters.useMapBounds}
              loading={loading}
            />

            {/* Inline Analytics Preview */}
            <AnalyticsCharts
              observations={observations}
              classifications={classifications}
              clusters={clusters}
            />
          </div>

          {/* Detail Telemetry & AI Inspection Panel (5 cols on large screens) */}
          <div className="lg:col-span-5 space-y-6">
            {selectedEntity ? (
              <DetailPanel
                selectedEntity={selectedEntity}
                onClose={() => setSelectedEntity(null)}
                onClassificationComplete={() => {
                  // Refresh stored classifications count
                  ApiService.getClassifications(filters, 1, 100).then((res) => {
                    useDashboardStore.setState({ classifications: res.classifications || [] })
                  })
                }}
              />
            ) : (
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-8 text-center space-y-3 backdrop-blur shadow-xl">
                <div className="size-12 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
                  <Flame className="size-6" />
                </div>
                <h3 className="text-base font-bold text-slate-100">Select an Anomaly on the Map</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  Click any active NASA FIRMS observation marker or persistent industrial cluster to inspect multi-factor explainable risk scores, spectral telemetry, and real-time AI classification.
                </p>
                <div className="pt-2">
                  {observations.length > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setSelectedEntity({ type: 'observation', data: observations[0] })
                      }
                      className="text-xs bg-slate-950 border-slate-800 text-amber-400 hover:bg-slate-800"
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

      {viewMode === 'map' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className={selectedEntity ? 'lg:col-span-8' : 'lg:col-span-12'}>
            <CommandCenterMap
              observations={observations}
              clusters={clusters}
              selectedEntity={selectedEntity}
              onSelectEntity={(entity) => setSelectedEntity(entity)}
              onBoundsChange={handleMapBoundsChange}
              useMapBounds={filters.useMapBounds}
              loading={loading}
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
