import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KPICards } from '../KPICards'
import type { FIRMSObservation, PersistentThermalCluster, ClassificationRecord } from '@/types'

describe('KPICards', () => {
  const mockObservations: FIRMSObservation[] = [
    {
      id: 1,
      latitude: 28.5,
      longitude: 77.2,
      brightness_primary: 340,
      brightness_secondary: 300,
      frp: 50.0,
      confidence_score: 90,
      confidence_category: 'high',
      acq_datetime: '2024-01-15T12:00:00Z',
      satellite: 'VIIRS',
      instrument: 'VIIRS',
      daynight: 'N',
      scan: 0.375,
      track: 0.375,
      cluster_id: null,
    },
    {
      id: 2,
      latitude: 28.6,
      longitude: 77.3,
      brightness_primary: 320,
      brightness_secondary: 290,
      frp: 30.0,
      confidence_score: 80,
      confidence_category: 'nominal',
      acq_datetime: '2024-01-15T14:00:00Z',
      satellite: 'VIIRS',
      instrument: 'VIIRS',
      daynight: 'D',
      scan: 0.375,
      track: 0.375,
      cluster_id: null,
    },
  ]

  const mockClusters: PersistentThermalCluster[] = [
    {
      cluster_id: 101,
      centroid_latitude: 28.55,
      centroid_longitude: 77.25,
      observation_count: 15,
      mean_frp_mw: 45.0,
      max_frp_mw: 90.0,
      persistence_duration_days: 12.5,
      is_persistent: true,
      first_seen_utc: '2024-01-03T10:00:00Z',
      last_seen_utc: '2024-01-15T14:00:00Z',
      mean_brightness_kelvin: 320,
      mean_confidence: 85,
      night_observation_ratio: 0.8,
      spatial_radius_meters: 500,
    },
  ]

  const mockClassifications: ClassificationRecord[] = [
    {
      id: 1,
      latitude: 28.5,
      longitude: 77.2,
      predicted_class: 'industrial_fire',
      confidence: 0.95,
      class_probabilities: { industrial_fire: 0.95 },
      model_version: 'random_forest_v1',
      risk_score: 88,
      risk_level: 'CRITICAL',
      created_at: '2024-01-15T12:00:00Z',
    },
  ]

  it('renders correctly with computed metrics', () => {
    render(
      <KPICards
        observations={mockObservations}
        clusters={mockClusters}
        classifications={mockClassifications}
        totalObservationsCount={2}
        totalClustersCount={1}
        loading={false}
        isDatabaseConnected={true}
      />
    )

    expect(screen.getByText('Raw Thermal Detections')).toBeInTheDocument()
    expect(screen.getByText('Persistent Thermal Clusters')).toBeInTheDocument()
    expect(screen.getByText('High & Critical Risk Anomalies')).toBeInTheDocument()
    expect(screen.getByText('Peak Radiative Power (FRP)')).toBeInTheDocument()
    expect(screen.getByText('50.0 MW')).toBeInTheDocument()
  })

  it('displays loading indicators when loading is true', () => {
    render(
      <KPICards
        observations={[]}
        clusters={[]}
        classifications={[]}
        totalObservationsCount={0}
        totalClustersCount={0}
        loading={true}
      />
    )

    const loadingPlaceholders = screen.getAllByText('...')
    expect(loadingPlaceholders.length).toBeGreaterThan(0)
  })
})
