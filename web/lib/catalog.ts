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
  scheduled_for?: string | null
}

export interface Catalog {
  products: Product[]
  categories: string[]
}

export function getCatalog(): Catalog {
  const filePath = path.join(process.cwd(), 'catalog.json')
  const raw = fs.readFileSync(filePath, 'utf-8')
  const data = JSON.parse(raw) as Partial<Catalog>
  return {
    products: (data.products || []).filter((p) => p.published !== false),
    categories: data.categories || [],
  }
}

export function getPublishedProducts(): Product[] {
  return getCatalog().products
}

export function getCategories(): string[] {
  return getCatalog().categories
}
