import legal from '@/content/legal.json'

export const metadata = {
  title: 'Note legali — M&M Manifatture',
}

export default function NoteLegaliPage() {
  const year = new Date().getFullYear()

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">Note legali</h1>
      <p className="text-muted text-sm mb-10">Ultimo aggiornamento: {year}</p>

      {/* Anchor nav */}
      <nav className="bg-white border border-border rounded-lg p-5 mb-10 text-sm space-y-2">
        <a href="#societa" className="block text-accent hover:underline">1. Informazioni societarie</a>
        <a href="#privacy" className="block text-accent hover:underline">2. Privacy Policy</a>
        <a href="#cookie" className="block text-accent hover:underline">3. Cookie Policy</a>
        <a href="#termini" className="block text-accent hover:underline">4. Termini di utilizzo</a>
      </nav>

      {/* 1. Informazioni societarie */}
      <section id="societa" className="mb-12 scroll-mt-20">
        <h2 className="font-serif text-xl font-semibold text-foreground mb-4">1. Informazioni societarie</h2>
        <p className="text-sm text-muted mb-4">
          Ai sensi dell'art. 7 D.Lgs. 70/2003 (Commercio Elettronico), le informazioni sul soggetto responsabile del sito:
        </p>
        <div className="bg-white border border-border rounded-lg p-5 space-y-2 text-sm">
          <div className="flex gap-4"><span className="text-muted w-32 shrink-0">Ragione sociale</span><span>{legal.company_name}</span></div>
          <div className="flex gap-4"><span className="text-muted w-32 shrink-0">P.IVA</span><span>{legal.vat_number}</span></div>
          <div className="flex gap-4"><span className="text-muted w-32 shrink-0">Sede legale</span><span>{legal.legal_address}</span></div>
          <div className="flex gap-4"><span className="text-muted w-32 shrink-0">Email</span>
            <a href={`mailto:${legal.email}`} className="text-accent hover:underline">{legal.email}</a>
          </div>
        </div>
      </section>

      {/* 2. Privacy Policy */}
      <section id="privacy" className="mb-12 scroll-mt-20 space-y-4 text-sm leading-relaxed text-foreground">
        <h2 className="font-serif text-xl font-semibold text-foreground mb-4">2. Privacy Policy</h2>
        <p>
          Il presente documento descrive come {legal.company_name} (di seguito "Titolare") raccoglie e tratta i dati personali degli utenti che visitano questo sito web, ai sensi del Regolamento UE 2016/679 (GDPR).
        </p>
        <h3 className="font-semibold text-foreground mt-6">Titolare del trattamento</h3>
        <p>{legal.company_name} — {legal.legal_address} — <a href={`mailto:${legal.email}`} className="text-accent hover:underline">{legal.email}</a></p>

        <h3 className="font-semibold text-foreground mt-6">Dati raccolti</h3>
        <ul className="list-disc pl-5 space-y-1 text-muted">
          <li><span className="text-foreground">Dati di navigazione (Google Analytics 4)</span>: pagine visitate, durata sessione, dispositivo, paese. IP anonimizzato. Raccolti solo previo consenso esplicito.</li>
          <li><span className="text-foreground">Dati del form contatti</span>: nome e messaggio, trasmessi direttamente via client email dell'utente. Il sito non archivia né trasmette questi dati a server propri.</li>
        </ul>

        <h3 className="font-semibold text-foreground mt-6">Base giuridica</h3>
        <ul className="list-disc pl-5 space-y-1 text-muted">
          <li>Analytics: <span className="text-foreground">consenso</span> (art. 6.1.a GDPR) — raccolta avviene solo dopo opt-in esplicito nel banner cookie.</li>
          <li>Form contatti: <span className="text-foreground">esecuzione di misure precontrattuali</span> (art. 6.1.b GDPR).</li>
        </ul>

        <h3 className="font-semibold text-foreground mt-6">Periodo di conservazione</h3>
        <p className="text-muted">Dati analytics: 14 mesi (impostazione predefinita GA4, configurabile). Dati form contatti: non archiviati dal sito.</p>

        <h3 className="font-semibold text-foreground mt-6">Trasferimenti extra-UE</h3>
        <p className="text-muted">Google Analytics trasferisce dati verso server Google LLC (USA) sulla base delle Standard Contractual Clauses approvate dalla Commissione Europea.</p>

        <h3 className="font-semibold text-foreground mt-6">Diritti dell'interessato</h3>
        <p className="text-muted">Hai diritto di accesso, rettifica, cancellazione, limitazione, portabilità e opposizione al trattamento. Per esercitarli scrivi a{' '}
          <a href={`mailto:${legal.email}`} className="text-accent hover:underline">{legal.email}</a>.
          Hai inoltre il diritto di proporre reclamo al Garante per la Protezione dei Dati Personali (<a href="https://www.garanteprivacy.it" className="text-accent hover:underline" target="_blank" rel="noopener noreferrer">garanteprivacy.it</a>).
        </p>
      </section>

      {/* 3. Cookie Policy */}
      <section id="cookie" className="mb-12 scroll-mt-20 space-y-4 text-sm leading-relaxed text-foreground">
        <h2 className="font-serif text-xl font-semibold text-foreground mb-4">3. Cookie Policy</h2>
        <p>Questo sito utilizza esclusivamente le seguenti tipologie di cookie:</p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 pr-4 text-muted font-medium">Tipo</th>
                <th className="text-left py-2 pr-4 text-muted font-medium">Nome</th>
                <th className="text-left py-2 pr-4 text-muted font-medium">Scopo</th>
                <th className="text-left py-2 text-muted font-medium">Opt-in</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="py-2 pr-4">Tecnico</td>
                <td className="py-2 pr-4 font-mono text-xs">mm_cookie_consent</td>
                <td className="py-2 pr-4 text-muted">Salva la scelta cookie dell'utente</td>
                <td className="py-2">No (necessario)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">Analytics</td>
                <td className="py-2 pr-4 font-mono text-xs">_ga, _ga_*</td>
                <td className="py-2 pr-4 text-muted">Google Analytics 4 — statistiche anonime di utilizzo</td>
                <td className="py-2">Sì</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p className="text-muted">
          Nessun cookie di profilazione, marketing o di terze parti al di fuori di Google Analytics (attivato solo con consenso).
        </p>
        <p className="text-muted">
          Puoi revocare il consenso in qualsiasi momento svuotando il localStorage del browser o tramite le impostazioni del tuo browser.
        </p>
      </section>

      {/* 4. Termini */}
      <section id="termini" className="mb-12 scroll-mt-20 space-y-4 text-sm leading-relaxed text-foreground">
        <h2 className="font-serif text-xl font-semibold text-foreground mb-4">4. Termini di utilizzo</h2>
        <ul className="list-disc pl-5 space-y-2 text-muted">
          <li>Questo sito è una <span className="text-foreground">vetrina informativa</span>. Non effettua vendite online né raccoglie dati di pagamento.</li>
          <li>I prezzi indicati sono a titolo informativo e si intendono <span className="text-foreground">IVA inclusa</span>, ai sensi della Direttiva 98/6/CE.</li>
          <li>Per acquistare un prodotto, contattare direttamente il negozio tramite la pagina <a href="/contatti" className="text-accent hover:underline">Contatti</a>.</li>
          <li>Tutti i contenuti (testi, foto, design) sono di proprietà di {legal.company_name} e sono protetti da copyright. È vietata la riproduzione senza autorizzazione scritta.</li>
          <li>Il Titolare non si assume responsabilità per eventuali errori nei prezzi o nelle descrizioni dei prodotti. Le informazioni correnti sono sempre disponibili contattando il negozio.</li>
        </ul>
        <p className="text-muted mt-4">
          Foro competente: Tribunale della sede legale del Titolare. Legge applicabile: legge italiana.
        </p>
      </section>
    </div>
  )
}
