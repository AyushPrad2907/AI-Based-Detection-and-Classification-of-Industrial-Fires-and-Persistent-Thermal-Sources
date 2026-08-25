import { useState } from 'react'
import {
  Filter,
  RotateCcw,
  Satellite,
  Shield,
  Flame,
  Crosshair,
  SlidersHorizontal,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { DashboardFilterState } from '@/types'

interface FilterBarProps {
  filters: DashboardFilterState
  onFiltersChange: (newFilters: DashboardFilterState) => void
  onReset: () => void
  totalCount?: number
  loading?: boolean
}

export function FilterBar({
  filters,
  onFiltersChange,
  onReset,
}: FilterBarProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handlePresetDate = (days: number | null) => {
    if (days === null) {
      onFiltersChange({ ...filters, startDate: undefined, endDate: undefined })
      return
    }
    const end = new Date()
    const start = new Date()
    start.setDate(end.getDate() - days)
    onFiltersChange({
      ...filters,
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0],
    })
  }

  const activeFilterCount = [
    filters.startDate,
    filters.satellite && filters.satellite !== 'ALL',
    filters.predictedClass && filters.predictedClass !== 'ALL',
    filters.riskLevel && filters.riskLevel !== 'ALL',
    filters.minConfidence && filters.minConfidence > 0,
    filters.minFRP && filters.minFRP > 0,
    filters.useMapBounds,
  ].filter(Boolean).length

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur space-y-4">
      {/* Top Bar: Primary Filters & Search */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-300 mr-1">
            <Filter className="size-3.5 text-amber-500" />
            <span>Filter Console</span>
            {activeFilterCount > 0 && (
              <Badge variant="outline" className="bg-amber-500/20 text-amber-300 border-amber-500/40 text-[10px] px-1.5 py-0">
                {activeFilterCount} active
              </Badge>
            )}
          </div>

          {/* Quick Date Presets */}
          <div className="flex items-center rounded-lg bg-slate-950 p-0.5 border border-slate-800 text-xs">
            <button
              onClick={() => handlePresetDate(null)}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                !filters.startDate
                  ? 'bg-amber-500 text-slate-950 shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Time
            </button>
            <button
              onClick={() => handlePresetDate(1)}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                filters.startDate && !filters.startDate.includes('7') && !filters.startDate.includes('30')
                  ? 'bg-amber-500 text-slate-950 shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              24h NRT
            </button>
            <button
              onClick={() => handlePresetDate(7)}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                filters.startDate?.includes('7')
                  ? 'bg-amber-500 text-slate-950 shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => handlePresetDate(30)}
              className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                filters.startDate?.includes('30')
                  ? 'bg-amber-500 text-slate-950 shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              30 Days
            </button>
          </div>

          {/* Satellite Sensor Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
            <Satellite className="size-3.5 text-cyan-400 shrink-0" />
            <select
              value={filters.satellite || 'ALL'}
              onChange={(e) => onFiltersChange({ ...filters, satellite: e.target.value })}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
            >
              <option value="ALL" className="bg-slate-900">All Satellites</option>
              <option value="VIIRS_SNPP_NRT" className="bg-slate-900">VIIRS Suomi-NPP</option>
              <option value="VIIRS_NOAA20_NRT" className="bg-slate-900">VIIRS NOAA-20</option>
              <option value="MODIS_NRT" className="bg-slate-900">MODIS (Terra/Aqua)</option>
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
            <Shield className="size-3.5 text-rose-400 shrink-0" />
            <select
              value={filters.riskLevel || 'ALL'}
              onChange={(e) => onFiltersChange({ ...filters, riskLevel: e.target.value })}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
            >
              <option value="ALL" className="bg-slate-900">All Risk Tiers</option>
              <option value="CRITICAL" className="bg-slate-900 text-rose-400">CRITICAL Risk</option>
              <option value="HIGH" className="bg-slate-900 text-orange-400">HIGH Risk</option>
              <option value="MODERATE" className="bg-slate-900 text-amber-400">MODERATE Risk</option>
              <option value="LOW" className="bg-slate-900 text-emerald-400">LOW Risk</option>
            </select>
          </div>

          {/* AI Classification Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
            <Flame className="size-3.5 text-amber-400 shrink-0" />
            <select
              value={filters.predictedClass || 'ALL'}
              onChange={(e) => onFiltersChange({ ...filters, predictedClass: e.target.value })}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer text-xs"
            >
              <option value="ALL" className="bg-slate-900">All Classes</option>
              <option value="persistent_industrial" className="bg-slate-900">Persistent Industrial</option>
              <option value="industrial_fire" className="bg-slate-900">Industrial Fire Incident</option>
              <option value="wildfire" className="bg-slate-900">Wildfire / Forest</option>
              <option value="agricultural_burn" className="bg-slate-900">Agricultural Burn</option>
              <option value="uncertain_anomaly" className="bg-slate-900">Uncertain Anomaly</option>
            </select>
          </div>
        </div>

        {/* Action Buttons: Toggle Viewport PostGIS & Reset */}
        <div className="flex items-center gap-2">
          {/* PostGIS BBox Map Sync Toggle */}
          <button
            onClick={() => onFiltersChange({ ...filters, useMapBounds: !filters.useMapBounds })}
            title="Query PostGIS spatial index strictly within current map viewport"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              filters.useMapBounds
                ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300 shadow-sm shadow-cyan-500/10'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Crosshair className={`size-3.5 ${filters.useMapBounds ? 'animate-pulse text-cyan-400' : ''}`} />
            <span>Map Viewport (BBox)</span>
          </button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs h-8 bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
          >
            <SlidersHorizontal className="size-3.5 mr-1" />
            <span>{showAdvanced ? 'Simple' : 'Sliders'}</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            disabled={activeFilterCount === 0}
            className="text-xs h-8 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10"
          >
            <RotateCcw className="size-3.5 mr-1" />
            <span>Reset</span>
          </Button>
        </div>
      </div>

      {/* Expandable Advanced Sliders: Confidence & FRP thresholds */}
      {showAdvanced && (
        <div className="pt-3 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Min Confidence Slider */}
          <div className="space-y-1.5 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <div className="flex justify-between text-slate-300">
              <span>Min Confidence:</span>
              <span className="font-mono text-amber-400 font-bold">{filters.minConfidence || 0}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={filters.minConfidence || 0}
              onChange={(e) => onFiltersChange({ ...filters, minConfidence: Number(e.target.value) })}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
          </div>

          {/* Min FRP Slider */}
          <div className="space-y-1.5 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <div className="flex justify-between text-slate-300">
              <span>Min Fire Radiative Power (MW):</span>
              <span className="font-mono text-yellow-400 font-bold">{filters.minFRP || 0} MW</span>
            </div>
            <input
              type="range"
              min="0"
              max="200"
              step="5"
              value={filters.minFRP || 0}
              onChange={(e) => onFiltersChange({ ...filters, minFRP: Number(e.target.value) })}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-yellow-500"
            />
          </div>

          {/* Date Picker Range */}
          <div className="space-y-1.5 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <span className="text-slate-300">Custom Start Date:</span>
            <input
              type="date"
              value={filters.startDate || ''}
              onChange={(e) => onFiltersChange({ ...filters, startDate: e.target.value || undefined })}
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono text-[11px]"
            />
          </div>

          <div className="space-y-1.5 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <span className="text-slate-300">Custom End Date:</span>
            <input
              type="date"
              value={filters.endDate || ''}
              onChange={(e) => onFiltersChange({ ...filters, endDate: e.target.value || undefined })}
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono text-[11px]"
            />
          </div>
        </div>
      )}
    </div>
  )
}
