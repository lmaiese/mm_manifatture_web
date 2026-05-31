import contact from '@/content/contact.json'
import MapsEmbed from '@/app/components/MapsEmbed'

export const metadata = {
  title: 'Contatti — M&M Manifatture',
  description: 'Contatta Monica Scarpa per ordini personalizzati o informazioni sui prodotti artigianali M&M Manifatture a Gioi (SA).',
}

export default function ContattiPage() {
  const waPhone = contact.phone.replace(/\s/g, '')
  const waMessage = encodeURIComponent(
    'Ciao Monica, ho visto il tuo sito e vorrei fare un ordine o avere informazioni sui tuoi pezzi artigianali.'
  )
  const waLink = `https://wa.me/39${waPhone}?text=${waMessage}`

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Contatti</h1>
      <p className="mb-10" style={{ color: 'var(--muted)' }}>
        Il modo più rapido per ordinare o fare una domanda è scrivere o chiamare direttamente Monica.
      </p>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Info */}
        <div className="space-y-5">
          <div>
            <p className="contact-info-label">Dove siamo</p>
            <p className="text-foreground">{contact.address}</p>
            <p className="text-foreground">{contact.city}</p>
          </div>

          <div>
            <p className="contact-info-label">Telefono</p>
            <a href={`tel:${contact.phone}`} className="text-accent hover:underline">
              {contact.phone}
            </a>
          </div>

          <div>
            <p className="contact-info-label">Email</p>
            <a href={`mailto:${contact.email}`} className="text-accent hover:underline">
              {contact.email}
            </a>
          </div>

          <div>
            <p className="contact-info-label">Orari negozio</p>
            <ul className="space-y-1">
              {contact.hours.map((h) => (
                <li key={h.days} className="flex gap-4 text-sm">
                  <span className="w-36 shrink-0" style={{ color: 'var(--muted)' }}>{h.days}</span>
                  <span className="text-foreground">{h.time}</span>
                </li>
              ))}
            </ul>
          </div>

          {(contact.social.instagram || contact.social.facebook) && (
            <div className="flex gap-4 pt-2">
              {contact.social.instagram && (
                <a
                  href={contact.social.instagram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-accent hover:underline"
                >
                  Instagram →
                </a>
              )}
              {contact.social.facebook && (
                <a
                  href={contact.social.facebook}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-accent hover:underline"
                >
                  Facebook →
                </a>
              )}
            </div>
          )}
        </div>

        {/* CTA dirette */}
        <div className="contact-cta-box">
          <h2 className="font-serif text-lg font-semibold text-foreground mb-2">Come contattarci</h2>
          <p className="text-sm mb-6" style={{ color: 'var(--muted)' }}>
            Monica risponde personalmente. Puoi scrivere su WhatsApp, chiamare o mandare un&apos;email — usa il canale che preferisci.
          </p>
          <div className="space-y-3">
            <a
              href={waLink}
              target="_blank"
              rel="noopener noreferrer"
              className="contact-cta-primary"
            >
              Scrivi su WhatsApp →
            </a>
            <a
              href={`tel:${contact.phone}`}
              className="contact-cta-secondary"
            >
              Chiama Monica
            </a>
            <a
              href={`mailto:${contact.email}`}
              className="contact-cta-secondary"
            >
              Manda un&apos;email
            </a>
          </div>
        </div>
      </div>

      {/* Dove siamo — mappa */}
      <section className="mt-12">
        <h2 className="font-serif text-xl font-semibold text-foreground mb-4">Dove siamo</h2>
        <MapsEmbed />
      </section>

      {/* Ordini personalizzati */}
      <section className="mt-14 p-8 bg-white rounded-lg border border-border">
        <h2 className="font-serif text-2xl font-semibold text-foreground mb-2">Vuoi qualcosa di specifico?</h2>
        <p className="mb-8" style={{ color: 'var(--muted)' }}>
          Monica lo fa su misura per te — colore, taglia e materiale a tua scelta. Non c&apos;è niente che non puoi chiedere.
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="custom-order-step">
            <span className="custom-order-number">01</span>
            <h3 className="font-serif text-base font-semibold text-foreground mb-1">Descrivi cosa vuoi</h3>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
              Scrivi o chiama. Racconta il pezzo: tipologia, colore, taglia, per chi è. Più dettagli dai, meglio Monica può guidarti sui materiali disponibili.
            </p>
          </div>
          <div className="custom-order-step">
            <span className="custom-order-number">02</span>
            <h3 className="font-serif text-base font-semibold text-foreground mb-1">Monica ti risponde con tempi e costi</h3>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
              Entro 24 ore ricevi una risposta con disponibilità dei filati, tempo di realizzazione stimato e prezzo. Nessun impegno finché non confermi.
            </p>
          </div>
          <div className="custom-order-step">
            <span className="custom-order-number">03</span>
            <h3 className="font-serif text-base font-semibold text-foreground mb-1">Ricevi il pezzo</h3>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
              Ritiro in negozio a Gioi o spedizione in Italia. Il pezzo parte solo quando Monica è soddisfatta del risultato.
            </p>
          </div>
        </div>
        <p className="mt-6 text-sm" style={{ color: 'var(--muted)' }}>
          <strong className="text-foreground">Tempi indicativi:</strong> accessori e cappellini 3–5 giorni · cardigan e maglioncini 7–15 giorni. I tempi dipendono dal carico di lavoro corrente — Monica lo comunica sempre in anticipo.
        </p>
      </section>
    </div>
  )
}
