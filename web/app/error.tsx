'use client'

import { useEffect } from 'react'
import Link from 'next/link'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log to console in production so it appears in Vercel Function Logs
    console.error('[GlobalError]', error.message, error.digest ?? '')
  }, [error])

  return (
    <div className="max-w-5xl mx-auto px-4 py-24 text-center">
      <p className="font-serif text-6xl font-semibold text-foreground mb-4">Ops</p>
      <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
        Qualcosa è andato storto
      </h1>
      <p className="text-muted mb-8 max-w-sm mx-auto">
        Si è verificato un errore inatteso. Riprova o torna alla home.
      </p>
      <div className="flex gap-4 justify-center">
        <button
          onClick={reset}
          className="inline-block px-6 py-2.5 border border-accent text-accent font-medium rounded hover:bg-accent hover:text-white transition-colors"
        >
          Riprova
        </button>
        <Link
          href="/"
          className="inline-block px-6 py-2.5 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors"
        >
          Torna alla home
        </Link>
      </div>
    </div>
  )
}
