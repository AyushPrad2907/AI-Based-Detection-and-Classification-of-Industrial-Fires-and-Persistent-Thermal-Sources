/**
 * TypeScript type definitions for SIH26162 Frontend.
 */

export type FireClassificationType =
  | 'industrial_fire'
  | 'wildfire'
  | 'agricultural_burn'
  | 'power_plant'
  | 'persistent_industrial'
  | 'unknown'

export type ConfidenceLevel = 'low' | 'nominal' | 'high'

export interface FireDetection {
  id: string
  latitude: number
  longitude: number
  brightness: number
  confidence: ConfidenceLevel
  frp: number // Fire Radiative Power (MW)
  acquisitionDate: string
  acquisitionTime: string
  satellite: 'MODIS' | 'VIIRS'
  classification?: FireClassificationType
  classificationConfidence?: number
  nearestFacility?: string
}

export interface ThermalSource {
  id: string
  name?: string
  latitude: number
  longitude: number
  sourceType: FireClassificationType
  avgTemperatureKelvin: number
  observedDaysCount: number
  lastDetected: string
  osmLandUse?: string
}

export interface HealthStatus {
  status: string
  service: string
  version: string
}
