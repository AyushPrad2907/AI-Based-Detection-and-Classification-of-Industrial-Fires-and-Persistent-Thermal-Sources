import type { FIRMSObservation, PersistentThermalCluster, ClassificationRecord } from '@/types'

export function exportToCSV(
  observations: FIRMSObservation[],
  classifications: ClassificationRecord[],
  _clusters?: PersistentThermalCluster[]
) {
  // Build headers
  const headers = [
    'Observation_ID',
    'Latitude',
    'Longitude',
    'FRP_MW',
    'Confidence_Score',
    'Brightness_Kelvin',
    'Satellite',
    'DayNight',
    'Acquisition_UTC',
    'Predicted_Class',
    'Risk_Score',
    'Risk_Level',
  ]

  // Map data rows
  const rows = observations.map((obs) => {
    const clf = classifications.find(
      (c) => c.observation_id === obs.id || (Math.abs(c.latitude - obs.latitude) < 0.001 && Math.abs(c.longitude - obs.longitude) < 0.001)
    )

    return [
      obs.id || '',
      obs.latitude.toFixed(5),
      obs.longitude.toFixed(5),
      obs.frp.toFixed(2),
      obs.confidence_score,
      obs.brightness_primary.toFixed(2),
      obs.satellite,
      obs.daynight,
      obs.acq_datetime || '',
      clf?.predicted_class || 'unclassified',
      clf?.risk_score !== undefined ? clf.risk_score : '',
      clf?.risk_level || '',
    ]
  })

  // Format CSV content
  const csvContent =
    'data:text/csv;charset=utf-8,' +
    [headers.join(','), ...rows.map((e) => e.join(','))].join('\n')

  // Trigger download
  const encodedUri = encodeURI(csvContent)
  const link = document.createElement('a')
  link.setAttribute('href', encodedUri)
  link.setAttribute(
    'download',
    `SIH26162_Thermal_Intelligence_Report_${new Date().toISOString().slice(0, 10)}.csv`
  )
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
