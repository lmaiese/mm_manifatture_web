import Link from 'next/link'
import CookiePreferencesButton from './CookiePreferencesButton'

const FOOTER_LINKS = [
  { href: '/note-legali', label: 'Note legali' },
  { href: '/note-legali#privacy', label: 'Privacy' },
  { href: '/note-legali#cookie', label: 'Cookie' },
  { href: '/contatti', label: 'Contatti' },
]

export default function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer className="mt-16 footer-dark">
      <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
        <div>
          <p>© {year} M&amp;M Manifatture di Scarpa Monica</p>
          <p className="footer-tagline">Fatto a mano a Gioi, nel Cilento. Con cura, un pezzo alla volta.</p>
        </div>
        <nav className="flex flex-wrap gap-6 justify-center">
          {FOOTER_LINKS.map(({ href, label }) => (
            <Link key={href} href={href} className="footer-link">
              {label}
            </Link>
          ))}
          <CookiePreferencesButton />
        </nav>
      </div>
    </footer>
  )
}
