'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import type { Product } from '@/lib/catalog'
import ProductCard from '../components/ProductCard'
import CategoryFilter from '../components/CategoryFilter'

interface Props {
  products: Product[]
  categories: string[]
}

export default function ProdottiClient({ products, categories }: Props) {
  const searchParams = useSearchParams()
  const categoria = searchParams.get('categoria') || undefined
  const filtered = categoria ? products.filter((p) => p.category === categoria) : products

  return (
    <>
      <section className="hero-section">
        <div className="max-w-5xl mx-auto px-4 pt-10 pb-8">
          <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Prodotti</h1>
          <p className="mb-6" style={{color: 'var(--muted)'}}>Tutti i pezzi sono realizzati a mano — ogni pezzo è unico.</p>
          {categories.length > 0 && (
            <Suspense>
              <CategoryFilter categories={categories} />
            </Suspense>
          )}
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {filtered.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-muted">
              {categoria
                ? `Nessun prodotto nella categoria "${categoria}" per ora.`
                : 'Nessun prodotto disponibile al momento. Torna presto!'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
            {filtered.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </div>
    </>
  )
}
