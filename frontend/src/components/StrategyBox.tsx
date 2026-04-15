type StrategyBoxProps = {
  actionPlan: string
  whoToContactFirst: string
}

export function StrategyBox({ actionPlan, whoToContactFirst }: StrategyBoxProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-slate-900">Outreach Strategy</h3>

      <div className="mb-4 rounded-lg bg-amber-50 p-3">
        <p className="text-xs font-medium uppercase tracking-wide text-amber-700">
          Who to contact first
        </p>
        <p className="mt-1 text-sm font-semibold text-amber-900">{whoToContactFirst}</p>
      </div>

      <div>
        <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-600">Action plan</p>
        <p className="text-sm text-slate-700">{actionPlan}</p>
      </div>
    </section>
  )
}
