import { notFound } from 'next/navigation'
import Image from 'next/image'
import { getPublishedProducts } from '@/lib/catalog'
import type { Metadata } from 'next'

const WHATSAPP_PHONE = '393331276332'
const BASE_URL = 'https://mm-manifatture-web.vercel.app'

interface Props {
  params: { id: string }
}

export async function generateStaticParams() {
  const products = getPublishedProducts()
  return products.map((p) => ({ id: p.id }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const products = getPublishedProducts()
  const product = products.find((p) => p.id === params.id)
  if (!product) return {}

  const price = `€${product.price.toFixed(2).replace('.', ',')}`
  const description = product.description_site
    ? product.description_site.slice(0, 160)
    : `${product.category} artigianale — ${price}`

  return {
    title: `${product.category} ${price} — M&M Manifatture`,
    description,
  }
}

export default function ProductPage({ params }: Props) {
  const products = getPublishedProducts()
  const product = products.find((p) => p.id === params.id)

  if (!product) return notFound()

  const photo = product.photos?.[0]
  const price = `€${product.price.toFixed(2).replace('.', ',')}`
  const productUrl = `${BASE_URL}/prodotti/${product.id}`
  const waMessage = encodeURIComponent(
    `Ciao Monica, sono interessato a questo pezzo: ${productUrl}`
  )
  const waHref = `https://wa.me/${WHATSAPP_PHONE}?text=${waMessage}`

  return (
    <main className="product-detail-page">
      <div className="product-detail-container">

        {/* Back link */}
        <a href="/prodotti" className="product-detail-back">
          ← Tutti i prodotti
        </a>

        <div className="product-detail-layout">

          {/* Foto */}
          <div className="product-detail-image-wrap">
            {photo ? (
              <Image
                src={photo}
                alt={product.description_site || product.category}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, 50vw"
                priority
              />
            ) : (
              <div className="product-detail-no-photo">
                Foto non disponibile
              </div>
            )}
            <span className="handmade-badge">fatto a mano</span>
          </div>

          {/* Info */}
          <div className="product-detail-info">

            <span className="product-detail-category">
              {product.category}
            </span>

            <p className="product-detail-price">{price}</p>

            {product.size && (
              <p className="product-detail-size">
                <span className="contact-info-label">Taglia</span>
                {product.size}
              </p>
            )}

            {product.description_site && (
              <p className="product-detail-description">
                {product.description_site}
              </p>
            )}

            <div className="product-detail-cta-group">
              <a
                href={waHref}
                target="_blank"
                rel="noopener noreferrer"
                className="contact-cta-primary"
              >
                Ordina questo pezzo →
              </a>
              <a href="/prodotti" className="contact-cta-secondary">
                ← Tutti i prodotti
              </a>
            </div>

          </div>
        </div>
      </div>
    </main>
  )
}
