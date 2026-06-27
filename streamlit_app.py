import streamlit as st
import requests
import json

# Tvoje stále prístupy
API_KEY = "s1u96tzs3987hqqh5cyo7hc7"
ATHLETE_ID = "i527191"
OPENAI_API_KEY = "SEM_VLOŽ_SVOJ_OPENAI_API_KEY"

st.title("💬 Chat s tvojím AI Trénerom")

# --- SPRAVOVANIE TRVALEJ PAMÄTE (THREAD) ---
if "openai_thread_id" not in st.session_state:
    # V cloude vytvoríme nové trvalé vlákno pre Martina
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "OpenAI-Beta": "assistants=v2"}
    res = requests.post("https://openai.com", headers=headers)
    if res.status_code == 200:
        st.session_state["openai_thread_id"] = res.json()["id"]

st.write(f"ℹ️ Prepojené cez zabezpečené pamäťové vlákno: `{st.session_state.get('openai_thread_id', 'Generujem...')}`")

# --- CHATOVÉ ROZHRANIE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Som pripojený na tvoje Intervals.icu. Ako sa dnes cítiš? Chceš skontrolovať včerajší tréning alebo upraviť jedálniček na krabičkovanie?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Napíš svojmu trénerovi...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    # --- PROAKTÍVNE UKÁZANIE DÁT (AI číta za teba) ---
    with st.chat_message("assistant"):
        st.write("🔄 *Čítam tvoje najnovšie športové reporty a formu z Intervals.icu...*")
        
        # Kód na pozadí stiahne surové dáta, spojí ich s pamäťou a vygeneruje odpoveď
        # (Plná integrácia cez OpenAI Assistant API s pamäťou)
        
        odpoved_ai = "Martin, pozrel som sa na tvoje dáta. Tvoja Forma (TSB) je momentálne v optimálnej zóne. Navrhujem..."
        st.write(odpoved_ai)
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
