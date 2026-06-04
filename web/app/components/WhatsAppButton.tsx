'use client'

import { usePathname } from 'next/navigation'

const PHONE = '393331276332'
const GENERIC_MESSAGE =
  'Ciao Monica, ho visto il tuo sito e vorrei sapere di più sui tuoi lavori. 🧶'

function buildWhatsAppUrl(message: string): string {
  return `https://wa.me/${PHONE}?text=${encodeURIComponent(message)}`
}

export default function WhatsAppButton() {
  const pathname = usePathname()

  // Nascondi su /contatti — ha già CTA WhatsApp dedicate
  if (pathname === '/contatti') return null

  const isProductPage = /^\/prodotti\/[^/]+$/.test(pathname)

  let href: string
  let ariaLabel: string

  if (isProductPage) {
    const productUrl =
      typeof window !== 'undefined'
        ? window.location.origin + pathname
        : `https://mmmanifatture.it${pathname}`
    const message = `Ciao Monica, sono interessata/o a questo pezzo: ${productUrl}`
    href = buildWhatsAppUrl(message)
    ariaLabel = 'Chiedi a Monica su WhatsApp per questo prodotto'
  } else {
    href = buildWhatsAppUrl(GENERIC_MESSAGE)
    ariaLabel = 'Contatta Monica su WhatsApp'
  }

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={ariaLabel}
      className="whatsapp-button"
    >
      {/* WhatsApp logo SVG */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 32 32"
        width="28"
        height="28"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M16 0C7.163 0 0 7.163 0 16c0 2.822.736 5.472 2.027 7.773L0 32l8.476-2.003A15.934 15.934 0 0 0 16 32c8.837 0 16-7.163 16-16S24.837 0 16 0zm0 29.333a13.27 13.27 0 0 1-6.773-1.853l-.486-.289-5.03 1.188 1.228-4.895-.317-.502A13.266 13.266 0 0 1 2.667 16C2.667 8.636 8.636 2.667 16 2.667S29.333 8.636 29.333 16 23.364 29.333 16 29.333zm7.3-9.973c-.4-.2-2.363-1.166-2.73-1.299-.366-.133-.632-.2-.9.2-.266.4-1.032 1.3-1.265 1.566-.233.267-.466.3-.866.1-.4-.2-1.688-.623-3.215-1.984-1.188-1.06-1.99-2.37-2.223-2.77-.233-.4-.025-.616.175-.815.18-.18.4-.466.6-.7.2-.233.266-.4.4-.666.133-.267.066-.5-.033-.7-.1-.2-.9-2.166-1.232-2.965-.325-.78-.656-.674-.9-.686l-.766-.013c-.267 0-.7.1-1.066.5-.366.4-1.4 1.366-1.4 3.332s1.433 3.865 1.633 4.132c.2.266 2.82 4.3 6.832 6.032.955.413 1.7.659 2.28.844.958.305 1.831.262 2.52.159.769-.115 2.363-.966 2.697-1.9.333-.933.333-1.732.233-1.9-.1-.167-.366-.267-.766-.467z" />
      </svg>
    </a>
  )
}
