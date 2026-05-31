import { Suspense } from 'react'
import { getPublishedProducts, getCategories } from '@/lib/catalog'
import type { Product } from '@/lib/catalog'
import ProdottiClient from './ProdottiClient'

export const metadata = {
  title: 'Prodotti — M&M Manifatture',
  description: 'Maglioncini in lana merinos, bambole di pezza e accessori artigianali. Pezzi pronti o su commissione — realizzati a mano da Monica Scarpa a Gioi (SA).',
}

export default function ProdottiPage() {
  const products = getPublishedProducts()
  const categories = getCategories()

  return (
    <Suspense>
      <ProdottiClient products={products} categories={categories} />
    </Suspense>
  )
}
