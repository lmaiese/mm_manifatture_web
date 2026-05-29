'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'

const NAV = [
  { href: '/prodotti', label: 'Prodotti' },
  { href: '/chi-siamo', label: 'Chi siamo' },
  { href: '/contatti', label: 'Contatti' },
]

export default function Header() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 bg-background/95 backdrop-blur border-b border-border">
      <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" aria-label="M&M Manifatture — Home">
          <svg width="180" height="40" viewBox="0 0 180 40" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
            <text x="0" y="26" fontFamily="'Source Serif 4', Georgia, serif" fontSize="22" fontWeight="600" fill="currentColor" className="text-foreground">M&amp;M</text>
            <text x="52" y="26" fontFamily="'Source Serif 4', Georgia, serif" fontSize="22" fontWeight="400" fill="currentColor" className="text-foreground">Manifatture</text>
            <text x="0" y="38" fontFamily="'Inter', system-ui, sans-serif" fontSize="9" fontWeight="400" letterSpacing="0.12em" fill="#d27684" style={{textTransform: 'uppercase'}}>di Scarpa Monica</text>
          </svg>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`text-sm font-medium transition-colors hover:text-accent ${
                pathname?.startsWith(href) ? 'text-accent' : 'text-muted'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-foreground"
          onClick={() => setOpen(!open)}
          aria-label="Menu"
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            {open ? (
              <path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" />
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <nav className="md:hidden border-t border-border bg-background px-4 py-4 flex flex-col gap-4">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`text-base font-medium transition-colors hover:text-accent ${
                pathname?.startsWith(href) ? 'text-accent' : 'text-foreground'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  )
}
