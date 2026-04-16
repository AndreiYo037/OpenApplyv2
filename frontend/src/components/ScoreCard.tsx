type ScoreCardProps = {
  finalScore: number
  jobFit: number
  contactScore: number
}

const toPercent = (value: number): string => `${Math.round((value || 0) * 100)}%`

export function ScoreCard({ finalScore, jobFit, contactScore }: ScoreCardProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-slate-900">Score Overview</h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-lg bg-indigo-50 p-3">
          <p className="text-xs text-indigo-700">Final Score</p>
          <p className="text-2xl font-bold text-indigo-900">{toPercent(finalScore)}</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs text-slate-700">Job Fit</p>
          <p className="text-2xl font-bold text-slate-900">{toPercent(jobFit)}</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs text-slate-700">Contact Score</p>
          <p className="text-2xl font-bold text-slate-900">{toPercent(contactScore)}</p>
        </div>
      </div>
    </section>
  )
}
