# mm_manifatture_web

Bot Telegram + sito vetrina per negozio di artigianato.

## Struttura

```
mm_manifatture_web/
├── bot/          # Python — Telegram bot (python-telegram-bot v20)
│   ├── src/
│   └── tests/
└── web/          # Next.js — sito vetrina statico (Vercel)
    ├── src/
    └── public/
```

## Come avviare

### Bot
```bash
cd bot
pip install -r requirements.txt
python src/main.py
```

### Sito
```bash
cd web
npm install
npm run dev
```

## Deploy

- **Web**: Vercel (deploy automatico su push main)
- **Bot**: Mac locale con launchd (v1), VPS Hetzner (v2)
