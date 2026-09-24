import {
  Play,
  Pause,
  RotateCcw,
  Clock,
  Flame,
  FastForward,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface TimelineScrubberBarProps {
  uniqueFrames: string[]
  selectedDateIndex: number | null
  setSelectedDateIndex: (idx: number | null) => void
  isPlaying: boolean
  setIsPlaying: (playing: boolean) => void
  activeCount: number
  totalCount: number
  playbackSpeed?: number
  onSpeedToggle?: () => void
}

export function TimelineScrubberBar({
  uniqueFrames,
  selectedDateIndex,
  setSelectedDateIndex,
  isPlaying,
  setIsPlaying,
  activeCount,
  totalCount,
  playbackSpeed = 1200,
  onSpeedToggle,
}: TimelineScrubberBarProps) {
  if (uniqueFrames.length === 0) return null

  const currentIndex = selectedDateIndex ?? (uniqueFrames.length - 1)
  const currentLabel = selectedDateIndex !== null ? uniqueFrames[selectedDateIndex] : 'All Observation Passes'
  const isFiltering = selectedDateIndex !== null

  return (
    <div className="w-full bg-slate-900/95 border border-slate-800 rounded-xl p-3 shadow-xl backdrop-blur-md flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
      {/* Play/Pause & Current Timestamp */}
      <div className="flex items-center gap-2.5 shrink-0">
        <Button
          size="sm"
          onClick={() => setIsPlaying(!isPlaying)}
          className={`h-8 px-3 text-xs font-bold gap-1.5 transition-all shadow-md ${
            isPlaying
              ? 'bg-amber-500 text-slate-950 hover:bg-amber-400 shadow-amber-500/20'
              : 'bg-emerald-600 text-white hover:bg-emerald-500 shadow-emerald-600/20'
          }`}
          title={isPlaying ? 'Pause timeline playback' : 'Play chronological satellite pass sequence'}
        >
          {isPlaying ? (
            <>
              <Pause className="size-3.5 fill-current" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="size-3.5 fill-current" />
              <span>Play Timeline</span>
            </>
          )}
        </Button>

        {/* Speed toggle if provided */}
        {onSpeedToggle && (
          <Button
            size="sm"
            variant="outline"
            onClick={onSpeedToggle}
            className="h-8 px-2 text-[11px] font-mono bg-slate-950 border-slate-800 text-slate-300 hover:text-amber-400"
            title="Toggle playback speed"
          >
            <FastForward className="size-3 mr-1 text-amber-500" />
            <span>{playbackSpeed <= 600 ? '2x' : '1x'}</span>
          </Button>
        )}

        {/* Active Frame Timestamp */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800/80">
          <Clock className="size-3 text-amber-400" />
          <span className="text-xs font-mono font-bold text-slate-200 tracking-tight">
            {currentLabel}
          </span>
          {uniqueFrames.length > 1 && (
            <span className="text-[10px] font-mono text-slate-500 hidden md:inline">
              ({currentIndex + 1}/{uniqueFrames.length})
            </span>
          )}
        </div>
      </div>

      {/* Scrubber Range Slider (middle) */}
      {uniqueFrames.length > 1 && (
        <div className="flex-1 flex items-center gap-2.5 px-1 min-w-[180px]">
          <span className="text-[10px] font-mono text-slate-500 shrink-0 hidden lg:inline">
            {uniqueFrames[0]}
          </span>
          <div className="relative w-full flex items-center">
            <input
              type="range"
              min="0"
              max={uniqueFrames.length - 1}
              value={currentIndex}
              onChange={(e) => {
                setIsPlaying(false)
                setSelectedDateIndex(Number(e.target.value))
              }}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500 hover:bg-slate-700 transition-colors"
              title="Drag to inspect specific satellite pass timestamp"
            />
          </div>
          <span className="text-[10px] font-mono text-slate-500 shrink-0 hidden lg:inline">
            {uniqueFrames[uniqueFrames.length - 1]}
          </span>
        </div>
      )}

      {/* Right side: Filter stats & Reset */}
      <div className="flex items-center justify-between sm:justify-end gap-2 shrink-0">
        <div className="flex items-center gap-1.5 text-xs font-mono">
          <Flame className="size-3.5 text-amber-500" />
          <span className="text-slate-400">Frame Telemetry:</span>
          <Badge
            variant="outline"
            className={`font-mono text-xs px-2 py-0.5 ${
              isFiltering
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                : 'bg-slate-950 text-slate-300 border-slate-800'
            }`}
          >
            {activeCount} / {totalCount} fires
          </Badge>
        </div>

        {isFiltering && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setIsPlaying(false)
              setSelectedDateIndex(null)
            }}
            className="h-7 px-2 text-[11px] bg-slate-950 border-slate-800 text-slate-300 hover:text-amber-400 hover:border-amber-500/40"
            title="Reset to display all observation telemetry simultaneously"
          >
            <RotateCcw className="size-3 mr-1 text-slate-400" />
            <span>Show All</span>
          </Button>
        )}
      </div>
    </div>
  )
}
