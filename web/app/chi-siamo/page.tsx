import Link from 'next/link'
import about from '@/content/about.json'

export const metadata = {
  title: 'Chi siamo — M&M Manifatture',
  description: 'Monica Scarpa realizza a mano ogni pezzo a Gioi, nel Cilento. Scopri la storia, i materiali e le tecniche dietro M&M Manifatture.',
}

export default function ChiSiamoPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">{about.title}</h1>
      <p className="text-accent font-medium mb-8">{about.subtitle}</p>

      {/* Storia */}
      <div className="space-y-5 text-foreground leading-relaxed">
        {about.body.slice(0, 2).map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </div>

      {/* Pull quote */}
      {about.pull_quote && (
        <blockquote className="about-pull-quote">
          <p>{about.pull_quote}</p>
        </blockquote>
      )}

      <div className="space-y-5 text-foreground leading-relaxed">
        {about.body.slice(2).map((para, i) => (
          <p key={i + 2}>{para}</p>
        ))}
      </div>

      {/* Valori */}
      {about.values.length > 0 && (
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          {about.values.map((v) => (
            <div key={v.label} className="bg-white rounded-lg border border-border p-6">
              <h3 className="font-serif text-lg font-semibold text-foreground mb-2">{v.label}</h3>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>{v.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* Materiali */}
      {about.materials && about.materials.length > 0 && (
        <section className="mt-14">
          <h2 className="font-serif text-2xl font-semibold text-foreground mb-2">I materiali che uso</h2>
          <p className="mb-6" style={{ color: 'var(--muted)' }}>Non compro in base al prezzo: compro in base a come si comporta il filo tra le mani.</p>
          <div className="grid md:grid-cols-3 gap-4">
            {about.materials.map((m) => (
              <div key={m.name} className="about-material-card">
                <h3 className="font-serif text-base font-semibold text-foreground mb-1">{m.name}</h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>{m.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Come lavoro */}
      {about.process_steps && about.process_steps.length > 0 && (
        <section className="mt-14">
          <h2 className="font-serif text-2xl font-semibold text-foreground mb-2">Come funziona un ordine</h2>
          <p className="mb-6" style={{ color: 'var(--muted)' }}>Nessun carrello, nessun checkout automatico. Ogni pezzo nasce da una conversazione.</p>
          <div className="space-y-4">
            {about.process_steps.map((s) => (
              <div key={s.step} className="about-process-step">
                <span className="about-process-number">{s.step}</span>
                <div>
                  <h3 className="font-serif text-base font-semibold text-foreground mb-0.5">{s.title}</h3>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>{s.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* CTA */}
      <div className="mt-14 flex flex-col sm:flex-row gap-4">
        <Link
          href="/prodotti"
          className="inline-block px-6 py-3 bg-accent text-white font-medium rounded hover:bg-accent-hover transition-colors text-center"
        >
          Sfoglia i prodotti
        </Link>
        <Link
          href="/contatti"
          className="inline-block px-6 py-3 border border-accent text-accent font-medium rounded hover:bg-accent hover:text-white transition-colors text-center"
        >
          Vuoi un pezzo personalizzato? →
        </Link>
      </div>
    </div>
  )
}
