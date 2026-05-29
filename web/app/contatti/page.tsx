import contact from '@/content/contact.json'

export const metadata = {
  title: 'Contatti — M&M Manifatture',
}

export default function ContattiPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Contatti</h1>
      <p className="text-muted mb-10">Scrivici o vieni a trovarci in negozio.</p>

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
                  <span className="text-muted w-32 shrink-0">{h.days}</span>
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
              <label className="block text-sm text-muted mb-1" htmlFor="nome">Nome</label>
              <input
                id="nome"
                name="from"
                type="text"
                className="w-full border border-border rounded px-3 py-2 text-sm focus:outline-none focus:border-accent"
                placeholder="Il tuo nome"
              />
            </div>
            <div>
              <label className="block text-sm text-muted mb-1" htmlFor="msg">Messaggio</label>
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
            <p className="text-xs text-muted text-center">
              Il tuo client email si aprirà con il messaggio già compilato.
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
