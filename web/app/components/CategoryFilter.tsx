'use client'

import { useRouter, useSearchParams } from 'next/navigation'

export default function CategoryFilter({ categories }: { categories: string[] }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const active = searchParams.get('categoria') || ''

  const set = (cat: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (cat) params.set('categoria', cat)
    else params.delete('categoria')
    router.replace(`/prodotti?${params.toString()}`, { scroll: false })
  }

  return (
    <div className="flex flex-wrap gap-2 mb-8">
      <button
        onClick={() => set('')}
        className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
          !active
            ? 'bg-accent text-white border-accent'
            : 'border-border text-muted hover:border-accent hover:text-accent'
        }`}
      >
        Tutti
      </button>
      {categories.map((cat) => (
        <button
          key={cat}
          onClick={() => set(cat)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
            active === cat
              ? 'bg-accent text-white border-accent'
              : 'border-border text-muted hover:border-accent hover:text-accent'
          }`}
        >
          {cat}
        </button>
      ))}
    </div>
  )
}
