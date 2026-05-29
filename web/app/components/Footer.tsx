import Link from 'next/link'

export default function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer className="border-t border-border mt-16">
      <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted">
        <p>© {year} M&M Manifatture di Scarpa Monica</p>
        <div className="flex gap-6">
          <Link href="/note-legali" className="hover:text-accent transition-colors">Note legali</Link>
          <Link href="/note-legali#privacy" className="hover:text-accent transition-colors">Privacy</Link>
          <Link href="/note-legali#cookie" className="hover:text-accent transition-colors">Cookie</Link>
          <Link href="/contatti" className="hover:text-accent transition-colors">Contatti</Link>
        </div>
      </div>
    </footer>
  )
}
