# Versione 1.16 – Profilazione utente + valutazione per sotto-soft skill

import streamlit as st
import openai

st.set_page_config(page_title="Certificazione Team Work v.1.16", layout="centered")

# Inizializzazione variabili di sessione
if "fase" not in st.session_state:
    st.session_state.fase = "profilo"
    st.session_state.profilo = {}
    st.session_state.sottoskills = {
        "Comunicazione": "Comunicazione",
        "Ascolto attivo": "Empatia",
        "Rispettare le opinioni altrui": "Empatia",
        "Gestione dei conflitti": "Problem solving",
        "Collaborazione proattiva": "Collaborazione",
        "Creatività": "Problem solving",
        "Responsabilità": "Leadership",
        "Fiducia": "Collaborazione",
        "Compromesso": "Comunicazione",
        "Leadership": "Leadership"
    }
    st.session_state.scelta = None
    st.session_state.domande = []
    st.session_state.risposte = []
    st.session_state.punteggi = []
    st.session_state.indice = 0

# Funzione generazione domanda

def genera_domanda_per_sottoskills(nome_sottoskills, profilo):
    prompt = f"""Sei un esperto di soft skill. Genera una domanda situazionale per valutare la sotto-soft skill "{nome_sottoskills}" all'interno della competenza Team Work. Considera questo profilo:
{profilo}
La domanda deve essere in tre parti:
1. Scenario realistico
2. Problema specifico
3. Domanda aperta mirata
Scrivi ogni parte su una nuova riga."""
    res = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Valutazione con pesi personalizzati

def valuta_risposta(risposta, primaria):
    if not risposta.strip():
        return {k: 0 for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]}
    prompt = f"""Valuta questa risposta:
"{risposta}"

Assegna un punteggio da 0 a 100 a ciascuna dimensione:
- Collaborazione
- Comunicazione
- Leadership
- Problem solving
- Empatia

Specifica in modo oggettivo per ogni punteggio cosa motiva la valutazione."""
    res = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    valutazione = {k: 0 for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]}
    for line in res.choices[0].message.content.strip().splitlines():
        for k in valutazione:
            if line.startswith(k):
                try:
                    valutazione[k] = int("".join(filter(str.isdigit, line)))
                except:
                    pass
    valutazione[primaria] = round(valutazione[primaria] * 1.5)
    return valutazione

# Descrizione finale

def descrizione_finale(nome, sotto, media):
    prompt = f"""Scrivi una valutazione del candidato {nome} sulla sotto-soft skill "{sotto}" del Team Work, basandoti su questi punteggi:
{media}
Specifica:
- Punti di forza
- Aree di miglioramento
- 3 corsi formativi (solo titolo)
La descrizione deve essere chiara, oggettiva, motivata, in 10-15 righe."""
    res = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# FASE 0 – Profilazione
if st.session_state.fase == "profilo":
    st.title("Certificazione Team Work (v. 1.16)")
    st.subheader("Compila il tuo profilo per iniziare")
    nome = st.text_input("Nome e cognome")
    eta = st.number_input("Età", min_value=16, max_value=100, step=1)
    azienda = st.text_input("Azienda (facoltativa)")
    ruolo = st.text_input("Ruolo attuale o più recente")
    settore = st.text_input("Settore professionale o di studio")
    anni_settore = st.slider("Anni di esperienza nel settore", 0, 40, 0)
    anni_ruolo = st.slider("Anni di esperienza nel ruolo", 0, 40, 0)
    if st.button("Avanti") and nome and eta and settore:
        st.session_state.profilo = {
            "nome": nome,
            "eta": eta,
            "azienda": azienda,
            "ruolo": ruolo,
            "settore": settore,
            "anni_settore": anni_settore,
            "anni_ruolo": anni_ruolo
        }
        st.session_state.fase = "scelta"
        st.rerun()

# FASE 1 – Selezione modulo sotto-skill
elif st.session_state.fase == "scelta":
    st.title("Seleziona la sotto-soft skill da valutare")
    scelta = st.selectbox("Sotto-soft skill:", list(st.session_state.sottoskills.keys()))
    if st.button("Avvia il test"):
        st.session_state.scelta = scelta
        st.session_state.fase = "test"
        st.session_state.domande = [genera_domanda_per_sottoskills(scelta, st.session_state.profilo)]
        st.rerun()

# FASE 2 – Test
elif st.session_state.fase == "test":
    nome_sotto = st.session_state.scelta
    indice = st.session_state.indice
    st.title(f"Modulo: {nome_sotto} – Domanda {indice + 1} di 20")

    for riga in st.session_state.domande[indice].splitlines():
        st.markdown(riga)

    risposta = st.text_area("La tua risposta", key=f"risposta_{indice}")
    if st.button("Invia risposta"):
        primaria = st.session_state.sottoskills[nome_sotto]
        valutazione = valuta_risposta(risposta, primaria)
        st.session_state.risposte.append(risposta)
        st.session_state.punteggi.append(valutazione)

        st.session_state.indice += 1
        if st.session_state.indice < 20:
            nuova = genera_domanda_per_sottoskills(nome_sotto, st.session_state.profilo)
            st.session_state.domande.append(nuova)
        else:
            st.session_state.fase = "fine"
        st.rerun()

# FASE 3 – Report finale
elif st.session_state.fase == "fine":
    st.title("📊 Risultato modulo Team Work")
    sotto = st.session_state.scelta
    nome = st.session_state.profilo.get("nome", "Utente")

    dimensioni = ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]
    media = {k: round(sum(p[k] for p in st.session_state.punteggi) / len(st.session_state.punteggi), 2) for k in dimensioni}
    totale = round(sum(media.values()) / len(media), 2)

    st.markdown(f"### Sotto-soft skill: **{sotto}**")
    for k, v in media.items():
        st.markdown(f"**{k}:** {v}/100")

    st.markdown("### ✅ Valutazione finale")
    if totale >= 70:
        st.success("Certificazione ottenuta ✅")
    else:
        st.warning("Certificazione non ottenuta ❌")

    st.markdown("### 🧾 Report dettagliato")
    report = descrizione_finale(nome, sotto, media)
    for r in report.split("\n"):
        st.markdown(r)

    if st.button("🔁 Torna alla selezione"):
        st.session_state.clear()
        st.rerun()
