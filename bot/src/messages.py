"""All user-facing bot strings live here. No hardcoded text in handlers."""

MESSAGES: dict[str, str] = {
    # START / welcome
    "welcome": (
        "Ciao! Sono il bot di M&M Manifatture 🧵\n\n"
        "Con /nuovo pubblichi un prodotto su sito e social in pochi passi.\n\n"
        "Comandi disponibili:\n"
        "/nuovo — inizia una nuova pubblicazione\n"
        "/riprendi — riprendi una pubblicazione in corso\n"
        "/stato — vedi cosa hai inserito finora\n"
        "/annulla — annulla e ricomincia\n"
        "/aiuto — aiuto sul passo corrente"
    ),
    # PHOTO step
    "step_photo_request": (
        "Mandami le foto del prodotto. Quando hai finito premi il bottone."
    ),
    "photo_received": "Foto ricevuta ({count}). Mandane altre o premi \"Ho finito\".",
    "photo_finish_button": "Ho finito con le foto",
    "error_not_a_photo": "Mandami una foto. Oppure /annulla per uscire.",
    "error_no_photos_yet": "Devi mandarmi almeno una foto prima di andare avanti.",
    # PRICE step
    "step_price_request": "Quanto costa? (scrivi solo il numero, es: 25)",
    "error_invalid_price": (
        "Non ho capito il prezzo. Scrivi solo il numero, es: 25 oppure 25,50"
    ),
    "error_description_short": (
        "La descrizione e' molto corta — l'AI avra' meno informazioni per creare le caption.\n"
        "Vuoi aggiungere qualcosa? Oppure premi Salta per procedere lo stesso."
    ),
    "error_description_long": (
        "La descrizione e' troppo lunga (max 800 caratteri).\n"
        "Accorciala un po' e riprova."
    ),
    # SIZE step
    "step_size_request": "Che taglia e'? Scegli dal menu' o scrivi la taglia libera.",
    "skip_button": "Salta",
    # DESCRIPTION step
    "step_description_request": (
        "Descrivi il prodotto: materiale, colori, lavorazione.\n"
        "Es: \"Sciarpa in lana merinos rossa, lavorata a mano\"\n\n"
        "Una buona descrizione migliora le caption AI. Puoi anche saltare."
    ),
    # WHEN step
    "step_when_request": "Quando lo pubblico?",
    "when_now_button": "Adesso",
    "when_slot_button": "Scegli orario",
    "when_auto_button": "Automatico (prossimo slot)",
    # SLOT step
    "step_slot_request": "Scegli quando pubblicare:",
    # CATEGORY step
    "step_category_request": "Che categoria e'?",
    "category_new_button": "Nuova categoria",
    "step_category_new_request": (
        "Scrivi il nome della nuova categoria:"
    ),
    "category_added": "Categoria \"{name}\" aggiunta.",
    # PREVIEW step
    "step_preview": (
        "Riepilogo prodotto\n\n"
        "Foto: {photos_count} foto\n"
        "Prezzo: {price}\n"
        "Taglia: {size}\n"
        "Descrizione: {description}\n"
        "Pubblicazione: {when}\n"
        "Categoria: {category}"
    ),
    "preview_confirm_button": "Conferma",
    "preview_edit_button": "Modifica",
    "preview_cancel_button": "Annulla",
    "edit_menu": "Cosa vuoi modificare?",
    "edit_photo_button": "Foto",
    "edit_price_button": "Prezzo",
    "edit_size_button": "Taglia",
    "edit_description_button": "Descrizione",
    "edit_when_button": "Orario",
    "edit_category_button": "Categoria",
    # AI caption
    "ai_generating": "Genero suggerimento AI...",
    "ai_unavailable_confirm": (
        "⚠️ Suggerimento AI non disponibile. Pubblico con la tua descrizione. Confermi?"
    ),
    "ai_confirm_yes": "Sì, pubblica",
    "ai_confirm_no": "Annulla",
    "step_preview_ai": (
        "Riepilogo prodotto\n\n"
        "Foto: {photos_count} foto\n"
        "Prezzo: {price}\n"
        "Taglia: {size}\n"
        "Pubblicazione: {when}\n"
        "Categoria: {category}\n\n"
        "📝 Tua descrizione:\n{description}\n\n"
        "🤖 Suggerimento AI (sito):\n{ai_site}\n\n"
        "📸 Instagram:\n{ai_instagram}\n\n"
        "👥 Facebook:\n{ai_facebook}"
    ),
    "ai_use_button": "Usa AI",
    "ai_use_mine_button": "Usa il mio testo",
    # Upload progress
    "uploading_photos": "⏳ Carico foto ({done}/{total})...",
    "upload_failed": "Errore nel caricamento delle foto. Riprova o /annulla.",
    # Publish outcome
    "publishing": "⏳ Sto pubblicando...",
    "price_confirm": "Prezzo: {price}. E' corretto?",
    "price_confirm_yes": "Sì, corretto",
    "price_confirm_no": "No, correggo",
    "publish_ok": (
        "Pubblicato! 🎉\n"
        "Prodotto: {category}\n\n"
        "{site_icon} Sito: {site}\n"
        "{ig_icon} Instagram: {instagram}\n"
        "{fb_icon} Facebook: {facebook}"
    ),
    "cmd_lista_empty": "Nessun prodotto pubblicato ancora.",
    "cmd_lista_header": "Ultimi prodotti pubblicati:\n\n",
    "cmd_lista_item": "• {category} — {price} ({when})\n",
    "cmd_resumed": "Riprendi da dove eri:",
    "publish_partial_alert": "⚠️ Pubblicazione parziale per chat {chat_id}: {result}",
    # Commands
    "cmd_already_in_progress": (
        "Hai gia' una pubblicazione in corso. /annulla per ricominciare."
    ),
    "cmd_cancel_confirm": (
        "Sei sicura di voler annullare?\n"
        "Perderai tutto quello che hai inserito finora."
    ),
    "cmd_cancel_yes": "Sì, annulla tutto",
    "cmd_cancel_no": "No, continua",
    "cmd_cancel_no_msg": "Ok, riprendi da dove eri.",
    "cmd_cancelled": "Annullato. Quando vuoi ripartire scrivi /nuovo.",
    "cmd_nothing_to_resume": "Non c'e' nessuna conversazione da riprendere. /nuovo per iniziare.",
    "cmd_state_header": "Stato corrente: {step}\n\nDati inseriti finora:\n{data}",
    "cmd_state_empty": "Nessuna pubblicazione in corso. /nuovo per iniziare.",
    # Help (per step)
    "help_photo": (
        "Mandami una o piu' foto del prodotto.\n"
        "Quando hai finito premi \"Ho finito con le foto\".\n"
        "/annulla per uscire."
    ),
    "help_price": "Scrivi solo il numero del prezzo (es: 25 oppure 25,50).",
    "help_size": "Scegli una taglia dal menu' (XS/S/M/L/XL/XXL/TU) oppure scrivi una taglia personalizzata. \"Salta\" se non applicabile.",
    "help_description": "Scrivi una descrizione oppure premi \"Salta\".",
    "help_when": (
        "Scegli un bottone: Adesso, Scegli orario, oppure Automatico."
    ),
    "help_slot": "Scegli uno degli slot proposti.",
    "help_category": "Scegli una categoria oppure crea una nuova.",
    "help_preview": "Premi Conferma, Modifica o Annulla.",
    "help_idle": (
        "Nessuna pubblicazione in corso.\n\n"
        "Scrivi /nuovo per pubblicare un prodotto, oppure manda direttamente una foto."
    ),
    # Inactivity
    "inactivity_ping": (
        "Sei ancora li'? Riprendi con /riprendi oppure /annulla per ricominciare."
    ),
    # Generic
    "unexpected_input": (
        "Non ho capito. Segui le indicazioni qui sopra. /annulla per uscire."
    ),
    "use_buttons": (
        "Usa i bottoni qui sopra per scegliere. /annulla per uscire."
    ),
    "photo_flow_autostart": (
        "Perfetto, ho ricevuto la foto! Iniziamo la pubblicazione.\n"
        "Puoi mandarne altre se vuoi, poi premi il bottone per andare avanti."
    ),
    "internal_error": "Qualcosa e' andato storto. Riprova o /annulla.",
}


# Step label used by /stato and /aiuto
STEP_LABELS: dict[int, str] = {
    0: "PHOTO",
    1: "PRICE",
    2: "SIZE",
    3: "DESCRIPTION",
    4: "WHEN",
    5: "SLOT",
    6: "CATEGORY",
    7: "PREVIEW",
}


HELP_BY_STEP: dict[int, str] = {
    0: MESSAGES["help_photo"],
    1: MESSAGES["help_price"],
    2: MESSAGES["help_size"],
    3: MESSAGES["help_description"],
    4: MESSAGES["help_when"],
    5: MESSAGES["help_slot"],
    6: MESSAGES["help_category"],
    7: MESSAGES["help_preview"],
}
