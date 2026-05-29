import Image from 'next/image'
import type { Product } from '@/lib/catalog'

export default function ProductCard({ product }: { product: Product }) {
  const photo = product.photos?.[0]

  return (
    <article className="bg-white rounded-lg border border-border overflow-hidden flex flex-col product-card">
      <div className="aspect-square relative bg-background overflow-hidden">
        {photo ? (
          <Image
            src={photo}
            alt={product.description_site || product.category}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 50vw, 33vw"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted text-sm">
            Nessuna foto
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col gap-2 flex-1">
        <div className="flex items-start justify-between gap-2">
          <span className="text-xs font-medium text-accent uppercase tracking-wide">
            {product.category}
          </span>
          {product.size && (
            <span className="text-xs text-muted">Taglia: {product.size}</span>
          )}
        </div>

        {product.description_site && (
          <p className="text-sm text-foreground leading-relaxed line-clamp-3">
            {product.description_site}
          </p>
        )}

        <div className="mt-auto pt-3 flex items-center justify-between border-t border-border">
          <span className="font-serif text-lg font-semibold text-foreground">
            €{product.price.toFixed(2)}
          </span>
          <span className="text-xs text-muted">IVA inclusa</span>
        </div>

        <a
          href="/contatti"
          className="block text-center text-sm py-2 px-4 rounded border border-accent text-accent hover:bg-accent hover:text-white transition-colors"
        >
          Contattaci per acquistare
        </a>
      </div>
    </article>
  )
}
