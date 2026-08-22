import { AlertTriangle, Sparkles } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface PlaceholderProps {
  title: string
  description: string
  phase?: string
}

export function Placeholder({ title, description, phase = 'Phase 1-4' }: PlaceholderProps) {
  return (
    <Card className="border-dashed border-slate-800 bg-slate-900/40">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Sparkles className="size-4 text-amber-500" />
            {title}
          </CardTitle>
          <Badge variant="outline" className="text-xs text-amber-400 border-amber-500/30">
            {phase}
          </Badge>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center p-8 text-center rounded-lg border border-slate-800/60 bg-slate-950/40">
          <AlertTriangle className="size-8 text-amber-500/70 mb-3" />
          <p className="text-sm text-slate-300 font-medium">Modular Architecture Established</p>
          <p className="text-xs text-slate-500 mt-1 max-w-sm">
            This module is planned and structurally integrated. Real data ingestion and inference will be connected in upcoming phases.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
