'use client'

import { useCallback, useState } from 'react'
import CookieBanner from './CookieBanner'
import GALoader from './GALoader'

const GA_ID = process.env.NEXT_PUBLIC_GA_ID || ''

export default function AnalyticsProvider() {
  const [gaEnabled, setGaEnabled] = useState(false)

  const handleConsent = useCallback((state: 'accepted' | 'declined') => {
    setGaEnabled(state === 'accepted')
  }, [])

  return (
    <>
      {gaEnabled && GA_ID && <GALoader gaId={GA_ID} />}
      <CookieBanner onConsent={handleConsent} />
    </>
  )
}
