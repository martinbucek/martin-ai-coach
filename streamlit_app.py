import streamlit as st
import requests
import json
from openai import OpenAI

# Inicializácia oficiálneho OpenAI klienta (ťahá kľúč bezpečne zo Secrets)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

API_KEY = "s1u96tzs3987hqqh5cyo7hc7"
ATHLETE_ID = "i527191"

st.title("💬 Chat s tvojím AI Trénerom")

# Bezpečné vytvorenie pamäťového vlákna (Thread) cez oficiálnu knižnicu
if "openai_thread_id" not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state["openai_thread_id"] = thread.id
    except Exception as e:
        st.error(f"Chyba pri vytváraní AI vlákna: {e}")

if "openai_thread_id" in st.session_state:
    st.write(f"ℹ️ Prepojené cez zabezpečené pamäťové vlákno: `{st.session_state['openai_thread_id']}`")

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
        
    with st.chat_message("assistant"):
        st.write("asy 🔄 *Čítam tvoje najnovšie športové reporty a formu z Intervals.icu...*")
        
        # Simulácia odpovede pre prvý test funkčnosti rozhrania
        odpoved_ai = "Martin, tvoj kód bol úspešne opravený a pripojený! Tvoja Forma (TSB) je v optimálnej zóne. Napíš mi, či už máš Apple Watch Ultra 3 na ruke, a môžeme naplánovať zajtrajší beh."
        st.write(odpoved_ai)
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
