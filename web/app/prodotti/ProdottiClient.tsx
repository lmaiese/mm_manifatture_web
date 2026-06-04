'use client'

import { Suspense, useState } from 'react'
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

  // Availability filter: 'available' (default) | 'all'
  const [availFilter, setAvailFilter] = useState<'available' | 'all'>('available')

  // Count helpers
  const availableCount = products.filter((p) => p.available !== false).length
  const soldCount      = products.filter((p) => p.available === false).length

  // Apply both filters
  const filtered = products
    .filter((p) => categoria ? p.category === categoria : true)
    .filter((p) => availFilter === 'available' ? p.available !== false : true)

  return (
    <>
      <section className="hero-section">
        <div className="max-w-5xl mx-auto px-4 pt-10 pb-8">
          <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Prodotti</h1>
          <p className="mb-4" style={{color: 'var(--muted)'}}>Pezzi pronti o su commissione — scrivi a Monica per qualsiasi richiesta.</p>

          {/* Availability filter */}
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => setAvailFilter('available')}
              className={`text-xs font-medium px-3 py-1.5 rounded-full border transition-colors ${
                availFilter === 'available'
                  ? 'bg-accent text-white border-accent'
                  : 'bg-white text-foreground border-border hover:border-accent hover:text-accent'
              }`}
            >
              Disponibili ({availableCount})
            </button>
            <button
              onClick={() => setAvailFilter('all')}
              className={`text-xs font-medium px-3 py-1.5 rounded-full border transition-colors ${
                availFilter === 'all'
                  ? 'bg-accent text-white border-accent'
                  : 'bg-white text-foreground border-border hover:border-accent hover:text-accent'
              }`}
            >
              Tutti · anche venduti ({availableCount + soldCount})
            </button>
          </div>

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
            <p className="font-serif text-xl text-foreground mb-2">
              {categoria
                ? `Nessun pezzo pronto in "${categoria}" per ora.`
                : availFilter === 'available'
                  ? 'Nessun pezzo disponibile al momento.'
                  : 'Nessun prodotto nel catalogo.'}
            </p>
            <p className="text-sm mb-6" style={{ color: 'var(--muted)' }}>
              Monica lavora su commissione:{' '}
              {categoria ? 'questo tipo di pezzo' : 'tutto quello che vedi sul sito'}{' '}
              lo puoi richiedere su misura.
            </p>
            <a
              href="/contatti"
              className="inline-block px-6 py-2.5 bg-accent text-white font-medium text-sm rounded hover:bg-accent-hover transition-colors"
            >
              Chiedi a Monica →
            </a>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
              {filtered.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
            {availFilter === 'available' && soldCount > 0 && (
              <p className="text-center text-xs mt-8" style={{ color: 'var(--muted)' }}>
                {soldCount} {soldCount === 1 ? 'pezzo venduto' : 'pezzi venduti'} nello storico —{' '}
                <button
                  onClick={() => setAvailFilter('all')}
                  className="underline hover:text-accent transition-colors"
                >
                  mostrali tutti
                </button>
              </p>
            )}
          </>
        )}
      </div>
    </>
  )
}
