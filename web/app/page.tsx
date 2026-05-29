import Link from 'next/link'
import { getPublishedProducts, getCategories } from '@/lib/catalog'
import ProductCard from './components/ProductCard'

export default function HomePage() {
  const products = getPublishedProducts()
  const latest = products.slice(-4).reverse()
  const categories = getCategories()

  return (
    <>
      {/* Hero */}
      <section className="max-w-5xl mx-auto px-4 pt-16 pb-12 text-center">
        <h1 className="font-serif text-4xl md:text-5xl font-semibold text-foreground leading-tight mb-4">
          Artigianato fatto a mano,<br className="hidden md:block" /> con cura
        </h1>
        <p className="text-muted text-lg max-w-xl mx-auto mb-8">
          Ogni pezzo è unico. Realizzato personalmente da Monica Scarpa con materiali scelti e attenzione al dettaglio.
        </p>
        <Link
          href="/prodotti"
          className="inline-block px-8 py-3 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors"
        >
          Sfoglia i prodotti
        </Link>
      </section>

      {/* Divider */}
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
          <p className="text-muted text-lg">
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
