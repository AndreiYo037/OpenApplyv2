import { useState } from 'react'

export type ContactItem = {
  name: string
  role: string
  source?: string
  linkedin_url?: string | null
  email?: string | null
}

type ContactListProps = {
  contacts: ContactItem[]
}

export function ContactList({ contacts }: ContactListProps) {
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null)

  const copyEmail = async (email: string) => {
    try {
      await navigator.clipboard.writeText(email)
      setCopiedEmail(email)
      window.setTimeout(() => setCopiedEmail(null), 1200)
    } catch {
      setCopiedEmail(null)
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-lg font-semibold text-slate-900">Top Contacts</h3>
      {contacts.length === 0 ? (
        <p className="text-sm text-slate-600">No contacts found yet.</p>
      ) : (
        <ul className="space-y-3">
          {contacts.map((contact, index) => (
            <li key={`${contact.name}-${index}`} className="rounded-lg border border-slate-200 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-slate-900">{contact.name}</p>
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
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
