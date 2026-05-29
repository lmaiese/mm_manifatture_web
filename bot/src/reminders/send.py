"""
Reminder engine — legge data/reminders.json e manda email via Gmail SMTP.
Eseguito ogni mattina da launchd (vedi docs/launchd/com.mmbot.reminders.plist).

Configurazione richiesta in .env:
  REMINDER_GMAIL_ADDRESS  — indirizzo mittente (Gmail)
  REMINDER_GMAIL_APP_PASSWORD  — App Password Gmail (non la password account)
"""

import json
import logging
import os
import smtplib
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s — reminders — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent.parent.parent / "data" / "reminders.json"
STATE_FILE = Path(__file__).parent.parent.parent / "data" / "reminders_state.json"


def load_reminders() -> list[dict]:
    with open(DATA_FILE) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def send_email(to: str, subject: str, body: str) -> None:
    sender = os.environ["REMINDER_GMAIL_ADDRESS"]
    password = os.environ["REMINDER_GMAIL_APP_PASSWORD"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"MM Bot Reminders <{sender}>"
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, to, msg.as_string())
    logger.info("Email inviata: %s → %s", subject, to)


def check_expiry(reminder: dict, today: date) -> str | None:
    """Restituisce messaggio se scadenza entro warn_days_before, None altrimenti."""
    if not reminder.get("expiry_date"):
        return None
    expiry = date.fromisoformat(reminder["expiry_date"])
    warn_days = reminder.get("warn_days_before", 7)
    days_left = (expiry - today).days
    if 0 <= days_left <= warn_days:
        return (
            f"SCADENZA TRA {days_left} GIORNI ({expiry.isoformat()})\n\n"
            f"{reminder['note']}"
        )
    if days_left < 0:
        return (
            f"SCADUTO DA {abs(days_left)} GIORNI ({expiry.isoformat()})\n\n"
            f"{reminder['note']}"
        )
    return None


def check_once(reminder: dict, today: date, state: dict) -> str | None:
    """Invia una sola volta quando due_date è impostata e non ancora inviato."""
    if not reminder.get("due_date"):
        return None
    if state.get(reminder["id"], {}).get("sent"):
        return None
    due = date.fromisoformat(reminder["due_date"])
    if today >= due:
        return f"SCADENZA RAGGIUNTA ({due.isoformat()})\n\n{reminder['note']}"
    warn_days = reminder.get("warn_days_before", 7)
    days_left = (due - today).days
    if days_left <= warn_days:
        return f"TRA {days_left} GIORNI ({due.isoformat()})\n\n{reminder['note']}"
    return None


def check_recurring(reminder: dict, today: date, state: dict) -> str | None:
    """Invia ogni recurrence_days a partire da start_date."""
    if not reminder.get("start_date"):
        return None
    start = date.fromisoformat(reminder["start_date"])
    if today < start:
        return None
    interval = reminder.get("recurrence_days", 30)
    last_sent_str = state.get(reminder["id"], {}).get("last_sent")
    if last_sent_str:
        last_sent = date.fromisoformat(last_sent_str)
        if (today - last_sent).days < interval:
            return None
    return reminder["note"]


def run() -> None:
    today = date.today()
    reminders = load_reminders()
    state = load_state()
    sent_count = 0

    for r in reminders:
        msg = None
        r_type = r.get("type")

        if r_type == "expiry":
            msg = check_expiry(r, today)
        elif r_type == "once":
            msg = check_once(r, today, state)
        elif r_type == "recurring":
            msg = check_recurring(r, today, state)

        if msg:
            subject = f"[MM Bot] Reminder: {r['label']}"
            body = f"{r['label']}\n{'—' * 40}\n{msg}\n\n— MM Bot Reminders"
            try:
                send_email(r["email"], subject, body)
                if r_type == "once":
                    state.setdefault(r["id"], {})["sent"] = True
                elif r_type == "recurring":
                    state.setdefault(r["id"], {})["last_sent"] = today.isoformat()
                sent_count += 1
            except Exception as e:
                logger.error("Errore invio email per %s: %s", r["id"], e)

    save_state(state)
    logger.info("Run completato — %d reminder inviati su %d totali", sent_count, len(reminders))


if __name__ == "__main__":
    run()
