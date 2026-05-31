import type { Metadata } from 'next'
import './globals.css'
import Header from './components/Header'
import Footer from './components/Footer'
import AnalyticsProvider from './components/AnalyticsProvider'

export const metadata: Metadata = {
  title: 'M&M Manifatture di Scarpa Monica — Artigianato fatto a mano',
  description: 'Prodotti artigianali unici realizzati a mano da Monica Scarpa. Borse, gioielli, oggetti per la casa e molto altro.',
  openGraph: {
    title: 'M&M Manifatture di Scarpa Monica',
    description: 'Prodotti artigianali unici realizzati a mano.',
    type: 'website',
    images: [{ url: '/logo-en.jpeg', width: 1080, height: 1080, alt: 'M&M Manifatture' }],
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
        <AnalyticsProvider />
      </body>
    </html>
  )
}
