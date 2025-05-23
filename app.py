# Versione 1.14 – Sistema Antifragile con contesto cumulativo

import streamlit as st
import openai

st.set_page_config(page_title="Certificazione Team Work v.1.14", layout="centered")

# Inizializzazione variabili di sessione
if "step" not in st.session_state:
    st.session_state.step = "profilo"
    st.session_state.profilo_utente = {}
    st.session_state.domande = []
    st.session_state.risposte = []
    st.session_state.sintesi = []
    st.session_state.punteggi = []
    st.session_state.indice = 0

# Funzioni di generazione e valutazione

def sintetizza_profilo(parziale):
    contesto = "\n".join([f"D: {d}\nR: {r}" for d, r in parziale])
    prompt = f"""Sulla base delle seguenti interazioni:
{contesto}

Fornisci una breve sintesi dei comportamenti osservati in relazione alla soft skill Team Work. Concentrati su aree forti, incerte e deboli."""
    res = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

def genera_domanda(profilo, storico, sintesi):
    contesto = "\n".join([f"D: {d}\nR: {r}" for d, r in storico])
    sommario = "\n".join(sintesi)
    prompt = f"""Profilo: {profilo}

Interazioni precedenti:
{contesto}

Sintesi intermedia:
{sommario}

Genera una nuova domanda situazionale per valutare la capacità di lavorare in team, focalizzandoti su incongruenze o aree poco esplorate. Struttura in:
- Scenario
- Problema
- Domanda

Se possibile, rendi ogni parte distinta con una nuova riga."""
    risposta = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return risposta.choices[0].message.content.strip()

def valuta_risposta(risposta):
    if not risposta.strip():
        return {k: 0 for k in ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]}
    prompt = f"""Valuta questa risposta:
"{risposta}"

Assegna un punteggio da 0 a 100 a ciascuna dimensione:
- Collaborazione
- Comunicazione
- Leadership
- Problem solving
- Empatia"""
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
    return valutazione

def descrizione_finale(storico, punteggio):
    contesto = "\n".join([f"D: {d}\nR: {r}" for d, r in storico])
    prompt = f"""Sulla base delle seguenti risposte:
{contesto}

E dei punteggi ottenuti:
{punteggio}

Scrivi una descrizione finale del profilo, motivando ogni valutazione, evidenziando le risposte critiche o eccellenti. Suggerisci 3 corsi di formazione pertinenti (solo nomi)."""
    res = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Interfaccia Profilo Utente
if st.session_state.step == "profilo":
    st.title("Certificazione Team Work – Sistema Adattivo e Coerente (v. 1.14)")
    st.subheader("Compila il tuo profilo per iniziare")

    nome = st.text_input("Nome e cognome")
    eta = st.number_input("Età", min_value=16, max_value=99, step=1)
    azienda = st.text_input("Azienda attuale o più recente (può essere vuoto se studente)")
    settore = st.text_input("Settore di attività")
    ruolo = st.text_input("Ruolo attuale o più recente (può essere vuoto se studente)")
    anni_settore = st.slider("Anni di esperienza nel settore", 0, 40, 0)
    anni_ruolo = st.slider("Anni di esperienza nel ruolo", 0, 40, 0)

    if st.button("Inizia il test"):
        if all([nome, eta, settore]):
            st.session_state.profilo_utente = {
                "nome": nome, "eta": eta, "azienda": azienda,
                "settore": settore, "ruolo": ruolo,
                "anni_settore": anni_settore, "anni_ruolo": anni_ruolo
            }
            profilo_str = str(st.session_state.profilo_utente)
            prima = genera_domanda(profilo_str, [], [])
            st.session_state.domande.append(prima)
            st.session_state.step = "test"
            st.rerun()
        else:
            st.error("Compila almeno i campi obbligatori: nome, età, settore.")

# Test a 30 domande con sintesi ogni 5
elif st.session_state.step == "test":
    st.title("Domande dinamiche di Team Work")
    i = st.session_state.indice

    st.markdown(f"**Domanda {i + 1} di 30**")
    for riga in st.session_state.domande[i].splitlines():
        st.markdown(riga)

    risposta = st.text_area("La tua risposta", key=f"risposta_{i}")
    if st.button("Invia risposta"):
        st.session_state.risposte.append(risposta)
        valutazione = valuta_risposta(risposta)
        st.session_state.punteggi.append(valutazione)

        if (i+1) % 5 == 0:
            parziale = list(zip(st.session_state.domande, st.session_state.risposte))[-5:]
            st.session_state.sintesi.append(sintetizza_profilo(parziale))

        st.session_state.indice += 1
        if st.session_state.indice < 30:
            profilo_str = str(st.session_state.profilo_utente)
            nuova = genera_domanda(
                profilo_str,
                list(zip(st.session_state.domande, st.session_state.risposte)),
                st.session_state.sintesi
            )
            st.session_state.domande.append(nuova)
        else:
            st.session_state.step = "risultato"

        st.rerun()

# Risultato finale
elif st.session_state.step == "risultato":
    st.title("✅ Profilazione completata")

    dimensioni = ["Collaborazione", "Comunicazione", "Leadership", "Problem solving", "Empatia"]
    media = {k: round(sum(p[k] for p in st.session_state.punteggi) / len(st.session_state.punteggi), 2) for k in dimensioni}
    totale = round(sum(media.values()) / len(media), 2)

    st.markdown("### Profilo finale:")
    for k in media:
        st.markdown(f"**{k}:** {media[k]}/100")

    st.markdown("### 🧭 Esito certificazione")
    if totale >= 70:
        st.success("🎖 Complimenti! Hai ottenuto la certificazione Team Work")
    else:
        st.warning("Continua ad allenarti per ottenere la certificazione.")

    st.markdown("### 📃 Descrizione dettagliata del profilo")
    descrizione = descrizione_finale(list(zip(st.session_state.domande, st.session_state.risposte)), media)
    for r in descrizione.split("\n"):
        st.markdown(r)

    if st.button("🔄 Ricomincia il test"):
        st.session_state.clear()
        st.rerun()
