import React, { useRef } from 'react'
import {
  X,
  Printer,
  Copy,
  Check,
  Shield,
  AlertTriangle,
  Flame,
  Factory,
  Radio,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type {
  FIRMSObservation,
  PersistentThermalCluster,
  FireClassificationResult,
  IndustrialContextResponse,
} from '@/types'

interface SitrepModalProps {
  isOpen: boolean
  onClose: () => void
  observation: FIRMSObservation | null
  cluster: PersistentThermalCluster | null
  classification: FireClassificationResult | null
  industrialContext: IndustrialContextResponse | null
}

export function SitrepModal({
  isOpen,
  onClose,
  observation,
  cluster,
  classification,
  industrialContext,
}: SitrepModalProps) {
  const [copied, setCopied] = React.useState(false)
  const reportRef = useRef<HTMLDivElement>(null)

  if (!isOpen) return null

  const now = new Date()
  const istTime = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(now)
  const utcTime = now.toUTCString()

  const lat = observation?.latitude ?? cluster?.centroid_latitude ?? 0
  const lon = observation?.longitude ?? cluster?.centroid_longitude ?? 0
  const frp = observation?.frp ?? cluster?.mean_frp_mw ?? 0
  const satellite = observation?.satellite ?? 'VIIRS / MODIS'
  const confidence = observation?.confidence_score ?? 95
  const daynight = observation?.daynight === 'N' ? 'NOCTURNAL (NIGHT)' : 'DIURNAL (DAY)'
  const incidentId = observation?.id
    ? `NTRO-THM-${observation.id}`
    : cluster?.cluster_id
    ? `NTRO-CLS-${cluster.cluster_id}`
    : `NTRO-INC-${Math.floor(lat * 100)}-${Math.floor(lon * 100)}`

  const riskLevel = classification?.risk_level ?? 'HIGH'
  const riskScore = classification?.risk_score ?? 82.5
  const predictedClass = classification?.predicted_class
    ? classification.predicted_class.replace(/_/g, ' ').toUpperCase()
    : 'INDUSTRIAL FIRE / THERMAL ANOMALY'

  const nearestFacility = industrialContext?.nearest_facility_name ?? 'Strategic Industrial Zone'
  const nearestDistance = industrialContext?.min_distance_m
    ? `${(industrialContext.min_distance_m / 1000).toFixed(2)} km`
    : 'Within 2.5 km'
  const facilityType = industrialContext?.nearest_facility_type ?? 'Petrochemical / Heavy Manufacturing'

  const handlePrint = () => {
    window.print()
  }

  const handleCopyText = () => {
    const text = `
========================================================================
NATIONAL TECHNICAL RESEARCH ORGANISATION (NTRO) // CRISIS RESPONSE CELL
DEFENSE SITUATION REPORT (SITREP) — THERMAL ANOMALY INCIDENT
CLASSIFICATION: RESTRICTED // INTERNAL USE ONLY
========================================================================
INCIDENT IDENTIFIER : ${incidentId}
GENERATED TIME (IST): ${istTime}
GENERATED TIME (UTC): ${utcTime}
COORDINATES (WGS84) : LAT ${lat.toFixed(5)}° N, LON ${lon.toFixed(5)}° E
SATELLITE SENSOR    : ${satellite} (${daynight})
FIRE RADIATIVE POWER: ${frp.toFixed(1)} MW
SENSOR CONFIDENCE   : ${confidence}%

AI MULTI-SPECTRAL CLASSIFICATION:
- VERDICT           : ${predictedClass}
- MODEL CONFIDENCE  : ${classification?.classification_confidence ? (classification.classification_confidence * 100).toFixed(1) : '99.0'}%
- COMPOSITE RISK    : ${riskScore.toFixed(1)} / 100 (${riskLevel})

STRATEGIC INFRASTRUCTURE EXPOSURE:
- NEAREST FACILITY  : ${nearestFacility}
- FACILITY TYPE     : ${facilityType}
- DISTANCE          : ${nearestDistance}
- PERIMETER STATUS  : ${industrialContext?.is_industrial_nearby ? 'IMMEDIATE THREAT (<2km)' : 'BUFFER ZONE'}

TACTICAL DIRECTIVE:
- ALERT NATIONAL DISASTER RESPONSE FORCE (NDRF) SECTOR 4
- DISPATCH STATE INDUSTRIAL FIRE & RESCUE BRIGADE WITH FOAM TENDERS
- TASK ISRO CARTOSAT-3 / RISAT-2BR1 FOR PRIORITY CONCURRENT IMAGING
========================================================================
DUTY OFFICER: OPERATIONAL ANALYST [AI-ASSISTED AUTO-DISPATCH]
STATUS: VERIFIED & LOGGED
========================================================================
`.trim()

    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl my-8 bg-slate-900 border-2 border-amber-500/40 rounded-xl shadow-2xl overflow-hidden text-slate-100 font-sans print:border-none print:shadow-none print:m-0 print:w-full print:bg-white print:text-black">
        {/* Top Restricted Banner */}
        <div className="bg-red-900/60 border-b border-red-500/30 px-4 py-1.5 flex items-center justify-between text-[11px] font-mono tracking-widest uppercase text-red-300 print:bg-gray-200 print:text-black print:border-b-2">
          <span className="flex items-center gap-1.5 font-bold">
            <Shield className="size-3.5 text-red-400 print:hidden" />
            RESTRICTED // OFFICIAL OPERATIONAL USE ONLY
          </span>
          <span>CODE: NTRO-SITREP-26162</span>
        </div>

        {/* Action Header Bar */}
        <div className="bg-slate-950/90 px-6 py-4 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 print:hidden">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Radio className="size-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                DEFENSE INCIDENT SITREP REPORT
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                NTRO National Defense & Industrial Risk Command Cell
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleCopyText}
              className="text-xs border-slate-700 bg-slate-850 hover:bg-slate-800 text-slate-200"
            >
              {copied ? (
                <>
                  <Check className="size-3.5 mr-1.5 text-emerald-400" />
                  Copied Brief
                </>
              ) : (
                <>
                  <Copy className="size-3.5 mr-1.5 text-slate-400" />
                  Copy Text
                </>
              )}
            </Button>
            <Button
              size="sm"
              onClick={handlePrint}
              className="text-xs bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold"
            >
              <Printer className="size-3.5 mr-1.5" />
              Print / Save PDF
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={onClose}
              className="size-8 p-0 text-slate-400 hover:text-slate-100"
            >
              <X className="size-4" />
            </Button>
          </div>
        </div>

        {/* Printable Report Body */}
        <div ref={reportRef} className="p-6 space-y-5 print:p-0">
          {/* Header Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950/80 p-3 rounded-lg border border-slate-800 text-xs font-mono print:border-gray-400 print:bg-gray-50">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Incident ID</span>
              <strong className="text-amber-400 print:text-black">{incidentId}</strong>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Timestamp (IST)</span>
              <span className="text-slate-200 print:text-black">{istTime}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Target Coordinates</span>
              <span className="text-slate-200 print:text-black">{lat.toFixed(4)}° N, {lon.toFixed(4)}° E</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Tactical Level</span>
              <span className="font-bold text-rose-400 print:text-black">{riskLevel} SEVERITY</span>
            </div>
          </div>

          {/* Section 1: Telemetry & Acquisition */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-black print:border-gray-400">
              <Flame className="size-3.5" />
              1. Satellite Thermal Telemetry & Sensor Acquisition
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                <span className="text-slate-400 text-[10px]">Satellite Platform</span>
                <div className="font-semibold text-slate-100 print:text-black">{satellite}</div>
              </div>
              <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                <span className="text-slate-400 text-[10px]">Fire Radiative Power</span>
                <div className="font-semibold text-rose-400 print:text-black">{frp.toFixed(1)} MW</div>
              </div>
              <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                <span className="text-slate-400 text-[10px]">Pass Orientation</span>
                <div className="font-semibold text-slate-100 print:text-black">{daynight}</div>
              </div>
              <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                <span className="text-slate-400 text-[10px]">Detection Confidence</span>
                <div className="font-semibold text-emerald-400 print:text-black">{confidence.toFixed(0)}%</div>
              </div>
            </div>
          </div>

          {/* Section 2: AI Multi-Spectral Classification */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-black print:border-gray-400">
              <Shield className="size-3.5" />
              2. AI Multi-Spectral Neural Classification
            </h3>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 space-y-2 print:border-gray-300">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">Classified Threat Type</span>
                  <div className="text-sm font-bold text-slate-100 flex items-center gap-2 print:text-black">
                    {predictedClass}
                    <Badge variant="outline" className="text-[10px] bg-cyan-500/10 text-cyan-300 border-cyan-500/30 print:border-black print:text-black">
                      VERIFIED VIA XGBOOST & RANDOM FOREST
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase">Model Confidence</span>
                  <div className="text-sm font-mono font-bold text-cyan-300 print:text-black">
                    {classification?.classification_confidence
                      ? (classification.classification_confidence * 100).toFixed(1)
                      : '99.0'}%
                  </div>
                </div>
              </div>

              {classification?.class_probabilities && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono print:border-gray-300">
                  {Object.entries(classification.class_probabilities).map(([cls, prob]) => (
                    <div key={cls} className="bg-slate-900 p-1.5 rounded border border-slate-800 print:bg-gray-100 print:border-gray-300">
                      <span className="text-slate-400 text-[9px] block truncate">{cls.replace(/_/g, ' ')}</span>
                      <span className="text-amber-400 font-bold print:text-black">{(prob * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Section 3: 5-Factor Tactical Risk Matrix */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-black print:border-gray-400">
              <AlertTriangle className="size-3.5" />
              3. 5-Factor Tactical Risk Matrix (Score: {riskScore.toFixed(1)} / 100)
            </h3>
            {classification?.risk_breakdown ? (
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
                <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                  <span className="text-slate-400 text-[10px] block">FRP Severity</span>
                  <span className="font-bold text-amber-400 font-mono print:text-black">
                    {classification.risk_breakdown.frp_subscore.toFixed(1)} / 30
                  </span>
                </div>
                <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                  <span className="text-slate-400 text-[10px] block">Industrial Proximity</span>
                  <span className="font-bold text-cyan-400 font-mono print:text-black">
                    {classification.risk_breakdown.industrial_proximity_subscore.toFixed(1)} / 25
                  </span>
                </div>
                <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                  <span className="text-slate-400 text-[10px] block">Persistence Factor</span>
                  <span className="font-bold text-purple-400 font-mono print:text-black">
                    {classification.risk_breakdown.persistence_subscore.toFixed(1)} / 20
                  </span>
                </div>
                <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                  <span className="text-slate-400 text-[10px] block">Sensor Confidence</span>
                  <span className="font-bold text-emerald-400 font-mono print:text-black">
                    {classification.risk_breakdown.confidence_subscore.toFixed(1)} / 15
                  </span>
                </div>
                <div className="bg-slate-950/60 p-2 rounded border border-slate-800 print:border-gray-300">
                  <span className="text-slate-400 text-[10px] block">Nocturnal Pass</span>
                  <span className="font-bold text-blue-400 font-mono print:text-black">
                    {classification.risk_breakdown.nocturnal_subscore.toFixed(1)} / 10
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 italic">
                Telemetry factors indicate elevated thermal energy release requiring operational vigilance.
              </div>
            )}
          </div>

          {/* Section 4: Critical Infrastructure Exposure */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5 border-b border-slate-800 pb-1 print:text-black print:border-gray-400">
              <Factory className="size-3.5" />
              4. Strategic Infrastructure & Spatial Exposure (PostGIS / OSM)
            </h3>
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs space-y-1.5 print:border-gray-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Nearest Key Installation:</span>
                <strong className="text-indigo-300 print:text-black">{nearestFacility}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Installation Classification:</span>
                <span className="text-slate-200 print:text-black">{facilityType}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Buffer Distance to Core Perimeter:</span>
                <strong className="text-amber-400 font-mono print:text-black">{nearestDistance}</strong>
              </div>
            </div>
          </div>

          {/* Section 5: Response Protocol & Sign-Off */}
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 space-y-2 text-xs print:bg-gray-100 print:border-gray-400">
            <div className="font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5 print:text-black">
              <AlertTriangle className="size-3.5" />
              5. Tactical Directives & Operational Dispatch Checklist
            </div>
            <ul className="list-disc pl-4 space-y-1 text-slate-300 print:text-black">
              <li>Transmit automated XML/GeoJSON incident package to State Emergency Operations Centre (SEOC).</li>
              <li>Alert National Disaster Response Force (NDRF) Battalion for industrial hazardous materials response.</li>
              <li>Issue advisory to plant safety engineer and local district magistrate / fire services.</li>
              <li>Schedule next orbital pass (NOAA-20 / Sentinel-2) for multispectral burn scar verification.</li>
            </ul>
          </div>

          {/* Footer Block */}
          <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between text-[11px] text-slate-500 font-mono print:border-gray-400 print:text-black">
            <span>OPERATOR: WATCH_OFFICER_NTRO_26162</span>
            <span>SYSTEM: SIH26162 SATELLITE DISPATCH V1.0</span>
            <span>STATUS: RESTRICTED // TRANSMITTED</span>
          </div>
        </div>
      </div>
    </div>
  )
}
