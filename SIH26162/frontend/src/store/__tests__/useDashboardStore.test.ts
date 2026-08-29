import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useDashboardStore, DEMO_SCENARIOS, scenarioToObservation } from '../useDashboardStore'
import { ApiService } from '@/lib/api'
import type { FIRMSObservation } from '@/types'

vi.mock('@/lib/api', () => ({
  ApiService: {
    getObservations: vi.fn().mockResolvedValue({ observations: [], total: 0, total_pages: 1 }),
    getPersistentSources: vi.fn().mockResolvedValue({ clusters: [], total_clusters: 0 }),
    getClassifications: vi.fn().mockResolvedValue({ classifications: [] }),
    getDatabaseHealth: vi.fn().mockResolvedValue({ database_connected: true }),
  },
}))

describe('useDashboardStore', () => {
  beforeEach(() => {
    useDashboardStore.setState({
      observations: [],
      totalObsCount: 0,
      clusters: [],
      totalClustersCount: 0,
      classifications: [],
      selectedEntity: null,
      viewMode: 'split',
      isHealthModalOpen: false,
      isDemoMode: false,
      activeDemoScenario: 0,
      currentPage: 1,
      loading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  it('should initialize with default states', () => {
    const state = useDashboardStore.getState()
    expect(state.viewMode).toBe('split')
    expect(state.isDemoMode).toBe(false)
    expect(state.selectedEntity).toBeNull()
    expect(state.currentPage).toBe(1)
  })

  it('should update selected entity', () => {
    const obs = scenarioToObservation(DEMO_SCENARIOS[0])
    useDashboardStore.getState().setSelectedEntity({ type: 'observation', data: obs })

    expect(useDashboardStore.getState().selectedEntity).toEqual({
      type: 'observation',
      data: obs,
    })
  })

  it('should switch view mode', () => {
    useDashboardStore.getState().setViewMode('analytics')
    expect(useDashboardStore.getState().viewMode).toBe('analytics')
  })

  it('should activate demo scenario correctly', () => {
    useDashboardStore.getState().activateDemoScenario(1)
    const state = useDashboardStore.getState()
    expect(state.activeDemoScenario).toBe(1)
    expect(state.selectedEntity?.type).toBe('observation')
    const obsData = state.selectedEntity?.data as FIRMSObservation
    expect(obsData.id).toBe(DEMO_SCENARIOS[1].obsId)
  })

  it('should toggle demo mode on and off', () => {
    useDashboardStore.getState().setDemoMode(true)
    expect(useDashboardStore.getState().isDemoMode).toBe(true)
    expect(useDashboardStore.getState().selectedEntity).not.toBeNull()

    useDashboardStore.getState().setDemoMode(false)
    expect(useDashboardStore.getState().isDemoMode).toBe(false)
    expect(useDashboardStore.getState().selectedEntity).toBeNull()
  })

  it('should fetch and populate dashboard data', async () => {
    const mockObs = [scenarioToObservation(DEMO_SCENARIOS[0])]
    vi.mocked(ApiService.getObservations).mockResolvedValueOnce({
      observations: mockObs,
      total: 1,
      total_pages: 1,
      page: 1,
      limit: 50,
    })

    await useDashboardStore.getState().fetchDashboardData()

    const state = useDashboardStore.getState()
    expect(state.loading).toBe(false)
    expect(state.observations.length).toBe(1)
    expect(state.totalObsCount).toBe(1)
  })
})
