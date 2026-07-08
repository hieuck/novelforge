import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Target, Flame, TrendingUp } from 'lucide-react'
import { api, WritingStats as WritingStatsType } from '../lib/api'

export function WritingStats({ projectId }: { projectId: string }) {
  const { t } = useTranslation()
  const [stats, setStats] = useState<WritingStatsType | null>(null)

  useEffect(() => {
    let cancelled = false
    api.get<WritingStatsType>(`/projects/${projectId}/writing-stats`)
      .then((data) => {
        if (!cancelled) setStats(data)
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [projectId])

  if (!stats) return null

  const progress = stats.daily_goal > 0 ? Math.min(100, Math.round((stats.today_words / stats.daily_goal) * 100)) : 0

  return (
    <div data-testid="writing-stats" className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300">{t('writing_stats.title')}</h3>
        <Target className="h-4 w-4 text-indigo-400" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center">
          <div data-testid="writing-stats-today" className="text-lg font-bold text-indigo-400">
            {stats.today_words.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">{t('writing_stats.today')}</div>
        </div>
        <div className="text-center">
          <div data-testid="writing-stats-goal" className="text-lg font-bold text-indigo-400">
            {stats.daily_goal.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">{t('writing_stats.goal')}</div>
        </div>
        <div className="text-center">
          <div data-testid="writing-stats-streak" className="flex items-center justify-center gap-1 text-lg font-bold text-orange-400">
            <Flame className="h-4 w-4" />
            {stats.streak.current}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">{t('writing_stats.streak')}</div>
        </div>
      </div>
      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
          <span>{t('writing_stats.progress')}</span>
          <span data-testid="writing-stats-progress">{progress}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-800">
          <div
            data-testid="writing-stats-bar"
            className="h-full bg-indigo-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-1 text-xs text-slate-500">
        <TrendingUp className="h-3 w-3" />
        <span data-testid="writing-stats-total">{stats.total_words.toLocaleString()} {t('writing_stats.total_words')}</span>
      </div>
    </div>
  )
}
