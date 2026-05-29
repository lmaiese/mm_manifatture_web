# Runbook — MM Manifatture Bot

> Documento operativo. Aggiornato incrementalmente ad ogni sprint.
> Obiettivo: chiunque con accesso può rimettere su il sistema in meno di 1 ora.

---

## Setup iniziale

### 1. Clona repo e attiva venv

```bash
git clone https://github.com/lmaiese/mm_manifatture_web.git
cd mm_manifatture_web/bot
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Compila .env con tutti i token
```

### 2. Configura Gmail App Password per reminder

1. Vai su https://myaccount.google.com/apppasswords
2. Crea App Password → nome "MM Bot Reminders"
3. Copia la password generata (16 caratteri)
4. In `.env`: `REMINDER_GMAIL_ADDRESS=maieseluigi@gmail.com`
5. In `.env`: `REMINDER_GMAIL_APP_PASSWORD=<password-16-caratteri>`

### 3. Attiva cron reminder (launchd macOS)

```bash
mkdir -p ~/Library/LaunchAgents
cp docs/launchd/com.mmbot.reminders.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.mmbot.reminders.plist
```

Verifica che giri:
```bash
launchctl list | grep mmbot
# test manuale:
/Users/maiesel/Obsidian/mm_manifatture_web/bot/.venv/bin/python \
  /Users/maiesel/Obsidian/mm_manifatture_web/bot/src/reminders/send.py
```

### 4. Aggiorna reminders.json con date reali

Dopo ogni setup (token Meta, dominio, VPS) aggiorna `bot/data/reminders.json`:
- `expiry_date`: data ISO (es. `"2026-07-28"`)
- `start_date`: data di go-live per i reminder ricorrenti

---

## Operazioni ricorrenti

### Refresh token Meta (ogni ~53gg)

```bash
# TODO Sprint 4: script refresh_meta_token.py
# Per ora: manuale su https://developers.facebook.com/tools/explorer
```

### Backup manuale SQLite

```bash
cp bot/bot.sqlite "bot/backups/bot_$(date +%Y%m%d).sqlite"
```

### Restart bot dopo crash

```bash
cd /Users/maiesel/Obsidian/mm_manifatture_web/bot
.venv/bin/python src/main.py
```

---

## Migrazione Mac → Hetzner VPS

1. Copia backup iCloud su VPS: `rsync -avz ~/Library/Mobile\ Documents/com~apple~CloudDocs/mmbot/ user@vps:~/mmbot_backup/`
2. Clona repo su VPS
3. Copia `.env` e `bot.sqlite` dal backup
4. Installa venv e dipendenze
5. Configura `systemd` invece di `launchd`
6. Avvia bot e verifica su bot diagnosi

---

## Troubleshooting

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| Bot non risponde | Mac in sleep / crash | Restart manuale, verifica `launchd` |
| Post non pubblicati su IG/FB | Token Meta scaduto | Refresh token, aggiorna `.env` |
| Sito non aggiornato | Vercel deploy hook fallito | Verifica quota build Vercel, triggera hook manualmente |
| Email reminder non arrivano | App Password Gmail scaduta / errore SMTP | Ri-genera App Password, verifica log `reminders_error.log` |
| Bot diagnosi silenzioso | Bot diagnosi crashato | Restart separato bot diagnosi |

---

*Aperto: 2026-05-29 (Sprint 1)*
*Aggiornare ad ogni sprint con nuove operazioni e troubleshooting.*
