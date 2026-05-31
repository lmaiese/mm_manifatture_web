'use client'

import { useState } from 'react'

export default function MapsEmbed() {
  const [show, setShow] = useState(false)

  if (!show) {
    return (
      <div className="maps-placeholder">
        <p className="maps-placeholder-address">Via Garibaldi 17, Gioi (SA) 84056</p>
        <button
          onClick={() => setShow(true)}
          className="maps-placeholder-btn"
          type="button"
        >
          Mostra su Google Maps
        </button>
        <p className="maps-placeholder-note">
          La mappa è fornita da Google Maps.{' '}
          <a
            href="https://maps.google.com/?q=Via+Garibaldi+17,+Gioi+SA+84056"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-accent"
          >
            Apri direttamente →
          </a>
        </p>
      </div>
    )
  }

  return (
    <div className="maps-embed-wrapper">
      <iframe
        src="https://maps.google.com/maps?q=Via+Garibaldi+17,+Gioi+SA+84056,+Italia&output=embed&hl=it"
        title="M&M Manifatture — Via Garibaldi 17, Gioi (SA)"
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        allowFullScreen
      />
    </div>
  )
}
