import Link from 'next/link'
import { getPublishedProducts, getCategories } from '@/lib/catalog'
import ProductCard from './components/ProductCard'
import about from '@/content/about.json'

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
          <p className="text-lg max-w-xl mx-auto mb-8" style={{ color: 'var(--muted)' }}>
            Monica realizza a mano maglioncini in lana merinos, bambole di pezza e accessori artigianali. Ogni pezzo richiede ore di lavoro. Nessuno è identico a un altro.
          </p>
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
            <h2 className="font-serif text-2xl font-semibold text-foreground mb-2">Come nascono i nostri pezzi</h2>
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
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-serif text-2xl font-semibold text-foreground">Ultimi arrivi</h2>
            <Link href="/prodotti" className="text-sm text-accent hover:underline">
              Vedi tutti →
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {latest.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 pb-16">
          <h2 className="font-serif text-2xl font-semibold text-foreground mb-6">Categorie</h2>
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

      {/* Empty state */}
      {products.length === 0 && (
        <section className="max-w-5xl mx-auto px-4 py-16 text-center">
          <p className="text-lg" style={{ color: 'var(--muted)' }}>
            I prodotti arrivano presto. Torna a trovarci!
          </p>
          <Link href="/contatti" className="mt-4 inline-block text-accent hover:underline">
            Contattaci intanto →
          </Link>
        </section>
      )}
    </>
  )
}
