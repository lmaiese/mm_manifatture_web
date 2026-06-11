import Image from 'next/image'
import type { Product } from '@/lib/catalog'

export default function ProductCard({ product }: { product: Product }) {
  const photo = product.photos?.[0]
  const isSold = product.available === false

  return (
    <article className={`bg-white rounded-lg border border-border overflow-hidden flex flex-col product-card${isSold ? ' product-card-sold' : ''}`}>
      <div className="aspect-[4/5] relative bg-background overflow-hidden">
        {photo ? (
          <Image
            src={photo}
            alt={product.description_site || product.title || product.category}
            fill
            className={`object-cover${isSold ? ' img-sold' : ''}`}
            sizes="(max-width: 768px) 50vw, 33vw"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-sm" style={{ color: 'var(--muted)' }}>
            Nessuna foto
          </div>
        )}
        {/* "fatto a mano" badge — top-left */}
        <span className="handmade-badge">fatto a mano</span>
        {/* "Venduto" badge — top-right, only for sold items */}
        {isSold && (
          <span className="sold-badge">✓ Venduto</span>
        )}
      </div>

      <div className="p-4 flex flex-col gap-2 flex-1">
        <div className="flex items-start justify-between gap-2">
          <span className="text-xs font-medium text-accent uppercase tracking-wide">
            {product.category}
          </span>
          {product.size && (
            <span className="text-xs" style={{ color: 'var(--muted)' }}>Taglia: {product.size}</span>
          )}
        </div>

        {product.description_site && (
          <p className={`text-sm leading-relaxed line-clamp-3${isSold ? ' text-muted-sold' : ' text-foreground'}`}>
            {product.description_site}
          </p>
        )}

        <div className="mt-auto pt-3 flex items-center justify-between border-t border-border">
          <span className={`font-serif text-lg font-semibold${isSold ? ' text-muted-sold' : ' text-foreground'}`}>
            €{product.price.toFixed(2)}
          </span>
          {isSold ? (
            <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>Non disponibile</span>
          ) : (
            <span className="text-xs" style={{ color: 'var(--muted)' }}>IVA inclusa</span>
          )}
        </div>

        {isSold ? (
          <div className="block text-center text-xs py-2 px-4 rounded border border-border select-none" style={{ color: 'var(--muted)' }}>
            Pezzo unico · Già venduto
          </div>
        ) : (
          <a
            href={`/prodotti/${product.id}`}
            className="block text-center text-sm py-2 px-4 rounded border border-accent text-accent hover:bg-accent hover:text-white transition-colors"
          >
            Vedi il pezzo →
          </a>
        )}
      </div>
    </article>
  )
}
