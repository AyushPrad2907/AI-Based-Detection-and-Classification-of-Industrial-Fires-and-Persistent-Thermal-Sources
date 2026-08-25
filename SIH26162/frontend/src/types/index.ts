/**
 * SIH26162 — Comprehensive TypeScript Type Definitions for Phase 4 Dashboard.
 */

export type FireClassificationType =
  | 'persistent_industrial'
  | 'industrial_fire'
  | 'wildfire'
  | 'agricultural_burn'
  | 'uncertain_anomaly'
  | 'unknown'

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'

export interface FIRMSObservation {
  id?: number
  latitude: number
  longitude: number
  brightness_primary: number
  brightness_secondary?: number | null
  frp: number // Fire Radiative Power (MW)
  confidence_score: number
  confidence_category: string
  acq_datetime: string
  satellite: string
  instrument: string
  daynight: string // 'D' | 'N'
  scan: number
  track: number
  cluster_id?: number | null
}

export interface PaginatedObservations {
  total: number
  page: number
  limit: number
  total_pages: number
  observations: FIRMSObservation[]
}

export interface PersistentThermalCluster {
  cluster_id: number
  centroid_latitude: number
  centroid_longitude: number
  observation_count: number
  first_seen_utc: string
  last_seen_utc: string
  persistence_duration_days: number
  mean_frp_mw: number
  max_frp_mw: number
  mean_brightness_kelvin: number
  mean_confidence: number
  night_observation_ratio: number
  spatial_radius_meters: number
  is_persistent: boolean
}

export interface ThermalSourcesResponse {
  total_clusters: number
  persistent_sources_count: number
  clusters: PersistentThermalCluster[]
  query_parameters: Record<string, unknown>
}

export interface RiskBreakdown {
  frp_subscore: number
  industrial_proximity_subscore: number
  persistence_subscore: number
  confidence_subscore: number
  nocturnal_subscore: number
}

export interface ClassificationRecord {
  id: number
  observation_id?: number | null
  latitude: number
  longitude: number
  predicted_class: FireClassificationType | string
  confidence: number
  class_probabilities: Record<string, number>
  model_version: string
  risk_score?: number | null
  risk_level?: RiskLevel | string | null
  reasons?: string[] | null
  created_at: string
}

export interface PaginatedClassifications {
  total: number
  page: number
  limit: number
  total_pages: number
  classifications: ClassificationRecord[]
}

export interface IndustrialFacility {
  osm_id?: number | null
  osm_type?: string | null
  name: string
  facility_type: string
  latitude: number
  longitude: number
  distance_meters: number
  tags: Record<string, string>
}

export interface IndustrialContextResponse {
  is_industrial_nearby: boolean
  min_distance_m: number
  min_distance_km: number
  nearest_facility_name?: string | null
  nearest_facility_type?: string | null
  total_facilities_in_radius: number
  facilities: IndustrialFacility[]
  query_latitude: number
  query_longitude: number
  search_radius_m: number
  status: string
}

export interface FireClassificationResult {
  latitude: number
  longitude: number
  predicted_class: FireClassificationType | string
  classification_confidence: number
  class_probabilities: Record<string, number>
  risk_score: number
  risk_level: RiskLevel | string
  risk_breakdown: RiskBreakdown
  reasons: string[]
  is_persistent_source: boolean
  persistent_cluster?: Record<string, unknown> | null
  industrial_context?: IndustrialContextResponse | null
  thermal_parameters: Record<string, unknown>
  classification_id?: number | null
}

export interface ModelStatus {
  ready: boolean
  model_type?: string | null
  classes: string[]
  features_count: number
  persistent_clusters_known: number
  model_path: string
  message?: string | null
}

export interface HealthStatus {
  status: string
  service: string
  version: string
}

export interface DatabaseHealth {
  status: string
  database_connected: boolean
  postgis_installed: boolean
  postgis_version?: string | null
  database_name?: string | null
  table_counts: {
    firms_observations: number
    persistent_thermal_sources: number
    industrial_facilities: number
    classifications: number
    risk_assessments: number
  }
  error?: string | null
}

export interface DashboardFilterState {
  startDate?: string
  endDate?: string
  satellite?: string
  instrument?: string
  minConfidence?: number
  minFRP?: number
  maxFRP?: number
  predictedClass?: string
  riskLevel?: string
  persistentOnly?: boolean
  clusterId?: number
  useMapBounds?: boolean
  bbox?: [number, number, number, number] // [min_lon, min_lat, max_lon, max_lat]
  searchQuery?: string
}

export interface SelectedEntity {
  type: 'observation' | 'cluster' | 'facility'
  data: FIRMSObservation | PersistentThermalCluster | IndustrialFacility
  classificationResult?: FireClassificationResult | null
}
