import about from '@/content/about.json'

export const metadata = {
  title: 'Chi siamo — M&M Manifatture',
}

export default function ChiSiamoPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-3xl font-semibold text-foreground mb-2">{about.title}</h1>
      <p className="text-accent font-medium mb-8">{about.subtitle}</p>

      <div className="space-y-5 text-foreground leading-relaxed">
        {about.body.map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </div>

      {about.values.length > 0 && (
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          {about.values.map((v) => (
            <div key={v.label} className="bg-white rounded-lg border border-border p-6">
              <h3 className="font-serif text-lg font-semibold text-foreground mb-2">{v.label}</h3>
              <p className="text-sm text-muted leading-relaxed">{v.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
