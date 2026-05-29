'use client'

import { useEffect, useState } from 'react'

const STORAGE_KEY = 'mm_cookie_consent'

export type ConsentState = 'accepted' | 'declined' | null

export function getConsent(): ConsentState {
  if (typeof window === 'undefined') return null
  return (localStorage.getItem(STORAGE_KEY) as ConsentState) || null
}

export default function CookieBanner({
  onConsent,
}: {
  onConsent: (state: 'accepted' | 'declined') => void
}) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) setVisible(true)
    else onConsent(saved as 'accepted' | 'declined')
  }, [onConsent])

  const handle = (choice: 'accepted' | 'declined') => {
    localStorage.setItem(STORAGE_KEY, choice)
    setVisible(false)
    onConsent(choice)
  }

  if (!visible) return null

  return (
    <div
      role="dialog"
      aria-label="Cookie consent"
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-border shadow-lg"
    >
      <div className="max-w-5xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <p className="text-sm text-foreground">
          Usiamo{' '}
          <a href="/note-legali#cookie" className="underline hover:text-accent">
            Google Analytics
          </a>{' '}
          per capire come viene usato il sito. I dati sono anonimi.
        </p>
        <div className="flex gap-3 shrink-0">
          <button
            onClick={() => handle('declined')}
            className="px-4 py-2 text-sm border border-border rounded hover:bg-background transition-colors"
          >
            Solo necessari
          </button>
          <button
            onClick={() => handle('accepted')}
            className="px-4 py-2 text-sm bg-accent text-white rounded hover:bg-accent-hover transition-colors"
          >
            Accetta
          </button>
        </div>
      </div>
    </div>
  )
}
