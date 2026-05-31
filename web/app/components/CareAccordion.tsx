'use client'

import { useState } from 'react'

const CARE: Record<string, string[]> = {
  Abbigliamento: [
    'Lavaggio a mano o lavatrice a 30°, programma delicati',
    'Asciugatura piatta su superficie orizzontale, lontano da fonti di calore',
    'Non centrifugare — il filato perde forma',
    'Stiratura con vapore a bassa temperatura, se necessario',
    'Riporre piegato, non appeso — evita che si allarghi sulle spalle',
  ],
  Altro: [
    'Pulizia a spot con panno umido — non immergere in acqua',
    'Conservare lontano dalla luce solare diretta',
    'Imbottitura in fibra naturale — maneggiare con cura',
  ],
}

const DEFAULT = [
  'Lavaggio delicato a mano, acqua tiepida',
  'Asciugatura piatta, lontano da fonti di calore',
  'Non centrifugare',
]

export default function CareAccordion({ category }: { category: string }) {
  const [open, setOpen] = useState(false)
  const rules = CARE[category] ?? DEFAULT

  return (
    <div className="care-accordion">
      <button
        className="care-accordion-trigger"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span>Cura e lavaggio</span>
        <svg
          width="16"
          height="16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', flexShrink: 0 }}
        >
          <path d="M4 6l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div className="care-accordion-body">
          {rules.map((rule, i) => (
            <div key={i} className="care-item">
              <span className="care-item-dot" aria-hidden="true">—</span>
              <span>{rule}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
