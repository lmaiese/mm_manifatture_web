import { notFound } from 'next/navigation'
import { getPublishedProducts } from '@/lib/catalog'
import type { Metadata } from 'next'
import PhotoGallery from '@/app/components/PhotoGallery'
import CareAccordion from '@/app/components/CareAccordion'
import ProductCard from '@/app/components/ProductCard'

const WHATSAPP_PHONE = '393331276332'
const BASE_URL = 'https://mmmanifatture.it'

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

  const isSold = product.available === false
  const price = `€${product.price.toFixed(2).replace('.', ',')}`
  const productUrl = `${BASE_URL}/prodotti/${product.id}`
  const waMessage = encodeURIComponent(
    `Ciao Monica, sono interessata/o a questo pezzo: ${productUrl}`
  )
  const waHref = `https://wa.me/${WHATSAPP_PHONE}?text=${waMessage}`
  const waSimilarMessage = encodeURIComponent(
    `Ciao Monica, ho visto questo pezzo sul tuo sito (${productUrl}) ma risulta venduto. Potresti realizzarne uno simile?`
  )
  const waSimilarHref = `https://wa.me/${WHATSAPP_PHONE}?text=${waSimilarMessage}`

  const related = products
    .filter((p) => p.category === product.category && p.id !== product.id && p.available !== false)
    .slice(0, 4)

  return (
    <main className="product-detail-page">
      <div className="product-detail-container">

        <a href="/prodotti" className="product-detail-back">
          ← Tutti i prodotti
        </a>

        <div className="product-detail-layout">

          {/* Gallery */}
          <PhotoGallery
            photos={product.photos ?? []}
            alt={product.description_site || product.category}
            isSold={isSold}
          />

          {/* Info */}
          <div className="product-detail-info">

            <span className="product-detail-category">{product.category}</span>

            <p className={`product-detail-price${isSold ? ' product-detail-price-sold' : ''}`}>{price}</p>

            <div className="product-detail-uniqueness">
              <span className="product-detail-uniqueness-dot">✦</span>
              <span>Pezzo unico</span>
              {!isSold && (
                <>
                  <span className="product-detail-uniqueness-sep">·</span>
                  <span>Realizzazione: 3–5 giorni lavorativi</span>
                </>
              )}
              {isSold && (
                <>
                  <span className="product-detail-uniqueness-sep">·</span>
                  <span className="product-detail-sold-label">✓ Già venduto</span>
                </>
              )}
            </div>

            {product.size && (
              <p className="product-detail-size">
                <span className="contact-info-label">Taglia</span>
                {product.size}
              </p>
            )}

            {product.description_site && (
              <p className={`product-detail-description${isSold ? ' product-detail-description-sold' : ''}`}>
                {product.description_site}
              </p>
            )}

            {!isSold && <CareAccordion category={product.category} />}

            {isSold ? (
              <div className="product-sold-notice">
                <p className="product-sold-notice-title">Questo pezzo è già stato venduto</p>
                <p className="product-sold-notice-body">
                  Monica può realizzarne uno simile su commissione — colori, taglia e materiali a tua scelta.
                </p>
              </div>
            ) : (
              <div className="product-order-steps">
                <p className="product-order-title">Come funziona l'ordine</p>
                <div className="product-order-list">
                  <div className="product-order-step">
                    <span className="product-order-number">1</span>
                    <div>
                      <p className="product-order-step-title">Scrivi su WhatsApp</p>
                      <p className="product-order-step-desc">Monica risponde entro 24 ore e conferma disponibilità.</p>
                    </div>
                  </div>
                  <div className="product-order-step">
                    <span className="product-order-number">2</span>
                    <div>
                      <p className="product-order-step-title">Conferma e personalizzazione</p>
                      <p className="product-order-step-desc">Taglia, colore, eventuali varianti. Ogni pezzo può essere adattato.</p>
                    </div>
                  </div>
                  <div className="product-order-step">
                    <span className="product-order-number">3</span>
                    <div>
                      <p className="product-order-step-title">Ritiro o spedizione</p>
                      <p className="product-order-step-desc">Ritiro a Gioi (SA) o spedizione in tutta Italia.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="product-detail-cta-group">
              {isSold ? (
                <a
                  href={waSimilarHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="contact-cta-primary"
                >
                  Chiedi qualcosa di simile →
                </a>
              ) : (
                <a
                  href={waHref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="contact-cta-primary"
                >
                  Ordina questo pezzo →
                </a>
              )}
              <a href="/prodotti" className="contact-cta-secondary">
                ← Tutti i prodotti
              </a>
            </div>

          </div>
        </div>

        {related.length > 0 && (
          <div className="related-products-section">
            <h2 className="related-products-title">Altri pezzi di Monica</h2>
            <div className="related-products-grid">
              {related.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </div>
        )}

      </div>
    </main>
  )
}
