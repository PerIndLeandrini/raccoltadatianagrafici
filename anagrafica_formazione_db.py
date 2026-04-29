import streamlit as st
import requests
from datetime import datetime, date
import re

st.set_page_config(
    page_title="Anagrafiche Formazione",
    page_icon="👤",
    layout="centered"
)

# ---------------------- Utility ----------------------
def pulisci_testo(x: str) -> str:
    return " ".join((x or "").strip().split())


def valida_cf(cf: str) -> bool:
    cf = pulisci_testo(cf).upper()
    return bool(re.fullmatch(r"[A-Z0-9]{16}", cf))


def valida_email(email: str) -> bool:
    email = pulisci_testo(email).lower()
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def valida_piva(piva: str) -> bool:
    piva = pulisci_testo(piva)
    return (piva == "") or bool(re.fullmatch(r"\d{11}", piva))


def api_post_anagrafica(payload: dict) -> dict:
    """Invia il payload all'API PHP sul dominio 4step."""
    base_url = st.secrets["api_anagrafiche"]["base_url"].rstrip("/")
    token = st.secrets["api_anagrafiche"]["token"]
    url = f"{base_url}/save_anagrafica.php"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-API-KEY": token,
        "User-Agent": "Mozilla/5.0 4step-anagrafiche-streamlit",
        "Accept": "application/json",
    }

    r = requests.post(url, json=payload, headers=headers, timeout=25)

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Risposta non JSON dall'API. HTTP {r.status_code}: {r.text[:500]}")

    if r.status_code >= 400 or not data.get("ok"):
        raise RuntimeError(data.get("error") or f"Errore API HTTP {r.status_code}")

    return data


# ---------------------- UI ----------------------
st.title("👤 Raccolta dati anagrfici")
st.write(
    "Modulo per raccogliere i dati anagrafici dei lavoratori e dell’azienda di appartenenza. "
    "I dati saranno usati per schede personali, registri formazione e futuri attestati."
)

with st.sidebar:
    st.header("ℹ️ Uso del modulo")
    st.markdown(
        """
- Compila il form qui accanto in tutte le sue parti
- Nella seziine aziendale puoi indicare solamente il nome del punto vendita 
- L’invio registra i dati nel database centralizzato.
"""
    )

st.subheader("👤 Dati anagrafici")

c1, c2 = st.columns(2)
with c1:
    nome = st.text_input("Nome *", max_chars=60)
    data_nascita = st.date_input("Data di nascita *", value=date(1990, 1, 1), format="DD/MM/YYYY")
    codice_fiscale = st.text_input("Codice fiscale *", max_chars=16).upper()
    email = st.text_input("Email *", max_chars=120, placeholder="nome@dominio.it")

with c2:
    cognome = st.text_input("Cognome *", max_chars=60)
    luogo_nascita = st.text_input("Luogo di nascita *", max_chars=80)
    telefono = st.text_input("Telefono", max_chars=30)
    mansione = st.text_input("Mansione / Ruolo", max_chars=100, placeholder="es. Addetto vendite, Magazziniere, Impiegato")

st.markdown("---")
st.subheader("🏢 Punto vendita")

c3, c4 = st.columns(2)
with c3:
    ragione_sociale = st.text_input("Azienda/punto vendita *", max_chars=150)
    partita_iva = st.text_input("Partita IVA", max_chars=11)
    codice_fiscale_azienda = st.text_input("Codice fiscale azienda", max_chars=16).upper()
    referente_azienda = st.text_input("Referente aziendale", max_chars=100)

with c4:
    sede_legale = st.text_input("Indirizzo sede / unità locale", max_chars=180)
    cap = st.text_input("CAP", max_chars=10)
    comune_azienda = st.text_input("Comune azienda", max_chars=80)
    provincia_azienda = st.text_input("Provincia", max_chars=2).upper()

email_referente = st.text_input("Email referente aziendale", max_chars=120, placeholder="referente@azienda.it")

st.markdown("---")
st.subheader("🔐 Informativa sintetica & consenso")
st.markdown(
    """
**Finalità**: gestione anagrafica, predisposizione schede personali, registri e futuri attestati.  
**Base giuridica**: adempimenti connessi alla formazione e agli obblighi documentali applicabili.  
**Conservazione**: per il tempo necessario a dimostrare la formazione svolta e secondo le regole documentali applicabili.  
**Diritti**: accesso, rettifica, limitazione, cancellazione ove applicabile.
"""
)
consenso = st.checkbox("✅ Dichiaro di aver letto l’informativa e autorizzo il trattamento dei dati per le finalità indicate.")

st.markdown("---")

if st.button("💾 Salva anagrafica", type="primary"):
    missing = []

    if not pulisci_testo(nome):
        missing.append("Nome")
    if not pulisci_testo(cognome):
        missing.append("Cognome")
    if not pulisci_testo(luogo_nascita):
        missing.append("Luogo di nascita")
    if not valida_cf(codice_fiscale):
        missing.append("Codice fiscale valido")
    if not valida_email(email):
        missing.append("Email partecipante valida")
    if not pulisci_testo(ragione_sociale):
        missing.append("Ragione sociale azienda")
    if not valida_piva(partita_iva):
        missing.append("Partita IVA valida, se inserita")
    if email_referente and not valida_email(email_referente):
        missing.append("Email referente valida, se inserita")

    if missing:
        st.error("⚠️ Compila correttamente: " + ", ".join(missing))
    elif not consenso:
        st.error("⚠️ Devi accettare l’informativa privacy per procedere.")
    else:
        payload = {
            "timestamp_invio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nome": pulisci_testo(nome).title(),
            "cognome": pulisci_testo(cognome).title(),
            "data_nascita": data_nascita.strftime("%Y-%m-%d"),
            "luogo_nascita": pulisci_testo(luogo_nascita).title(),
            "codice_fiscale": pulisci_testo(codice_fiscale).upper(),
            "email": pulisci_testo(email).lower(),
            "telefono": pulisci_testo(telefono),
            "mansione": pulisci_testo(mansione),
            "ragione_sociale": pulisci_testo(ragione_sociale),
            "partita_iva": pulisci_testo(partita_iva),
            "codice_fiscale_azienda": pulisci_testo(codice_fiscale_azienda).upper(),
            "sede_legale": pulisci_testo(sede_legale),
            "cap": pulisci_testo(cap),
            "comune_azienda": pulisci_testo(comune_azienda).title(),
            "provincia_azienda": pulisci_testo(provincia_azienda).upper(),
            "referente_azienda": pulisci_testo(referente_azienda),
            "email_referente": pulisci_testo(email_referente).lower(),
            "consenso_privacy": "SI",
            "sorgente_app": "streamlit_anagrafiche_formazione",
        }

        try:
            with st.spinner("Salvataggio in corso sul database 4step..."):
                result = api_post_anagrafica(payload)

            record_id = result.get("id") or result.get("record_id") or ""
            if record_id:
                st.success(f"✅ Anagrafica salvata correttamente. ID record: {record_id}")
            else:
                st.success("✅ Anagrafica salvata correttamente nel database.")

            st.info("Il dato è ora disponibile per schede personali, registri formazione e futuri attestati.")

        except Exception as e:
            st.error(f"❌ Errore durante il salvataggio: {e}")
            st.caption("Verifica URL API, token nei secrets e configurazione PHP/MySQL sul dominio.")

st.caption("* Campi obbligatori. I dati sono inviati tramite API protetta da token verso il database del dominio 4step.")
