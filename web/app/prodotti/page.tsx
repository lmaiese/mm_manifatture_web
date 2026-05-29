import { Suspense } from 'react'
import { getPublishedProducts, getCategories } from '@/lib/catalog'
import ProductCard from '../components/ProductCard'
import CategoryFilter from '../components/CategoryFilter'

export const metadata = {
  title: 'Prodotti — M&M Manifatture',
  description: 'Tutti i prodotti artigianali realizzati a mano da Monica Scarpa.',
}

function ProductGrid({ categoria }: { categoria?: string }) {
  const products = getPublishedProducts()
  const filtered = categoria
    ? products.filter((p) => p.category === categoria)
    : products

  if (filtered.length === 0) {
    return (
      <div className="py-16 text-center">
        <p className="text-muted">
          {categoria
            ? `Nessun prodotto nella categoria "${categoria}" per ora.`
            : 'Nessun prodotto disponibile al momento. Torna presto!'}
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
      {filtered.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  )
}

export default function ProdottiPage({
  searchParams,
}: {
  searchParams: { categoria?: string }
}) {
  const categories = getCategories()
  const categoria = searchParams.categoria

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Prodotti</h1>
      <p className="text-muted mb-8">Tutti i pezzi sono realizzati a mano — ogni pezzo è unico.</p>

      {categories.length > 0 && (
        <Suspense>
          <CategoryFilter categories={categories} />
        </Suspense>
      )}

      <ProductGrid categoria={categoria} />
    </div>
  )
}
