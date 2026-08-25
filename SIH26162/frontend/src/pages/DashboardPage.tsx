import { useState, useEffect, useCallback } from 'react'
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
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { KPICards } from '@/components/dashboard/KPICards'
import { FilterBar } from '@/components/dashboard/FilterBar'
import { CommandCenterMap } from '@/components/dashboard/CommandCenterMap'
import { DetailPanel } from '@/components/dashboard/DetailPanel'
import { AnalyticsCharts } from '@/components/dashboard/AnalyticsCharts'
import { ObservationsTable } from '@/components/dashboard/ObservationsTable'
import { SystemHealthModal } from '@/components/dashboard/SystemHealthModal'
import { ApiService } from '@/lib/api'
import type {
  FIRMSObservation,
  PersistentThermalCluster,
  ClassificationRecord,
  SelectedEntity,
  DashboardFilterState,
  DatabaseHealth,
} from '@/types'

export function DashboardPage() {
  // Primary Data State
  const [observations, setObservations] = useState<FIRMSObservation[]>([])
  const [totalObsCount, setTotalObsCount] = useState<number>(0)
  const [clusters, setClusters] = useState<PersistentThermalCluster[]>([])
  const [totalClustersCount, setTotalClustersCount] = useState<number>(0)
  const [classifications, setClassifications] = useState<ClassificationRecord[]>([])

  // Selection & UI State
  const [selectedEntity, setSelectedEntity] = useState<SelectedEntity | null>(null)
  const [viewMode, setViewMode] = useState<'split' | 'map' | 'table' | 'analytics'>('split')
  const [isHealthModalOpen, setIsHealthModalOpen] = useState<boolean>(false)
  const [dbHealth, setDbHealth] = useState<DatabaseHealth | null>(null)

  // Filtering & Pagination State
  const [filters, setFilters] = useState<DashboardFilterState>({
    satellite: 'ALL',
    predictedClass: 'ALL',
    riskLevel: 'ALL',
    minConfidence: 0,
    minFRP: 0,
    useMapBounds: false,
  })
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize] = useState<number>(50)
  const [totalPages, setTotalPages] = useState<number>(1)

  // Status & Error State
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [isOffline, setIsOffline] = useState<boolean>(false)
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date())

  // Fetch real data from backend APIs
  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // 1. Fetch Observations
      const obsRes = await ApiService.getObservations(filters, currentPage, pageSize)
      setObservations(obsRes.observations || [])
      setTotalObsCount(obsRes.total || 0)
      setTotalPages(obsRes.total_pages || 1)

      // 2. Fetch Persistent Clusters
      const clustersRes = await ApiService.getPersistentSources(filters, 200, 0)
      setClusters(clustersRes.clusters || [])
      setTotalClustersCount(clustersRes.total_clusters || 0)

      // 3. Fetch Stored Classifications
      const clfRes = await ApiService.getClassifications(filters, 1, 100)
      setClassifications(clfRes.classifications || [])

      // 4. Fetch DB Health
      const dbRes = await ApiService.getDatabaseHealth().catch(() => null)
      setDbHealth(dbRes)

      setIsOffline(false)
      setLastRefreshed(new Date())
    } catch (err: unknown) {
      console.error('Failed to load dashboard telemetry:', err)
      setIsOffline(true)
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to communicate with SIH26162 FastAPI / PostGIS backend.'
      )
    } finally {
      setLoading(false)
    }
  }, [filters, currentPage, pageSize])

  // Initial Load & on filter/page change
  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  // Handle map bounding box updates
  const handleMapBoundsChange = (bbox: [number, number, number, number]) => {
    if (filters.useMapBounds) {
      setFilters((prev) => ({ ...prev, bbox }))
    }
  }

  // Handle Filter Reset
  const handleResetFilters = () => {
    setFilters({
      satellite: 'ALL',
      predictedClass: 'ALL',
      riskLevel: 'ALL',
      minConfidence: 0,
      minFRP: 0,
      useMapBounds: false,
    })
    setCurrentPage(1)
  }

  return (
    <div className="flex flex-col gap-6 py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto min-h-screen">
      {/* Top Header & Command Center Status */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2">
              <span>Command Center</span>
              <span className="text-amber-500 font-mono text-sm sm:text-base font-semibold px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30">
                PHASE 4 PRODUCTION
              </span>
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 flex items-center gap-2">
            <span>Real-time Thermal Anomaly & Persistent Industrial Fire Detection System</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400 font-mono text-xs">
              Updated {lastRefreshed.toLocaleTimeString()}
            </span>
          </p>
        </div>

        {/* Action Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Data Source Badge: Real Data */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-900 border border-slate-800 text-slate-300">
            <Radio className="size-3 text-emerald-400 animate-pulse" />
            <span className="text-emerald-400 font-bold">LIVE TELEMETRY</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">PostGIS + FIRMS</span>
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
            onClick={loadDashboardData}
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
            onClick={loadDashboardData}
            className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs h-7 px-3"
          >
            Retry Connection
          </Button>
        </div>
      )}

      {/* Real-time KPI Telemetry Cards */}
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
        onFiltersChange={(newFilters) => {
          setFilters(newFilters)
          setCurrentPage(1)
        }}
        onReset={handleResetFilters}
        totalCount={totalObsCount}
        loading={loading}
      />

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
                    setClassifications(res.classifications || [])
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
                    setClassifications(res.classifications || [])
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
