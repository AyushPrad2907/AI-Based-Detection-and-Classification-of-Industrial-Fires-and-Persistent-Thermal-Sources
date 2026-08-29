import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { ApiService } from '@/lib/api'
import type {
  FIRMSObservation,
  PersistentThermalCluster,
  ClassificationRecord,
  SelectedEntity,
  DashboardFilterState,
  DatabaseHealth,
} from '@/types'

// ---------------------------------------------------------------------------
// Demo Scenario Configuration (Objective 5 — real DB-backed observations)
// ---------------------------------------------------------------------------
export const DEMO_SCENARIOS = [
  {
    id: 'A',
    label: 'Persistent Industrial Source',
    description: 'Cluster 72 — nocturnal, high-confidence, Haryana industrial belt',
    obsId: 3028,
    latitude: 29.45829,
    longitude: 76.86964,
    frp: 15.72,
    confidence: 98,
    brightness_primary: 319.27,
    brightness_secondary: 296.1,
    daynight: 'N',
    satellite: 'TERRA',
    instrument: 'MODIS',
    cluster_id: 72,
    acq_datetime: '2024-01-15T20:45:00Z',
  },
  {
    id: 'B',
    label: 'Low-Risk Anomaly',
    description: 'Low FRP / Low confidence / Daytime transient — likely agricultural',
    obsId: 2951,
    latitude: 29.703,
    longitude: 68.51967,
    frp: 1.34,
    confidence: 30,
    brightness_primary: 310.0,
    brightness_secondary: 295.0,
    daynight: 'D',
    satellite: 'N20',
    instrument: 'VIIRS',
    cluster_id: null,
    acq_datetime: '2024-01-15T10:15:00Z',
  },
  {
    id: 'C',
    label: 'High-Risk Thermal Event',
    description: 'FRP 97 MW / 100% confidence — Sri Lanka industrial fire',
    obsId: 1884,
    latitude: 6.62644,
    longitude: 81.2471,
    frp: 97.24,
    confidence: 100,
    brightness_primary: 365.07,
    brightness_secondary: 296.24,
    daynight: 'D',
    satellite: 'TERRA',
    instrument: 'MODIS',
    cluster_id: null,
    acq_datetime: '2024-01-15T07:20:00Z',
  },
  {
    id: 'D',
    label: 'Wildfire / Agricultural Burn',
    description: 'Goa coastal belt — 135 MW, moderate-confidence daytime detection',
    obsId: 2611,
    latitude: 15.77281,
    longitude: 73.70358,
    frp: 135.46,
    confidence: 30,
    brightness_primary: 337.78,
    brightness_secondary: 295.82,
    daynight: 'D',
    satellite: 'N20',
    instrument: 'VIIRS',
    cluster_id: null,
    acq_datetime: '2024-01-15T08:00:00Z',
  },
] as const

export function scenarioToObservation(s: (typeof DEMO_SCENARIOS)[number]): FIRMSObservation {
  return {
    id: s.obsId,
    latitude: s.latitude,
    longitude: s.longitude,
    brightness_primary: s.brightness_primary,
    brightness_secondary: s.brightness_secondary,
    frp: s.frp,
    confidence_score: s.confidence,
    confidence_category: s.confidence >= 80 ? 'high' : s.confidence >= 50 ? 'nominal' : 'low',
    acq_datetime: s.acq_datetime,
    satellite: s.satellite,
    instrument: s.instrument,
    daynight: s.daynight,
    scan: 0.375,
    track: 0.375,
    cluster_id: s.cluster_id ?? null,
  }
}

export interface DashboardState {
  // Primary Data
  observations: FIRMSObservation[]
  totalObsCount: number
  clusters: PersistentThermalCluster[]
  totalClustersCount: number
  classifications: ClassificationRecord[]

  // Selection & UI
  selectedEntity: SelectedEntity | null
  viewMode: 'split' | 'map' | 'table' | 'analytics' | 'simulator'
  isHealthModalOpen: boolean
  dbHealth: DatabaseHealth | null

  // Auto-Pulse Live Telemetry
  autoPulseInterval: number // 0 = off, 15, 30, 60 seconds

  // Filtering & Pagination
  filters: DashboardFilterState
  currentPage: number
  pageSize: number
  totalPages: number

  // Status & Telemetry
  loading: boolean
  error: string | null
  isOffline: boolean
  lastRefreshed: Date

  // Demo Mode
  isDemoMode: boolean
  activeDemoScenario: number
}

export interface DashboardActions {
  fetchDashboardData: () => Promise<void>
  setSelectedEntity: (entity: SelectedEntity | null) => void
  setViewMode: (mode: 'split' | 'map' | 'table' | 'analytics' | 'simulator') => void
  setAutoPulseInterval: (sec: number) => void
  setFilters: (updater: DashboardFilterState | ((prev: DashboardFilterState) => DashboardFilterState)) => void
  resetFilters: () => void
  setCurrentPage: (page: number) => void
  setIsHealthModalOpen: (open: boolean) => void
  setDemoMode: (enabled: boolean) => void
  activateDemoScenario: (index: number) => void
  handleMapBoundsChange: (bbox: [number, number, number, number]) => void
}

export type DashboardStore = DashboardState & DashboardActions

const initialFilters: DashboardFilterState = {
  satellite: 'ALL',
  predictedClass: 'ALL',
  riskLevel: 'ALL',
  minConfidence: 0,
  minFRP: 0,
  useMapBounds: false,
}

export const useDashboardStore = create<DashboardStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial State
    observations: [],
    totalObsCount: 0,
    clusters: [],
    totalClustersCount: 0,
    classifications: [],

    selectedEntity: null,
    viewMode: 'split',
    isHealthModalOpen: false,
    dbHealth: null,

    autoPulseInterval: 0,

    filters: initialFilters,
    currentPage: 1,
    pageSize: 50,
    totalPages: 1,

    loading: true,
    error: null,
    isOffline: false,
    lastRefreshed: new Date(),

    isDemoMode: false,
    activeDemoScenario: 0,

    // Actions
    fetchDashboardData: async () => {
      const { filters, currentPage, pageSize } = get()
      set({ loading: true, error: null })
      try {
        const [obsRes, clustersRes, clfRes, dbRes] = await Promise.all([
          ApiService.getObservations(filters, currentPage, pageSize),
          ApiService.getPersistentSources(filters, 200, 0),
          ApiService.getClassifications(filters, 1, 100),
          ApiService.getDatabaseHealth().catch(() => null),
        ])

        set({
          observations: obsRes.observations || [],
          totalObsCount: obsRes.total || 0,
          totalPages: obsRes.total_pages || 1,
          clusters: clustersRes.clusters || [],
          totalClustersCount: clustersRes.total_clusters || 0,
          classifications: clfRes.classifications || [],
          dbHealth: dbRes,
          isOffline: false,
          lastRefreshed: new Date(),
          loading: false,
        })
      } catch (err: unknown) {
        console.error('Failed to load dashboard telemetry:', err)
        set({
          isOffline: true,
          error:
            err instanceof Error
              ? err.message
              : 'Unable to communicate with SIH26162 FastAPI / PostGIS backend.',
          loading: false,
        })
      }
    },

    setSelectedEntity: (entity) => set({ selectedEntity: entity }),

    setViewMode: (viewMode) => set({ viewMode }),

    setAutoPulseInterval: (autoPulseInterval) => set({ autoPulseInterval }),

    setFilters: (updater) => {
      const currentFilters = get().filters
      const nextFilters = typeof updater === 'function' ? updater(currentFilters) : updater
      set({ filters: nextFilters, currentPage: 1 })
      get().fetchDashboardData()
    },

    resetFilters: () => {
      set({ filters: initialFilters, currentPage: 1 })
      get().fetchDashboardData()
    },

    setCurrentPage: (currentPage) => {
      set({ currentPage })
      get().fetchDashboardData()
    },

    setIsHealthModalOpen: (isHealthModalOpen) => set({ isHealthModalOpen }),

    setDemoMode: (isDemoMode) => {
      if (isDemoMode) {
        set({ isDemoMode: true })
        get().activateDemoScenario(0)
      } else {
        set({ isDemoMode: false, selectedEntity: null })
      }
    },

    activateDemoScenario: (scenarioIndex) => {
      const s = DEMO_SCENARIOS[scenarioIndex]
      if (s) {
        set({
          activeDemoScenario: scenarioIndex,
          selectedEntity: { type: 'observation', data: scenarioToObservation(s) },
        })
      }
    },

    handleMapBoundsChange: (bbox) => {
      const { filters } = get()
      if (filters.useMapBounds) {
        get().setFilters((prev) => ({ ...prev, bbox }))
      }
    },
  }))
)
