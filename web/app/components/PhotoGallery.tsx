'use client'

import Image from 'next/image'
import { useCallback, useEffect, useRef, useState } from 'react'

interface Props {
  photos: string[]
  alt: string
  isSold?: boolean
}

// Auto-rotate interval (ms) — paused on hover/zoom and while the lightbox is open.
const AUTOROTATE_MS = 4500

export default function PhotoGallery({ photos, alt, isSold = false }: Props) {
  const [active, setActive] = useState(0)
  const [zoomOrigin, setZoomOrigin] = useState<{ x: number; y: number } | null>(null)
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const current = photos[active] ?? null
  const hasMultiple = photos.length > 1

  const goTo = useCallback(
    (index: number) => {
      if (photos.length === 0) return
      setActive(((index % photos.length) + photos.length) % photos.length)
    },
    [photos.length]
  )

  // --- Auto-rotate carousel (paused while zooming or while lightbox is open) ---
  useEffect(() => {
    if (!hasMultiple || zoomOrigin || lightboxOpen) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }
    intervalRef.current = setInterval(() => {
      setActive((i) => (i + 1) % photos.length)
    }, AUTOROTATE_MS)
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [hasMultiple, zoomOrigin, lightboxOpen, photos.length])

  // --- Lightbox: keyboard navigation + lock body scroll while open ---
  useEffect(() => {
    if (!lightboxOpen) return

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setLightboxOpen(false)
      else if (e.key === 'ArrowRight') goTo(active + 1)
      else if (e.key === 'ArrowLeft') goTo(active - 1)
    }

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [lightboxOpen, active, goTo])

  // --- Zoom on hover (desktop only — gated in CSS via hover/pointer media query) ---
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    setZoomOrigin({ x: Math.min(100, Math.max(0, x)), y: Math.min(100, Math.max(0, y)) })
  }

  const handleMouseLeave = () => setZoomOrigin(null)

  const openLightbox = () => {
    if (current) setLightboxOpen(true)
  }

  const handleMainKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      openLightbox()
    }
  }

  return (
    <div className="photo-gallery">
      <div
        className="photo-gallery-main"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={openLightbox}
        onKeyDown={handleMainKeyDown}
        role={current ? 'button' : undefined}
        tabIndex={current ? 0 : undefined}
        aria-label={current ? 'Apri immagine a schermo intero' : undefined}
      >
        {current ? (
          <Image
            src={current}
            alt={alt}
            fill
            className={`object-cover photo-gallery-img${isSold ? ' img-sold' : ''}${zoomOrigin ? ' is-zoomed' : ''}`}
            style={zoomOrigin ? { transformOrigin: `${zoomOrigin.x}% ${zoomOrigin.y}%` } : undefined}
            sizes="(max-width: 768px) 100vw, 50vw"
            priority
          />
        ) : (
          <div className="product-detail-no-photo">Foto non disponibile</div>
        )}
        <span className="handmade-badge">fatto a mano</span>
        {isSold && <span className="sold-badge">✓ Venduto</span>}
        {current && (
          <span className="photo-gallery-expand-hint" aria-hidden="true">⤢</span>
        )}
      </div>

      {hasMultiple && (
        <div className="photo-gallery-thumbs">
          {photos.map((src, i) => (
            <button
              key={i}
              onClick={() => goTo(i)}
              className={`photo-gallery-thumb${i === active ? ' active' : ''}`}
              aria-label={`Foto ${i + 1}`}
            >
              <Image
                src={src}
                alt={`${alt} — foto ${i + 1}`}
                fill
                className="object-cover"
                sizes="64px"
              />
            </button>
          ))}
        </div>
      )}

      {lightboxOpen && current && (
        <div
          className="photo-lightbox"
          onClick={() => setLightboxOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-label={alt}
        >
          <button
            className="photo-lightbox-close"
            onClick={() => setLightboxOpen(false)}
            aria-label="Chiudi"
          >
            ✕
          </button>

          {hasMultiple && (
            <button
              className="photo-lightbox-nav photo-lightbox-prev"
              onClick={(e) => {
                e.stopPropagation()
                goTo(active - 1)
              }}
              aria-label="Foto precedente"
            >
              ‹
            </button>
          )}

          <div className="photo-lightbox-image-wrap" onClick={(e) => e.stopPropagation()}>
            <Image src={current} alt={alt} fill className="object-contain" sizes="100vw" />
          </div>

          {hasMultiple && (
            <button
              className="photo-lightbox-nav photo-lightbox-next"
              onClick={(e) => {
                e.stopPropagation()
                goTo(active + 1)
              }}
              aria-label="Foto successiva"
            >
              ›
            </button>
          )}

          {hasMultiple && (
            <div className="photo-lightbox-counter">
              {active + 1} / {photos.length}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
