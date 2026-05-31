import contact from '@/content/contact.json'

export const metadata = {
  title: 'Contatti — M&M Manifatture',
}

export default function ContattiPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Contatti</h1>
      <p className="mb-10" style={{ color: 'var(--muted)' }}>Scrivici o vieni a trovarci in negozio.</p>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Info */}
        <div className="space-y-5">
          <div>
            <h2 className="font-serif text-lg font-semibold text-foreground mb-1">Dove siamo</h2>
            <p className="text-foreground">{contact.address}</p>
            <p className="text-foreground">{contact.city}</p>
          </div>

          <div>
            <h2 className="font-serif text-lg font-semibold text-foreground mb-1">Telefono</h2>
            <a href={`tel:${contact.phone}`} className="text-accent hover:underline">
              {contact.phone}
            </a>
          </div>

          <div>
            <h2 className="font-serif text-lg font-semibold text-foreground mb-1">Email</h2>
            <a href={`mailto:${contact.email}`} className="text-accent hover:underline">
              {contact.email}
            </a>
          </div>

          <div>
            <h2 className="font-serif text-lg font-semibold text-foreground mb-2">Orari</h2>
            <ul className="space-y-1">
              {contact.hours.map((h) => (
                <li key={h.days} className="flex gap-4 text-sm">
                  <span className="w-32 shrink-0" style={{ color: 'var(--muted)' }}>{h.days}</span>
                  <span className="text-foreground">{h.time}</span>
                </li>
              ))}
            </ul>
          </div>

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
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg border border-border p-6">
          <h2 className="font-serif text-lg font-semibold text-foreground mb-4">Mandaci un messaggio</h2>
          <form
            action={`mailto:${contact.email}`}
            method="GET"
            className="space-y-4"
          >
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--muted)' }} htmlFor="nome">Nome</label>
              <input
                id="nome"
                name="from"
                type="text"
                className="w-full border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="Il tuo nome"
              />
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: 'var(--muted)' }} htmlFor="msg">Messaggio</label>
              <textarea
                id="msg"
                name="body"
                rows={4}
                className="w-full border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent resize-none"
                placeholder="Come possiamo aiutarti?"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 bg-accent text-white text-sm rounded hover:bg-accent-hover transition-colors"
            >
              Apri client email
            </button>
            <p className="text-xs text-center" style={{ color: 'var(--muted)' }}>
              Il tuo client email si aprirà con il messaggio già compilato.
            </p>
          </form>
        </div>
      </div>

      {/* Ordini personalizzati */}
      <section className="mt-14 p-8 bg-white rounded-lg border border-border">
        <h2 className="font-serif text-2xl font-semibold text-foreground mb-2">Ordini personalizzati</h2>
        <p className="mb-8" style={{ color: 'var(--muted)' }}>
          Non trovi quello che cerchi tra i prodotti disponibili? Monica può realizzarlo apposta per te — colore, misura e materiale a tua scelta.
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
          <strong className="text-foreground">Tempi indicativi:</strong> accessori 3–5 giorni · bambole di pezza 7–10 giorni · maglioncini 10–15 giorni. I tempi dipendono dal carico di lavoro corrente — Monica lo comunica sempre in anticipo.
        </p>
      </section>
    </div>
  )
}
