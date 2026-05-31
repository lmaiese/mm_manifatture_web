import type { Metadata } from 'next'
import './globals.css'
import Header from './components/Header'
import Footer from './components/Footer'
import AnalyticsProvider from './components/AnalyticsProvider'

export const metadata: Metadata = {
  metadataBase: new URL('https://mmmanifatture.it'),
  title: 'M&M Manifatture di Scarpa Monica — Artigianato fatto a mano',
  description: 'Maglioncini in lana merinos, bambole di pezza e accessori artigianali fatti a mano da Monica Scarpa a Gioi, nel Cilento. Ogni pezzo è unico.',
  openGraph: {
    title: 'M&M Manifatture di Scarpa Monica — Artigianato fatto a mano',
    description: 'Maglioncini in lana merinos, bambole di pezza e accessori artigianali fatti a mano da Monica Scarpa a Gioi, nel Cilento.',
    type: 'website',
    locale: 'it_IT',
    images: [{ url: '/logo-en.jpeg', width: 1080, height: 1080, alt: 'M&M Manifatture — Artigianato fatto a mano' }],
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
