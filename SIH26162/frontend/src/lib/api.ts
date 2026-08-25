import axios from 'axios'
import type {
  FIRMSObservation,
  PaginatedObservations,
  ThermalSourcesResponse,
  PaginatedClassifications,
  FireClassificationResult,
  IndustrialContextResponse,
  ModelStatus,
  HealthStatus,
  DatabaseHealth,
  DashboardFilterState,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

/**
 * Axios instance configured for SIH26162 backend API communication.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 20000,
})

// Global interceptors for error diagnostics
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('SIH26162 API Error:', error?.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * API Service wrapper for all SIH26162 backend capabilities.
 */
export const ApiService = {
  // Health & Diagnostics
  async getHealth(): Promise<HealthStatus> {
    const res = await apiClient.get<HealthStatus>('/health/')
    return res.data
  },

  async getDatabaseHealth(): Promise<DatabaseHealth> {
    const res = await apiClient.get<DatabaseHealth>('/health/db')
    return res.data
  },

  async getModelStatus(): Promise<ModelStatus> {
    const res = await apiClient.get<ModelStatus>('/fires/status')
    return res.data
  },

  // FIRMS Observations (Spatial, Temporal, Sensor filters & PostGIS Bounding Box)
  async getObservations(filters: DashboardFilterState = {}, page = 1, limit = 50): Promise<PaginatedObservations> {
    const params: Record<string, string | number | boolean> = {
      page,
      limit,
    }

    if (filters.startDate) params.start_date = filters.startDate
    if (filters.endDate) params.end_date = filters.endDate
    if (filters.satellite && filters.satellite !== 'ALL') params.satellite = filters.satellite
    if (filters.instrument && filters.instrument !== 'ALL') params.instrument = filters.instrument
    if (filters.minConfidence !== undefined && filters.minConfidence > 0) params.min_confidence = filters.minConfidence
    if (filters.minFRP !== undefined && filters.minFRP > 0) params.min_frp = filters.minFRP
    if (filters.maxFRP !== undefined && filters.maxFRP > 0) params.max_frp = filters.maxFRP
    if (filters.clusterId !== undefined) params.cluster_id = filters.clusterId

    if (filters.useMapBounds && filters.bbox) {
      params.bbox = filters.bbox.join(',')
    }

    const res = await apiClient.get<PaginatedObservations>('/fires/observations', { params })
    return res.data
  },

  async getObservationById(id: number): Promise<FIRMSObservation> {
    const res = await apiClient.get<FIRMSObservation>(`/fires/${id}`)
    return res.data
  },

  // Persistent Thermal Sources & Spatio-Temporal Clusters
  async getPersistentSources(
    filters: DashboardFilterState = {},
    limit = 200,
    offset = 0
  ): Promise<ThermalSourcesResponse> {
    const params: Record<string, string | number | boolean> = {
      limit,
      offset,
      persistent_only: filters.persistentOnly !== false,
      min_observations: 2,
    }

    if (filters.minConfidence !== undefined && filters.minConfidence > 0) params.min_confidence = filters.minConfidence
    if (filters.minFRP !== undefined && filters.minFRP > 0) params.min_frp = filters.minFRP

    if (filters.useMapBounds && filters.bbox) {
      params.bbox = filters.bbox.join(',')
    }

    const res = await apiClient.get<ThermalSourcesResponse>('/thermal/sources', { params })
    return res.data
  },

  async getAllClusters(): Promise<ThermalSourcesResponse> {
    const res = await apiClient.get<ThermalSourcesResponse>('/thermal/clusters')
    return res.data
  },

  // Stored Classifications & Risk Assessments
  async getClassifications(
    filters: DashboardFilterState = {},
    page = 1,
    limit = 50
  ): Promise<PaginatedClassifications> {
    const params: Record<string, string | number | boolean> = {
      page,
      limit,
    }

    if (filters.predictedClass && filters.predictedClass !== 'ALL') {
      params.predicted_class = filters.predictedClass
    }
    if (filters.riskLevel && filters.riskLevel !== 'ALL') {
      params.risk_level = filters.riskLevel
    }
    if (filters.minConfidence !== undefined && filters.minConfidence > 0) {
      params.min_confidence = filters.minConfidence / 100.0 // 0-1 scale for classification
    }

    const res = await apiClient.get<PaginatedClassifications>('/fires/classifications', { params })
    return res.data
  },

  // Live Real-Time ML Inference & Risk Scoring
  async classifyObservation(payload: {
    latitude: number
    longitude: number
    brightness_primary?: number
    brightness_secondary?: number | null
    frp?: number
    confidence?: number
    daynight?: string
    acq_datetime?: string
    satellite?: string
    instrument?: string
    query_osm?: boolean
    osm_radius_m?: number
    persist?: boolean
  }): Promise<FireClassificationResult> {
    const res = await apiClient.post<FireClassificationResult>('/fires/classify', {
      latitude: payload.latitude,
      longitude: payload.longitude,
      brightness_primary: payload.brightness_primary ?? 330.0,
      brightness_secondary: payload.brightness_secondary ?? null,
      frp: payload.frp ?? 15.0,
      confidence: payload.confidence ?? 80.0,
      daynight: payload.daynight ?? 'D',
      acq_datetime: payload.acq_datetime ?? undefined,
      satellite: payload.satellite ?? 'VIIRS_SNPP_NRT',
      instrument: payload.instrument ?? 'VIIRS',
      query_osm: payload.query_osm ?? true,
      osm_radius_m: payload.osm_radius_m ?? 5000,
      persist: payload.persist ?? false,
    })
    return res.data
  },

  // OpenStreetMap Industrial Context Query
  async getIndustrialContext(
    latitude: number,
    longitude: number,
    radius_m = 5000
  ): Promise<IndustrialContextResponse> {
    const res = await apiClient.post<IndustrialContextResponse>('/geospatial/industrial-context', {
      latitude,
      longitude,
      radius_m,
    })
    return res.data
  },
}
