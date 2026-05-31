import Link from 'next/link'
import type { Metadata } from 'next'
import { getPublishedProducts, getCategories } from '@/lib/catalog'
import ProductCard from './components/ProductCard'
import about from '@/content/about.json'

export const metadata: Metadata = {
  description: 'Maglioncini in lana merinos e capi in maglia fatti a mano da Monica Scarpa a Gioi, nel Cilento. Ogni pezzo è unico e nasce da una conversazione.',
}

export default function HomePage() {
  const products = getPublishedProducts()
  const latest = products.slice(-4).reverse()
  const categories = getCategories()

  return (
    <>
      {/* Hero */}
      <section className="hero-section">
        <div className="max-w-5xl mx-auto px-4 pt-16 pb-12 text-center relative z-10">
          <h1 className="font-serif text-4xl md:text-5xl font-semibold text-foreground leading-tight mb-4">
            Artigianato fatto a mano,<br className="hidden md:block" /> a Gioi, nel Cilento
          </h1>
          <p className="text-lg max-w-xl mx-auto mb-4" style={{ color: 'var(--muted)' }}>
            Monica realizza a mano maglioncini in lana merinos, cardigan e cappellini. Ogni pezzo richiede ore di lavoro. Nessuno è identico a un altro.
          </p>
          {about.hero_trust && (
            <p className="hero-trust-stat">
              {about.hero_trust}
            </p>
          )}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/prodotti"
              className="inline-block px-8 py-3 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors"
            >
              Sfoglia i prodotti
            </Link>
            <Link
              href="/chi-siamo"
              className="inline-block px-8 py-3 border border-foreground text-foreground font-medium rounded hover:border-accent hover:text-accent transition-colors"
            >
              Scopri come nascono →
            </Link>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="border-t border-border" />

      {/* Come nascono i pezzi */}
      {about.process_steps && about.process_steps.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 py-14">
          <div className="text-center mb-10">
            <h2 className="font-serif text-2xl font-semibold text-foreground mb-2">Come nascono i miei pezzi</h2>
            <p style={{ color: 'var(--muted)' }}>Nessun carrello automatico. Ogni ordine è una conversazione.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {about.process_steps.map((s) => (
              <div key={s.step} className="home-process-card">
                <span className="home-process-number">{s.step}</span>
                <h3 className="font-serif text-lg font-semibold text-foreground mb-1">{s.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>{s.description}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <Link
              href="/contatti"
              className="inline-block px-7 py-3 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors"
            >
              Voglio un pezzo personalizzato →
            </Link>
          </div>
        </section>
      )}

      <div className="border-t border-border" />

      {/* Latest products */}
      {latest.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 py-12">
          <div className="flex items-start justify-between mb-2 gap-4">
            <h2 className="font-serif text-2xl font-semibold text-foreground">Ultimi pezzi disponibili</h2>
            <Link href="/prodotti" className="text-sm text-accent hover:underline shrink-0 mt-1">
              Vedi tutti →
            </Link>
          </div>
          <p className="text-sm mb-8" style={{ color: 'var(--muted)' }}>
            Monica lavora su commissione: questi pezzi sono pronti adesso — gli altri li fa su misura.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {latest.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {products.length === 0 && (
        <section className="max-w-5xl mx-auto px-4 py-16 text-center">
          <p className="font-serif text-xl text-foreground mb-3">
            Nessun pezzo disponibile in questo momento.
          </p>
          <p className="mb-6" style={{ color: 'var(--muted)' }}>
            Monica lavora su commissione — scrivile e realizza qualcosa su misura per te.
          </p>
          <Link
            href="/contatti"
            className="inline-block px-7 py-3 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors"
          >
            Chiedi un pezzo personalizzato →
          </Link>
        </section>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 py-10 border-t border-border">
          <h2 className="font-serif text-xl font-semibold text-foreground mb-4">Sfoglia per tipo</h2>
          <div className="flex flex-wrap gap-3">
            {categories.map((cat) => (
              <Link
                key={cat}
                href={`/prodotti?categoria=${encodeURIComponent(cat)}`}
                className="px-5 py-2 border border-border rounded-full text-sm text-foreground hover:border-accent hover:text-accent transition-colors"
              >
                {cat}
              </Link>
            ))}
          </div>
        </section>
      )}
    </>
  )
}
