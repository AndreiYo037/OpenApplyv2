import { useState } from 'react'

export type ContactItem = {
  id?: string
  name: string
  role: string
  role_type?: 'recruiter' | 'hiring_manager' | 'senior_ic' | 'junior_ic' | 'unknown'
  influence_level?: number
  source?: string
  linkedin_url?: string | null
  email?: string | null
}

export type ContactMessage = {
  message: string
  personalization_points?: string[]
  effectiveness_breakdown?: Record<string, unknown>
}

type ContactListProps = {
  contacts: ContactItem[]
  messages: Record<string, ContactMessage>
  loadingContactId: string | null
  onGenerateMessage: (contact: ContactItem) => Promise<void>
  onRegenerateMessage: (contact: ContactItem) => Promise<void>
}

const influenceBand = (value: number): 'High' | 'Medium' | 'Low' => {
  if (value >= 80) return 'High'
  if (value >= 55) return 'Medium'
  return 'Low'
}

export function ContactList({
  contacts,
  messages,
  loadingContactId,
  onGenerateMessage,
  onRegenerateMessage,
}: ContactListProps) {
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null)
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  const copyEmail = async (email: string) => {
    try {
      await navigator.clipboard.writeText(email)
      setCopiedEmail(email)
      window.setTimeout(() => setCopiedEmail(null), 1200)
    } catch {
      setCopiedEmail(null)
    }
  }

  const copyMessage = async (contactId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMessageId(contactId)
      window.setTimeout(() => setCopiedMessageId(null), 1200)
    } catch {
      setCopiedMessageId(null)
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-slate-900">Top Contacts (Priority Order)</h3>
      {contacts.length === 0 ? (
        <p className="text-sm text-slate-600">No contacts found yet.</p>
      ) : (
        <ul className="space-y-3">
          {contacts.map((contact, index) => {
            const contactId = contact.id ?? `${contact.name}-${index}`
            const influence = Number(contact.influence_level ?? 40)
            const band = influenceBand(influence)
            const deEmphasize = band === 'Low'
            const topHighlight = index < 2
            return (
              <li
                key={contactId}
                className={`rounded-lg border p-4 ${
                  topHighlight ? 'border-indigo-200 bg-indigo-50/40' : 'border-slate-200'
                } ${deEmphasize ? 'opacity-80' : ''}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-slate-900">
                    <span className="mr-2 rounded bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700">
                      #{index + 1}
                    </span>
                    {contact.name} - {contact.role}
                  </p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                      contact.source === 'job_description'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {contact.source === 'job_description' ? 'From JD' : 'Discovered'}
                  </span>
                </div>
                <p className="mt-1 text-xs font-medium text-slate-600">
                  Influence: <span className="text-slate-800">{band}</span> ({Math.round(influence)})
                </p>
                {band === 'Low' && (
                  <p className="mt-1 text-xs text-amber-700">
                    This contact may have lower hiring influence.
                  </p>
                )}
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {contact.linkedin_url && (
                    <a
                      href={contact.linkedin_url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
                    >
                      LinkedIn
                    </a>
                  )}
                  {contact.email && (
                    <>
                      <a
                        href={`mailto:${contact.email}`}
                        className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                      >
                        {contact.email}
                      </a>
                      <button
                        type="button"
                        onClick={() => copyEmail(contact.email as string)}
                        className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
                      >
                        {copiedEmail === contact.email ? 'Copied' : 'Copy Email'}
                      </button>
                    </>
                  )}
                </div>
                <div className="mt-3">
                  <button
                    type="button"
                    disabled={loadingContactId === contactId}
                    onClick={() => onGenerateMessage({ ...contact, id: contactId })}
                    className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {loadingContactId === contactId ? 'Generating message...' : 'Generate Outreach Message'}
                  </button>
                  {messages[contactId] && (
                    <button
                      type="button"
                      disabled={loadingContactId === contactId}
                      onClick={() => onRegenerateMessage({ ...contact, id: contactId })}
                      className="ml-2 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
                    >
                      Regenerate
                    </button>
                  )}
                </div>
                {messages[contactId]?.message && (
                  <details className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <summary className="cursor-pointer text-sm font-semibold text-slate-800">Generated Message</summary>
                    <textarea
                      readOnly
                      value={messages[contactId]?.message ?? ''}
                      className="mt-3 h-32 w-full resize-y rounded border border-slate-300 bg-white p-2 text-sm text-slate-800"
                    />
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => copyMessage(contactId, messages[contactId].message)}
                        className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
                      >
                        {copiedMessageId === contactId ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  </details>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
