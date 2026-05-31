'use client'

import Image from 'next/image'
import { useState } from 'react'

interface Props {
  photos: string[]
  alt: string
}

export default function PhotoGallery({ photos, alt }: Props) {
  const [active, setActive] = useState(0)
  const current = photos[active] ?? null

  return (
    <div className="photo-gallery">
      <div className="photo-gallery-main">
        {current ? (
          <Image
            src={current}
            alt={alt}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 50vw"
            priority
          />
        ) : (
          <div className="product-detail-no-photo">Foto non disponibile</div>
        )}
        <span className="handmade-badge">fatto a mano</span>
      </div>

      {photos.length > 1 && (
        <div className="photo-gallery-thumbs">
          {photos.map((src, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
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
    </div>
  )
}
