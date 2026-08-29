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
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type {
  FIRMSObservation,
  PersistentThermalCluster,
  IndustrialFacility,
  SelectedEntity,
} from '@/types'

interface CommandCenterMapProps {
  observations: FIRMSObservation[]
  clusters: PersistentThermalCluster[]
  facilities?: IndustrialFacility[]
  selectedEntity: SelectedEntity | null
  onSelectEntity: (entity: SelectedEntity) => void
  onBoundsChange?: (bbox: [number, number, number, number]) => void
  useMapBounds?: boolean
  loading?: boolean
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
}: CommandCenterMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markersLayerRef = useRef<L.LayerGroup | null>(null)
  const clustersLayerRef = useRef<L.LayerGroup | null>(null)
  const facilitiesLayerRef = useRef<L.LayerGroup | null>(null)
  const selectedHighlightRef = useRef<L.LayerGroup | null>(null)

  // Layer Visibility Toggles
  const [showObservations, setShowObservations] = useState(true)
  const [showClusters, setShowClusters] = useState(true)
  const [showFacilities, setShowFacilities] = useState(true)
  const [activeTileLayer, setActiveTileLayer] = useState<'stadia' | 'esri' | 'osm'>('stadia')
  const tileLayerRef = useRef<L.TileLayer | null>(null)

  // Basemap tile configs — all completely free, no API key required
  const TILE_LAYERS = {
    stadia: {
      url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 20,
      subdomains: '',
    },
    esri: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      attribution: '&copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
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

    // India geographic center
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

    // Stadia Alidade Smooth Dark — free, no key, no watermark
    const cfg = TILE_LAYERS.stadia
    const initialTile = L.tileLayer(cfg.url, {
      attribution: cfg.attribution,
      maxZoom: cfg.maxZoom,
      subdomains: cfg.subdomains,
    }).addTo(map)

    tileLayerRef.current = initialTile

    // Create Layer Groups
    markersLayerRef.current = L.layerGroup().addTo(map)
    clustersLayerRef.current = L.layerGroup().addTo(map)
    facilitiesLayerRef.current = L.layerGroup().addTo(map)
    selectedHighlightRef.current = L.layerGroup().addTo(map)

    // Viewport Bounds Change Listener
    map.on('moveend', () => {
      const bounds = map.getBounds()
      const minLon = bounds.getWest()
      const minLat = bounds.getSouth()
      const maxLon = bounds.getEast()
      const maxLat = bounds.getNorth()
      if (onBoundsChange) {
        onBoundsChange([minLon, minLat, maxLon, maxLat])
      }
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
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
      subdomains: cfg.subdomains,
    }).addTo(mapRef.current)
  }, [activeTileLayer])

  // Render FIRMS Observation Markers
  useEffect(() => {
    if (!markersLayerRef.current) return
    markersLayerRef.current.clearLayers()

    if (!showObservations) return

    observations.forEach((obs) => {
      const color = getObservationColor(obs)
      const isHighPower = obs.frp >= 50
      const isNight = obs.daynight === 'N'

      // Custom SVG Marker DivIcon
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
            <span class="font-bold text-slate-100 flex items-center gap-1">
              🔥 FIRMS Observation
            </span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">
              ${obs.satellite}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-300 mb-2">
            <div><span class="text-slate-400">Lat/Lon:</span> ${obs.latitude.toFixed(4)}, ${obs.longitude.toFixed(4)}</div>
            <div><span class="text-slate-400">FRP:</span> <strong class="text-amber-400 font-mono">${obs.frp.toFixed(1)} MW</strong></div>
            <div><span class="text-slate-400">Brightness:</span> ${obs.brightness_primary.toFixed(1)} K</div>
            <div><span class="text-slate-400">Confidence:</span> ${obs.confidence_score.toFixed(0)}%</div>
            <div><span class="text-slate-400">Pass:</span> ${obs.daynight === 'N' ? '🌙 Night' : '☀️ Day'}</div>
            <div><span class="text-slate-400">Time:</span> ${new Date(obs.acq_datetime).toLocaleDateString()}</div>
          </div>
          <div class="text-[10px] text-amber-400 font-medium bg-slate-900 p-1 rounded border border-slate-800 text-center">
            Click marker to inspect AI Classification & Risk Analysis
          </div>
        </div>
      `

      marker.bindPopup(popupContent)
      marker.on('click', () => {
        onSelectEntity({ type: 'observation', data: obs })
      })

      markersLayerRef.current?.addLayer(marker)
    })
  }, [observations, showObservations, onSelectEntity])

  // Render Persistent Thermal Clusters
  useEffect(() => {
    if (!clustersLayerRef.current) return
    clustersLayerRef.current.clearLayers()

    if (!showClusters) return

    clusters.forEach((cluster) => {
      // Draw spatial halo circle
      if (cluster.spatial_radius_meters > 0) {
        const circle = L.circle([cluster.centroid_latitude, cluster.centroid_longitude], {
          radius: Math.max(cluster.spatial_radius_meters, 400),
          color: '#06b6d4',
          fillColor: '#06b6d4',
          fillOpacity: 0.12,
          weight: 1.5,
          dashArray: '3, 6',
        })
        clustersLayerRef.current?.addLayer(circle)
      }

      // Cluster centroid marker
      const clusterHtml = `
        <div class="relative flex items-center justify-center cursor-pointer group" style="width: 28px; height: 28px;">
          <div class="absolute inset-0 rounded-full border border-cyan-400/60 animate-ping opacity-30"></div>
          <div class="w-6 h-6 rounded-full bg-cyan-950/90 border-2 border-cyan-400 flex items-center justify-center text-cyan-300 font-mono text-[10px] font-bold shadow-lg shadow-cyan-500/30 group-hover:scale-110 transition-transform">
            ${cluster.observation_count}
          </div>
        </div>
      `

      const clusterIcon = L.divIcon({
        html: clusterHtml,
        className: 'custom-cluster-icon',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      })

      const marker = L.marker([cluster.centroid_latitude, cluster.centroid_longitude], {
        icon: clusterIcon,
      })

      const popupContent = `
        <div class="p-3 text-xs font-sans">
          <div class="flex items-center justify-between gap-2 border-b border-slate-700/60 pb-1.5 mb-2">
            <span class="font-bold text-cyan-300 flex items-center gap-1">
              🏭 Persistent Cluster #${cluster.cluster_id}
            </span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-semibold">
              ${cluster.is_persistent ? 'PERSISTENT' : 'TRANSIENT'}
            </span>
          </div>
          <div class="space-y-1 text-slate-300 mb-2">
            <div><span class="text-slate-400">Centroid:</span> ${cluster.centroid_latitude.toFixed(4)}, ${cluster.centroid_longitude.toFixed(4)}</div>
            <div><span class="text-slate-400">Satellite Passes:</span> <strong class="text-cyan-300">${cluster.observation_count} detections</strong></div>
            <div><span class="text-slate-400">Mean FRP:</span> ${cluster.mean_frp_mw.toFixed(1)} MW (Max: ${cluster.max_frp_mw.toFixed(1)} MW)</div>
            <div><span class="text-slate-400">Active Duration:</span> ${cluster.persistence_duration_days.toFixed(1)} days</div>
            <div><span class="text-slate-400">Nocturnal Ratio:</span> ${(cluster.night_observation_ratio * 100).toFixed(0)}%</div>
          </div>
          <div class="text-[10px] text-cyan-400 bg-slate-900 p-1 rounded border border-slate-800 text-center font-medium">
            Click marker to inspect full cluster telemetry
          </div>
        </div>
      `

      marker.bindPopup(popupContent)
      marker.on('click', () => {
        onSelectEntity({ type: 'cluster', data: cluster })
      })

      clustersLayerRef.current?.addLayer(marker)
    })
  }, [clusters, showClusters, onSelectEntity])

  // Render OSM Industrial Facilities Overlays
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

      const facIcon = L.divIcon({
        html: facilityHtml,
        className: 'custom-fac-icon',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      })

      const marker = L.marker([fac.latitude, fac.longitude], { icon: facIcon })

      const popupContent = `
        <div class="p-2.5 text-xs font-sans">
          <div class="font-bold text-indigo-300 mb-1">🏢 ${fac.name || 'Industrial Facility'}</div>
          <div class="text-slate-400 text-[11px] mb-1">Type: <span class="text-slate-200">${fac.facility_type}</span></div>
          ${fac.distance_meters > 0 ? `<div class="text-slate-400 text-[11px]">Distance: <span class="text-amber-400">${(fac.distance_meters / 1000).toFixed(2)} km</span></div>` : ''}
        </div>
      `

      marker.bindPopup(popupContent)
      marker.on('click', () => {
        onSelectEntity({ type: 'facility', data: fac })
      })

      facilitiesLayerRef.current?.addLayer(marker)
    })
  }, [facilities, showFacilities, onSelectEntity])

  // Center/Highlight on Selected Entity
  useEffect(() => {
    if (!selectedHighlightRef.current || !mapRef.current || !selectedEntity) return
    selectedHighlightRef.current.clearLayers()

    const lat =
      'latitude' in selectedEntity.data
        ? selectedEntity.data.latitude
        : selectedEntity.data.centroid_latitude
    const lon =
      'longitude' in selectedEntity.data
        ? selectedEntity.data.longitude
        : selectedEntity.data.centroid_longitude

    if (typeof lat === 'number' && typeof lon === 'number') {
      const ring = L.circleMarker([lat, lon], {
        radius: 18,
        color: '#f59e0b',
        fillColor: '#f59e0b',
        fillOpacity: 0.25,
        weight: 2.5,
      })
      selectedHighlightRef.current.addLayer(ring)
      mapRef.current.panTo([lat, lon], { animate: true })
    }
  }, [selectedEntity])

  const handleRecenter = () => {
    if (mapRef.current) {
      mapRef.current.setView([22.5937, 78.9629], 5, { animate: true })
    }
  }

  return (
    <div className="relative w-full h-[580px] lg:h-[650px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl">
      {/* Map Container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Map Overlay Controls & Legend */}
      <div className="absolute top-3 left-3 z-[1000] flex flex-col gap-2 pointer-events-auto">
        {/* Layer Switches */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-2 backdrop-blur shadow-lg flex flex-col gap-1 text-xs">
          <div className="text-[11px] font-bold text-slate-400 px-1 uppercase tracking-wider mb-1 flex items-center justify-between">
            <span>Layers</span>
            <Layers className="size-3 text-slate-400" />
          </div>

          <button
            onClick={() => setShowObservations(!showObservations)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded text-left transition-colors ${
              showObservations ? 'bg-amber-500/20 text-amber-300 font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Flame className="size-3 text-amber-500" />
              <span>FIRMS Detections ({observations.length})</span>
            </div>
            {showObservations ? <Eye className="size-3 text-amber-400" /> : <EyeOff className="size-3 text-slate-500" />}
          </button>

          <button
            onClick={() => setShowClusters(!showClusters)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded text-left transition-colors ${
              showClusters ? 'bg-cyan-500/20 text-cyan-300 font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Cpu className="size-3 text-cyan-400" />
              <span>Persistent Clusters ({clusters.length})</span>
            </div>
            {showClusters ? <Eye className="size-3 text-cyan-400" /> : <EyeOff className="size-3 text-slate-500" />}
          </button>

          {facilities.length > 0 && (
            <button
              onClick={() => setShowFacilities(!showFacilities)}
              className={`flex items-center justify-between gap-2 px-2 py-1 rounded text-left transition-colors ${
                showFacilities ? 'bg-indigo-500/20 text-indigo-300 font-medium' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <Factory className="size-3 text-indigo-400" />
                <span>OSM Facilities ({facilities.length})</span>
              </div>
              {showFacilities ? <Eye className="size-3 text-indigo-400" /> : <EyeOff className="size-3 text-slate-500" />}
            </button>
          )}

          {/* Base Layer Switch */}
          <div className="pt-1.5 mt-1 border-t border-slate-800 flex gap-1">
            <button
              onClick={() => setActiveTileLayer('stadia')}
              className={`flex-1 py-0.5 text-[10px] rounded font-mono transition-colors ${
                activeTileLayer === 'stadia' ? 'bg-slate-800 text-amber-400 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Stadia Alidade Smooth Dark (Free, No Key)"
            >
              Dark
            </button>
            <button
              onClick={() => setActiveTileLayer('esri')}
              className={`flex-1 py-0.5 text-[10px] rounded font-mono transition-colors ${
                activeTileLayer === 'esri' ? 'bg-slate-800 text-amber-400 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Esri World Dark Gray Base"
            >
              Esri
            </button>
            <button
              onClick={() => setActiveTileLayer('osm')}
              className={`flex-1 py-0.5 text-[10px] rounded font-mono transition-colors ${
                activeTileLayer === 'osm' ? 'bg-slate-800 text-amber-400 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
              title="OpenStreetMap Standard"
            >
              Street
            </button>
          </div>
        </div>
      </div>

      {/* Top Right Quick Actions */}
      <div className="absolute top-3 right-3 z-[1000] flex items-center gap-2 pointer-events-auto">
        <Button
          size="sm"
          variant="outline"
          onClick={handleRecenter}
          className="h-8 bg-slate-900/90 border-slate-800 text-slate-200 text-xs hover:bg-slate-800 shadow-lg backdrop-blur"
        >
          <Crosshair className="size-3.5 mr-1.5 text-amber-500" />
          <span>India Overview</span>
        </Button>
      </div>

      {/* Bottom Map Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] pointer-events-auto bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 text-[11px] backdrop-blur shadow-lg hidden sm:flex items-center gap-4">
        <span className="text-slate-400 font-semibold uppercase text-[10px]">FRP Scale:</span>
        <div className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-yellow-400 shadow-sm" />
          <span className="text-slate-300">&lt;15 MW (Low)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-amber-500 shadow-sm" />
          <span className="text-slate-300">15-35 MW</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-orange-500 shadow-sm" />
          <span className="text-slate-300">35-80 MW</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="size-2.5 rounded-full bg-red-500 shadow-sm animate-pulse" />
          <span className="text-slate-300">&gt;80 MW (Critical)</span>
        </div>
        <div className="flex items-center gap-1.5 pl-2 border-l border-slate-800">
          <span className="size-3 rounded-full border border-cyan-400 bg-cyan-950/80 text-[8px] flex items-center justify-center text-cyan-300 font-mono">
            N
          </span>
          <span className="text-cyan-300 font-medium">Persistent Source</span>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 z-[1001] bg-slate-950/40 backdrop-blur-[1px] flex items-center justify-center pointer-events-none">
          <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 flex items-center gap-3 shadow-2xl">
            <RefreshCw className="size-4 text-amber-500 animate-spin" />
            <span className="text-xs font-medium text-slate-200">Querying PostGIS Spatial Index...</span>
          </div>
        </div>
      )}
    </div>
  )
}

export const CommandCenterMap = React.memo(CommandCenterMapInner)
