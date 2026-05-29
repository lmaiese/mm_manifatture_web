import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-24 text-center">
      <p className="font-serif text-6xl font-semibold text-foreground mb-4">404</p>
      <h1 className="font-serif text-2xl font-semibold text-foreground mb-3">
        Pagina non trovata
      </h1>
      <p className="text-muted mb-8 max-w-sm mx-auto">
        La pagina che cerchi non esiste o è stata spostata.
      </p>
      <Link
        href="/"
        className="inline-block px-6 py-2.5 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors"
      >
        Torna alla home
      </Link>
    </div>
  )
}
