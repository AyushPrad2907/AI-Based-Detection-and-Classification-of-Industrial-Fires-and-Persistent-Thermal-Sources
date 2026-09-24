import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import {
  Layers,
  Flame,
  Cpu,
  Factory,
  RefreshCw,
  Eye,
  EyeOff,
  Crosshair,
  Radio,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type {
  FIRMSObservation,
  PersistentThermalCluster,
  IndustrialFacility,
  SelectedEntity,
} from '@/types'

const escapeHtml = (str: string | number | undefined | null): string => {
  if (str == null) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

interface CommandCenterMapProps {
  observations: FIRMSObservation[]
  clusters: PersistentThermalCluster[]
  facilities?: IndustrialFacility[]
  selectedEntity: SelectedEntity | null
  onSelectEntity: (entity: SelectedEntity) => void
  onBoundsChange?: (bbox: [number, number, number, number]) => void
  useMapBounds?: boolean
  loading?: boolean
  targetedAlertLocation?: { lat: number; lon: number; label?: string } | null
  activeObservations: FIRMSObservation[]
}

// Helper for color-coding markers based on FRP
function getObservationColor(obs: FIRMSObservation): string {
  if (obs.frp >= 80) return '#ef4444' // Red - Extreme FRP
  if (obs.frp >= 35) return '#f97316' // Orange - High FRP
  if (obs.frp >= 15) return '#f59e0b' // Amber - Moderate FRP
  return '#eab308' // Yellow - Low FRP
}

function CommandCenterMapInner({
  observations,
  clusters,
  facilities = [],
  selectedEntity,
  onSelectEntity,
  onBoundsChange,
  loading = false,
  targetedAlertLocation = null,
  activeObservations,
}: CommandCenterMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markersLayerRef = useRef<L.LayerGroup | null>(null)
  const clustersLayerRef = useRef<L.LayerGroup | null>(null)
  const facilitiesLayerRef = useRef<L.LayerGroup | null>(null)
  const selectedHighlightRef = useRef<L.LayerGroup | null>(null)
  const radarBeaconLayerRef = useRef<L.LayerGroup | null>(null)
  const heatmapLayerRef = useRef<L.LayerGroup | null>(null)

  // Layer Visibility Toggles
  const [showObservations, setShowObservations] = useState(true)
  const [showClusters, setShowClusters] = useState(true)
  const [showFacilities, setShowFacilities] = useState(true)
  const [showHeatmap, setShowHeatmap] = useState(true)

  type BasemapType = 'stadia' | 'satellite' | 'sentinel' | 'osm'
  // FIX A: Default to 'stadia' dark tile — ALWAYS start dark
  const [activeTileLayer, setActiveTileLayer] = useState<BasemapType>('stadia')
  const tileLayerRef = useRef<L.TileLayer | null>(null)

  // Basemap tile configs
  const TILE_LAYERS: Record<BasemapType, { url: string; attribution: string; maxZoom: number; subdomains: string }> = {
    stadia: {
      url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 20,
      subdomains: '',
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: '&copy; Esri &mdash; High-Resolution Earth Imagery',
      maxZoom: 19,
      subdomains: '',
    },
    sentinel: {
      url: 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg',
      attribution: '&copy; <a href="https://maps.eox.at/">EOX IT Services GmbH</a> &copy; <a href="https://sentinel.esa.int/">Copernicus Sentinel-2 Cloudless</a>',
      maxZoom: 16,
      subdomains: '',
    },
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
      subdomains: 'abc',
    },
  }

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    const defaultCenter: [number, number] = [22.5937, 78.9629]
    const defaultZoom = 5

    const map = L.map(mapContainerRef.current, {
      center: defaultCenter,
      zoom: defaultZoom,
      zoomControl: true,
      attributionControl: true,
      minZoom: 3,
      maxZoom: 18,
    })

    // Always start with dark tile
    const cfg = TILE_LAYERS.stadia
    const initialTile = L.tileLayer(cfg.url, {
      attribution: cfg.attribution,
      maxZoom: cfg.maxZoom,
      subdomains: cfg.subdomains || '',
    }).addTo(map)

    tileLayerRef.current = initialTile

    heatmapLayerRef.current = L.layerGroup().addTo(map)
    markersLayerRef.current = L.layerGroup().addTo(map)
    clustersLayerRef.current = L.layerGroup().addTo(map)
    facilitiesLayerRef.current = L.layerGroup().addTo(map)
    selectedHighlightRef.current = L.layerGroup().addTo(map)
    radarBeaconLayerRef.current = L.layerGroup().addTo(map)

    map.on('moveend', () => {
      const bounds = map.getBounds()
      if (onBoundsChange) {
        onBoundsChange([bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()])
      }
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      heatmapLayerRef.current = null
      radarBeaconLayerRef.current = null
    }
  }, [onBoundsChange])

  // Switch Base Tile Layer
  useEffect(() => {
    if (!mapRef.current || !tileLayerRef.current) return
    mapRef.current.removeLayer(tileLayerRef.current)
    const cfg = TILE_LAYERS[activeTileLayer]
    tileLayerRef.current = L.tileLayer(cfg.url, {
      attribution: cfg.attribution,
      maxZoom: cfg.maxZoom,
      subdomains: cfg.subdomains || '',
    }).addTo(mapRef.current)
  }, [activeTileLayer])

  // Targeted Alert Location Radar Beacon
  useEffect(() => {
    if (!mapRef.current || !radarBeaconLayerRef.current) return
    radarBeaconLayerRef.current.clearLayers()

    if (!targetedAlertLocation) return

    const { lat, lon, label } = targetedAlertLocation
    mapRef.current.flyTo([lat, lon], 12, { animate: true, duration: 1.2 })

    const ring = L.circle([lat, lon], {
      radius: 3500,
      color: '#ef4444',
      fillColor: '#ef4444',
      fillOpacity: 0.22,
      weight: 2,
      dashArray: '6, 8',
    })

    const center = L.circleMarker([lat, lon], {
      radius: 9,
      color: '#ffffff',
      fillColor: '#ef4444',
      fillOpacity: 0.95,
      weight: 2,
    }).bindPopup(`<div class="p-2 text-xs font-bold text-red-400">🚨 ${escapeHtml(label || 'Targeted Thermal Anomaly')}</div>`)

    radarBeaconLayerRef.current.addLayer(ring)
    radarBeaconLayerRef.current.addLayer(center)
    center.openPopup()
  }, [targetedAlertLocation])

  // Render FIRMS Observation Markers
  useEffect(() => {
    if (!markersLayerRef.current) return
    markersLayerRef.current.clearLayers()
    if (!showObservations) return

    activeObservations.forEach((obs) => {
      const color = getObservationColor(obs)
      const isHighPower = obs.frp >= 50
      const isNight = obs.daynight === 'N'

      const iconHtml = `
        <div class="relative flex items-center justify-center cursor-pointer group" style="width: 22px; height: 22px;" role="button" tabindex="0" aria-label="Fire detection marker">
          ${isHighPower ? `<div class="marker-pulse" style="background-color: ${color}40; border: 1px solid ${color};"></div>` : ''}
          <div class="w-3.5 h-3.5 rounded-full flex items-center justify-center border-2 border-slate-950 transition-transform group-hover:scale-125 shadow-lg"
               style="background-color: ${color}; box-shadow: 0 0 8px ${color}aa;">
            ${isNight ? '<div class="w-1 h-1 bg-slate-950 rounded-full"></div>' : ''}
          </div>
        </div>
      `

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-firms-icon',
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      })

      const marker = L.marker([obs.latitude, obs.longitude], { icon: customIcon })

      const popupContent = `
        <div class="p-3 text-xs font-sans">
          <div class="flex items-center justify-between gap-2 border-b border-slate-700/60 pb-1.5 mb-2">
            <span class="font-bold text-slate-100 flex items-center gap-1">🔥 FIRMS Observation</span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">${escapeHtml(obs.satellite)}</span>
          </div>
          <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-300 mb-2">
            <div><span class="text-slate-400">Lat/Lon:</span> ${escapeHtml(obs.latitude.toFixed(4))}, ${escapeHtml(obs.longitude.toFixed(4))}</div>
            <div><span class="text-slate-400">FRP:</span> <strong class="text-amber-400 font-mono">${escapeHtml(obs.frp.toFixed(1))} MW</strong></div>
            <div><span class="text-slate-400">Brightness:</span> ${escapeHtml(obs.brightness_primary.toFixed(1))} K</div>
            <div><span class="text-slate-400">Confidence:</span> ${escapeHtml(obs.confidence_score.toFixed(0))}%</div>
            <div><span class="text-slate-400">Pass:</span> ${obs.daynight === 'N' ? '🌙 Night' : '☀️ Day'}</div>
            <div><span class="text-slate-400">Time:</span> ${escapeHtml(new Date(obs.acq_datetime).toLocaleDateString())}</div>
          </div>
          <div class="text-[10px] text-amber-400 font-medium bg-slate-900 p-1 rounded border border-slate-800 text-center">Click marker to inspect AI Classification &amp; Risk Analysis</div>
        </div>
      `

      marker.bindPopup(popupContent)
      marker.on('click', () => onSelectEntity({ type: 'observation', data: obs }))
      markersLayerRef.current?.addLayer(marker)
    })
  }, [activeObservations, showObservations, onSelectEntity])

  // Render Thermal Risk Heatmap
  useEffect(() => {
    if (!heatmapLayerRef.current) return
    heatmapLayerRef.current.clearLayers()
    if (!showHeatmap) return

    activeObservations.forEach((obs) => {
      const frp = Math.max(obs.frp || 10, 5)
      const outerRadius = Math.min(38000, 12000 + frp * 180)
      const midRadius = outerRadius * 0.52
      const coreRadius = outerRadius * 0.22

      heatmapLayerRef.current?.addLayer(L.circle([obs.latitude, obs.longitude], { radius: outerRadius, stroke: false, fillColor: '#dc2626', fillOpacity: 0.08 }))
      heatmapLayerRef.current?.addLayer(L.circle([obs.latitude, obs.longitude], { radius: midRadius, stroke: false, fillColor: '#f97316', fillOpacity: 0.18 }))
      heatmapLayerRef.current?.addLayer(L.circle([obs.latitude, obs.longitude], { radius: coreRadius, stroke: false, fillColor: '#fde047', fillOpacity: 0.38 }))
    })
  }, [activeObservations, showHeatmap])

  // Render Persistent Thermal Clusters
  useEffect(() => {
    if (!clustersLayerRef.current) return
    clustersLayerRef.current.clearLayers()
    if (!showClusters) return

    clusters.forEach((cluster) => {
      if (cluster.spatial_radius_meters > 0) {
        clustersLayerRef.current?.addLayer(L.circle([cluster.centroid_latitude, cluster.centroid_longitude], {
          radius: Math.max(cluster.spatial_radius_meters, 400),
          color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 0.12, weight: 1.5, dashArray: '3, 6',
        }))
      }

      const clusterHtml = `
        <div class="relative flex items-center justify-center cursor-pointer group" style="width: 28px; height: 28px;">
          <div class="absolute inset-0 rounded-full border border-cyan-400/60 animate-ping opacity-30"></div>
          <div class="w-6 h-6 rounded-full bg-cyan-950/90 border-2 border-cyan-400 flex items-center justify-center text-cyan-300 font-mono text-[10px] font-bold shadow-lg shadow-cyan-500/30 group-hover:scale-110 transition-transform">
            ${escapeHtml(cluster.observation_count)}
          </div>
        </div>
      `

      const marker = L.marker([cluster.centroid_latitude, cluster.centroid_longitude], {
        icon: L.divIcon({ html: clusterHtml, className: 'custom-cluster-icon', iconSize: [28, 28], iconAnchor: [14, 14] }),
      })

      marker.bindPopup(`
        <div class="p-3 text-xs font-sans">
          <div class="flex items-center justify-between gap-2 border-b border-slate-700/60 pb-1.5 mb-2">
            <span class="font-bold text-cyan-300">🏭 Persistent Cluster #${escapeHtml(cluster.cluster_id)}</span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold">${cluster.is_persistent ? 'PERSISTENT' : 'TRANSIENT'}</span>
          </div>
          <div class="space-y-1 text-slate-300 mb-2">
            <div><span class="text-slate-400">Centroid:</span> ${escapeHtml(cluster.centroid_latitude.toFixed(4))}, ${escapeHtml(cluster.centroid_longitude.toFixed(4))}</div>
            <div><span class="text-slate-400">Satellite Passes:</span> <strong class="text-cyan-300">${escapeHtml(cluster.observation_count)} detections</strong></div>
            <div><span class="text-slate-400">Mean FRP:</span> ${escapeHtml(cluster.mean_frp_mw.toFixed(1))} MW (Max: ${escapeHtml(cluster.max_frp_mw.toFixed(1))} MW)</div>
            <div><span class="text-slate-400">Active Duration:</span> ${escapeHtml(cluster.persistence_duration_days.toFixed(1))} days</div>
            <div><span class="text-slate-400">Nocturnal Ratio:</span> ${escapeHtml((cluster.night_observation_ratio * 100).toFixed(0))}%</div>
          </div>
          <div class="text-[10px] text-cyan-400 bg-slate-900 p-1 rounded border border-slate-800 text-center font-medium">Click marker to inspect full cluster telemetry</div>
        </div>
      `)
      marker.on('click', () => onSelectEntity({ type: 'cluster', data: cluster }))
      clustersLayerRef.current?.addLayer(marker)
    })
  }, [clusters, showClusters, onSelectEntity])

  // Render OSM Facilities
  useEffect(() => {
    if (!facilitiesLayerRef.current) return
    facilitiesLayerRef.current.clearLayers()
    if (!showFacilities || facilities.length === 0) return

    facilities.forEach((fac) => {
      const facilityHtml = `
        <div class="flex items-center justify-center cursor-pointer p-1 rounded-md bg-indigo-950/80 border border-indigo-400/60 shadow-md shadow-indigo-500/20">
          <svg class="w-3.5 h-3.5 text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
      `
      const marker = L.marker([fac.latitude, fac.longitude], {
        icon: L.divIcon({ html: facilityHtml, className: 'custom-fac-icon', iconSize: [20, 20], iconAnchor: [10, 10] }),
      })
      marker.bindPopup(`
        <div class="p-2.5 text-xs font-sans">
          <div class="font-bold text-indigo-300 mb-1">🏢 ${escapeHtml(fac.name || 'Industrial Facility')}</div>
          <div class="text-slate-400 text-[11px] mb-1">Type: <span class="text-slate-200">${escapeHtml(fac.facility_type)}</span></div>
          ${fac.distance_meters > 0 ? `<div class="text-slate-400 text-[11px]">Distance: <span class="text-amber-400">${escapeHtml((fac.distance_meters / 1000).toFixed(2))} km</span></div>` : ''}
        </div>
      `)
      marker.on('click', () => onSelectEntity({ type: 'facility', data: fac }))
      facilitiesLayerRef.current?.addLayer(marker)
    })
  }, [facilities, showFacilities, onSelectEntity])

  // Highlight Selected Entity
  useEffect(() => {
    if (!selectedHighlightRef.current || !mapRef.current || !selectedEntity) return
    selectedHighlightRef.current.clearLayers()

    const lat = 'latitude' in selectedEntity.data ? selectedEntity.data.latitude : selectedEntity.data.centroid_latitude
    const lon = 'longitude' in selectedEntity.data ? selectedEntity.data.longitude : selectedEntity.data.centroid_longitude

    if (typeof lat === 'number' && typeof lon === 'number') {
      selectedHighlightRef.current.addLayer(L.circleMarker([lat, lon], {
        radius: 18, color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.25, weight: 2.5,
      }))
      mapRef.current.panTo([lat, lon], { animate: true })
    }
  }, [selectedEntity])

  const handleRecenter = () => {
    mapRef.current?.setView([22.5937, 78.9629], 5, { animate: true })
  }

  return (
    // FIX B: Map container — NO bottom overlay inside. Only layer controls & legend remain as absolute overlays.
    <div className="relative w-full h-full rounded-xl overflow-hidden border border-slate-800 bg-slate-900 shadow-2xl">
      {/* Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Top-Left: Layer Switches Panel */}
      <div className="absolute top-3 left-3 z-[1000] pointer-events-auto">
        <div className="bg-slate-900/95 border border-slate-700 rounded-lg p-2 backdrop-blur-md shadow-xl flex flex-col gap-1 text-xs min-w-[190px]">
          <div className="text-[10px] font-bold text-slate-400 px-1 uppercase tracking-widest mb-1 flex items-center justify-between">
            <span className="flex items-center gap-1.5"><Layers className="size-3" /> Layers</span>
          </div>

          {[
            { key: 'obs', label: `FIRMS Detections (${observations.length})`, active: showObservations, toggle: () => setShowObservations(!showObservations), icon: <Flame className="size-3 text-amber-500" />, activeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
            { key: 'heat', label: 'Thermal Risk Heatmap', active: showHeatmap, toggle: () => setShowHeatmap(!showHeatmap), icon: <span className="text-rose-400 text-xs leading-none">🔥</span>, activeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
            { key: 'clust', label: `Persistent Clusters (${clusters.length})`, active: showClusters, toggle: () => setShowClusters(!showClusters), icon: <Cpu className="size-3 text-cyan-400" />, activeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
          ].map((item) => (
            <button key={item.key} onClick={item.toggle}
              className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded border transition-all ${item.active ? `${item.activeClass} border` : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'}`}>
              <div className="flex items-center gap-1.5">{item.icon}<span>{item.label}</span></div>
              {item.active ? <Eye className="size-3 opacity-70" /> : <EyeOff className="size-3 opacity-40" />}
            </button>
          ))}

          {facilities.length > 0 && (
            <button onClick={() => setShowFacilities(!showFacilities)}
              className={`flex items-center justify-between gap-2 px-2 py-1.5 rounded border transition-all ${showFacilities ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'}`}>
              <div className="flex items-center gap-1.5"><Factory className="size-3 text-indigo-400" /><span>OSM Facilities ({facilities.length})</span></div>
              {showFacilities ? <Eye className="size-3 opacity-70" /> : <EyeOff className="size-3 opacity-40" />}
            </button>
          )}

          {/* Basemap Switcher */}
          <div className="pt-1.5 mt-1 border-t border-slate-800 grid grid-cols-2 gap-1">
            {([
              { key: 'stadia', label: '🌑 Dark', title: 'Stadia Dark (Recommended)' },
              { key: 'satellite', label: '🛰️ Sat', title: 'Esri World Imagery' },
              { key: 'sentinel', label: '🇪🇺 S-2', title: 'Copernicus Sentinel-2' },
              { key: 'osm', label: '🗺️ Street', title: 'OpenStreetMap' },
            ] as { key: BasemapType; label: string; title: string }[]).map((tile) => (
              <button key={tile.key} onClick={() => setActiveTileLayer(tile.key)} title={tile.title}
                className={`py-1 px-1 text-[10px] rounded font-mono text-center transition-all ${
                  activeTileLayer === tile.key
                    ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 bg-slate-800/40 border border-transparent'
                }`}>
                {tile.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Top-Right: Recenter Button */}
      <div className="absolute top-3 right-3 z-[1000] pointer-events-auto">
        <Button size="sm" variant="outline" onClick={handleRecenter}
          className="h-8 bg-slate-900/90 border-slate-700 text-slate-200 text-xs hover:bg-slate-800 shadow-lg backdrop-blur">
          <Crosshair className="size-3.5 mr-1.5 text-amber-500" />
          <span>India Overview</span>
        </Button>
      </div>

      {/* Bottom-Left: FRP Scale Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] pointer-events-none bg-slate-900/95 border border-slate-700 rounded-lg px-3 py-2 text-[11px] backdrop-blur-md shadow-lg hidden sm:flex items-center gap-4">
        <span className="text-slate-500 font-bold uppercase text-[9px] tracking-widest">FRP Scale</span>
        {[
          { color: 'bg-yellow-400', label: '<15 MW' },
          { color: 'bg-amber-500', label: '15–35' },
          { color: 'bg-orange-500', label: '35–80' },
          { color: 'bg-red-500 animate-pulse', label: '>80 MW' },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5">
            <span className={`size-2.5 rounded-full ${item.color} shadow-sm`} />
            <span className="text-slate-400">{item.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 pl-2 border-l border-slate-800">
          <span className="size-3 rounded-full border border-cyan-400 bg-cyan-950/80 text-[8px] flex items-center justify-center text-cyan-300 font-mono">N</span>
          <span className="text-cyan-400 font-medium">Persistent</span>
        </div>
      </div>

      {/* Live data indicator — top center */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] pointer-events-none">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900/90 border border-slate-700 text-[10px] font-mono text-slate-400 backdrop-blur shadow-md">
          <Radio className="size-3 text-emerald-400 animate-pulse" />
          <span className="text-emerald-400 font-bold">NASA FIRMS NRT</span>
          <span className="text-slate-600">·</span>
          <span>{observations.length} detections</span>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 z-[1001] bg-slate-950/50 backdrop-blur-[2px] flex items-center justify-center pointer-events-none">
          <div className="bg-slate-900 border border-slate-700 rounded-xl px-5 py-3 flex items-center gap-3 shadow-2xl">
            <RefreshCw className="size-4 text-amber-500 animate-spin" />
            <span className="text-sm font-semibold text-slate-200">Querying PostGIS Spatial Index...</span>
          </div>
        </div>
      )}
    </div>
  )
}

export const CommandCenterMap = React.memo(CommandCenterMapInner)
