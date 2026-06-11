import fs from 'fs'
import path from 'path'

export interface Product {
  id: string
  created_at: string
  title?: string | null
  category: string
  price: number
  size?: string | null
  description_site?: string | null
  description_instagram?: string | null
  description_facebook?: string | null
  photos: string[]
  published: boolean
  available?: boolean   // undefined / true = available for purchase; false = sold / historical
  scheduled_for?: string | null
  target?: 'bambino' | 'donna' | 'uomo' | 'unisex' | null  // target demografico del pezzo; null/assente = non classificato
}

export interface Catalog {
  products: Product[]
  categories: string[]
}

/**
 * Returns all published products (both available and sold).
 * Filters out hidden products (published === false) only.
 * available=false items are still returned — they appear with a "sold" badge.
 */
export function getCatalog(): Catalog {
  const filePath = path.join(process.cwd(), 'catalog.json')
  const raw = fs.readFileSync(filePath, 'utf-8')
  const data = JSON.parse(raw) as Partial<Catalog>
  return {
    products: (data.products || []).filter((p) => p.published !== false),
    categories: data.categories || [],
  }
}

/** All published products regardless of availability (for /prodotti "Tutti" view). */
export function getPublishedProducts(): Product[] {
  return getCatalog().products
}

/** Only published products that are available for purchase (available !== false). */
export function getAvailableProducts(): Product[] {
  return getCatalog().products.filter((p) => p.available !== false)
}

/** Published products that are sold / historical (available === false). */
export function getSoldProducts(): Product[] {
  return getCatalog().products.filter((p) => p.available === false)
}

export function getCategories(): string[] {
  return getCatalog().categories
}

/** Distinct `target` values present among published products (count > 0), in fixed display order. */
export function getTargets(): string[] {
  const order: NonNullable<Product['target']>[] = ['bambino', 'donna', 'uomo', 'unisex']
  const present = new Set(
    getCatalog()
      .products.map((p) => p.target)
      .filter((t): t is NonNullable<Product['target']> => !!t)
  )
  return order.filter((t) => present.has(t))
}
