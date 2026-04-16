import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { evaluateJob, generateMessage } from './api/client'
import { ContactList, type ContactItem, type ContactMessage } from './components/ContactList'
import { ScoreCard } from './components/ScoreCard'
import { StrategyBox } from './components/StrategyBox'

type EvaluationResult = {
  final_score: number
  job_fit: number
  contact_score: number
  action_plan: string
  actionable?: boolean
  discard_reason?: string | null
  company_signals?: string[]
  job_summary?: string
  required_skills?: string[]
  decision?: string
  contacts: ContactItem[]
  [key: string]: unknown
}

function App() {
  const [jobText, setJobText] = useState('')
  const [cvText, setCvText] = useState('')
  const [result, setResult] = useState<EvaluationResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<Record<string, ContactMessage>>({})
  const [loadingContactId, setLoadingContactId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const canSubmit = useMemo(() => jobText.trim().length > 0 && cvText.trim().length > 0, [jobText, cvText])

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setErrorMessage(null)

    const payload = {
      job_text: jobText.trim(),
      cv_text: cvText.trim(),
    }

    setIsLoading(true)
    const response = await evaluateJob<EvaluationResult>(payload)
    if (response.error) {
      setResult(null)
      setErrorMessage(response.error)
    } else {
      setResult(response.data)
      setMessages({})
    }
    setIsLoading(false)
  }

  const generateForContact = async (contact: ContactItem, force = false) => {
    if (!result) return
    const contactId = contact.id ?? `${contact.name}-${contact.role}`
    if (!force && messages[contactId]) return
    setLoadingContactId(contactId)
    const response = await generateMessage<ContactMessage>({
      contact_id: contactId,
      cv: { raw_text: cvText.trim() },
      job: {
        title: String((result as { title?: string }).title ?? 'Unknown'),
        company: String((result as { company?: string }).company ?? 'Unknown'),
        description: jobText.trim(),
      },
      company_intel: {
        signals: result.company_signals ?? [],
      },
      contact: {
        ...contact,
        id: contactId,
      },
      user_preferences: {
        tone: 'role_aware',
      },
    })
    if (response.error) {
      setErrorMessage(response.error)
    } else if (response.data) {
      setMessages((prev) => ({ ...prev, [contactId]: response.data as ContactMessage }))
    }
    setLoadingContactId(null)
  }

  return (
    <main className="min-h-screen bg-slate-100 py-10">
      <div className="mx-auto w-full max-w-4xl px-4">
        <h1 className="mb-8 text-3xl font-bold text-slate-900">Decision Engine</h1>

        <form onSubmit={onSubmit} className="space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-xl font-semibold text-slate-900">1. Job Input</h2>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Job description
            </label>
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              placeholder="Paste full job description here..."
              className="h-56 w-full resize-y rounded-lg border border-slate-300 p-3 text-sm outline-none ring-indigo-200 focus:ring"
            />
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-xl font-semibold text-slate-900">2. CV Input</h2>
            <label className="mb-2 block text-sm font-medium text-slate-700">CV text</label>
            <textarea
              value={cvText}
              onChange={(e) => setCvText(e.target.value)}
              placeholder="Paste full CV text here..."
              className="h-56 w-full resize-y rounded-lg border border-slate-300 p-3 text-sm outline-none ring-indigo-200 focus:ring"
            />
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-xl font-semibold text-slate-900">3. Submit Button</h2>
            <button
              type="submit"
              disabled={!canSubmit || isLoading}
              className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isLoading ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Evaluating...
                </span>
              ) : (
                'Evaluate Job'
              )}
            </button>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-xl font-semibold text-slate-900">4. Results Section</h2>
            {errorMessage && (
              <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                {errorMessage}
              </div>
            )}
            {!result ? (
              <p className="text-sm text-slate-600">
                Submit the form to see evaluation results here.
              </p>
            ) : (
              <div className="space-y-4">
                <div
                  className={`rounded-lg border p-3 text-sm ${
                    result.actionable === false
                      ? 'border-amber-300 bg-amber-50 text-amber-900'
                      : 'border-emerald-200 bg-emerald-50 text-emerald-900'
                  }`}
                >
                  {result.actionable === false
                    ? 'Low-confidence opportunity: weak fit or low reliability contacts. Review score and outreach carefully.'
                    : 'Actionable opportunity: strong enough fit with reliable contact coverage.'}
                </div>
                <ScoreCard
                  finalScore={result.final_score}
                  jobFit={result.job_fit}
                  contactScore={result.contact_score}
                />
                {Array.isArray(result.company_signals) && result.company_signals.length > 0 && (
                  <section className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-700">
                      Singapore Company Signals
                    </h3>
                    <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                      {result.company_signals.slice(0, 4).map((signal) => (
                        <li key={signal}>{signal}</li>
                      ))}
                    </ul>
                    {result.job_summary && (
                      <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                          Job Description Summary
                        </p>
                        <p className="mt-1 text-sm text-slate-700">{result.job_summary}</p>
                      </div>
                    )}
                    {Array.isArray(result.required_skills) && result.required_skills.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                          Skills They Are Looking For
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {result.required_skills.slice(0, 8).map((skill) => (
                            <span
                              key={skill}
                              className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </section>
                )}
                <ContactList
                  contacts={result.contacts ?? []}
                  messages={messages}
                  loadingContactId={loadingContactId}
                  onGenerateMessage={(contact) => generateForContact(contact, false)}
                  onRegenerateMessage={(contact) => generateForContact(contact, true)}
                />
                <StrategyBox
                  actionPlan={result.action_plan ?? 'No action plan returned.'}
                  whoToContactFirst={(result.contacts?.[0]?.name as string) ?? 'No contact recommendation yet'}
                />
              </div>
            )}
          </section>
        </form>
      </div>
    </main>
  )
}

export default App
