'use client'

import { useEffect } from 'react'

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void
    dataLayer?: unknown[]
  }
}

export default function GALoader({ gaId }: { gaId: string }) {
  useEffect(() => {
    if (!gaId || typeof window === 'undefined') return

    const script1 = document.createElement('script')
    script1.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`
    script1.async = true
    document.head.appendChild(script1)

    window.dataLayer = window.dataLayer || []
    window.gtag = function (...args: unknown[]) {
      window.dataLayer!.push(args)
    }
    window.gtag('js', new Date())
    window.gtag('config', gaId, { anonymize_ip: true })
  }, [gaId])

  return null
}
