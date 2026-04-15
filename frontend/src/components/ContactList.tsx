import { useState } from 'react'

export type ContactItem = {
  id: string
  name: string
  role: string
  source?: string
  confidence?: number
  search_hint?: string
  linkedin_url?: string | null
  email?: string | null
  score?: number
  reason?: string
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
          {contacts.map((contact, index) => (
            <li key={`${contact.name}-${index}`} className="rounded-lg border border-slate-200 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-slate-900">
                  <span className="mr-2 rounded bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700">
                    #{index + 1}
                  </span>
                  {contact.name}
                </p>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                    contact.source === 'job_description'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {contact.source === 'job_description' ? 'Recruiter from JD' : 'Discovered'}
                </span>
              </div>
              <p className="text-sm text-slate-600">{contact.role}</p>
              {typeof contact.score === 'number' && (
                <p className="mt-1 text-xs font-medium text-indigo-700">Score: {Math.round(contact.score)}/100</p>
              )}
              {contact.reason && <p className="mt-1 text-xs text-slate-500">{contact.reason}</p>}
              {typeof contact.confidence === 'number' && (
                <p className="mt-1 text-xs text-slate-500">
                  Discovery confidence: {Math.round(contact.confidence * 100)}%
                </p>
              )}
              {contact.search_hint && (
                <p className="mt-1 text-xs text-slate-500">Signal: {contact.search_hint}</p>
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
                  disabled={loadingContactId === contact.id}
                  onClick={() => onGenerateMessage(contact)}
                  className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {loadingContactId === contact.id ? 'Generating message...' : 'Generate Outreach Message'}
                </button>
                {messages[contact.id] && (
                  <button
                    type="button"
                    disabled={loadingContactId === contact.id}
                    onClick={() => onRegenerateMessage(contact)}
                    className="ml-2 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
                  >
                    Regenerate
                  </button>
                )}
              </div>
              {messages[contact.id]?.message && (
                <details className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <summary className="cursor-pointer text-sm font-semibold text-slate-800">
                    Generated Message
                  </summary>
                  <textarea
                    readOnly
                    value={messages[contact.id]?.message ?? ''}
                    className="mt-3 h-32 w-full resize-y rounded border border-slate-300 bg-white p-2 text-sm text-slate-800"
                  />
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => copyMessage(contact.id, messages[contact.id].message)}
                      className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
                    >
                      {copiedMessageId === contact.id ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </details>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
