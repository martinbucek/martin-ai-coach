import streamlit as st
import requests
import json
import datetime
from openai import OpenAI

# Inicializácia OpenAI klienta
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

API_KEY = "s1u96tzs3987hqqh5cyo7hc7"
ATHLETE_ID = "i527191"

st.title("🏃‍♂️ Martin's AI Coach v1.0")

# 1. ZABEZPEČENIE PAMÄŤOVÉHO VLÁKNA (THREAD)
if "openai_thread_id" not in st.session_state:
    try:
        thread = client.beta.threads.create()
        st.session_state["openai_thread_id"] = thread.id
    except Exception as e:
        st.error(f"Chyba pri vytváraní AI vlákna: {e}")

if "openai_thread_id" in st.session_state:
    st.write(f"ℹ️ Prepojené cez zabezpečené pamäťové vlákno: `{st.session_state['openai_thread_id']}`")

# 2. HISTÓRIA CHATU NA OBRAZOVKE
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Som pripojený na tvoje Intervals.icu. Ako sa dnes cítiš? Chceš skontrolovať včerajší tréning alebo upraviť jedálniček na krabičkovanie?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. REÁLNE SŤAHOVANIE DÁT Z CLOUDU PRE AI
today_str = datetime.date.today().strftime("%Y-%m-%d")
tomorrow_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
day_after_tomorrow_str = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

# Sťahujeme Formu (TSB)
ctl, atl, tsb = 0, 0, 0
try:
    url_stats = f"https://intervals.icu{ATHLETE_ID}/wellness?oldest={today_str}&newest={today_str}"
    stats_resp = requests.get(url_stats, auth=("API_KEY", API_KEY))
    if stats_resp.status_code == 200 and stats_resp.json():
        w = stats_resp.json()[-1]
        ctl, atl, tsb = w.get("ctl", 0), w.get("atl", 0), w.get("tsb", 0)
except:
    pass

# Sťahujeme dnešnú aktivitu (Kinomap z rotopedu)
dnesny_trenig = "Žiadna aktivita."
try:
    url_act = f"https://intervals.icu{ATHLETE_ID}/activities"
    act_resp = requests.get(url_act, params={"oldest": today_str, "newest": today_str}, auth=("API_KEY", API_KEY))
    if act_resp.status_code == 200 and act_resp.json():
        a = act_resp.json()[-1]
        dnesny_trenig = f"Typ: {a.get('type')}, Čas: {round(a.get('moving_time', 0)/60, 1)} min, Vzdialenosť: {round(a.get('distance', 0)/1000, 2)} km, Tep: {a.get('average_heartrate', 0)} bpm, Load: {a.get('icu_training_load', 0)}."
except:
    pass

# 4. CHATOVÝ VSTUP OD MARTINA
user_input = st.chat_input("Napíš svojmu trénerovi...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        st.write("🔄 *Čítam tvoje najnovšie športové reporty a formu z Intervals.icu...*")
        
        # Komplexný systémový kontext, ktorý AI podstrčíme na pozadí, aby si všetko pamätala
        system_context = f"""
        Si elitný multišportový tréner a nutričný poradca pre bežcov. Tvoj zverenec sa volá Martin.
        Martin behá 4x týždenne (Long Runy nad 10 km) a vracia sa do formy po chorobe. Neznáša rigidné príkazy.
        Doma cvičí na rotopede Hop-Sport HS-4500H Creft cez iPad (Zwift/Kinomap).
        
        AKTUÁLNE REÁLNE METRIKY Z CLOUDU DNEŠNÉHO DŇA:
        - Dlhodobá kondícia (CTL): {ctl}
        - Akútna únava (ATL): {atl}
        - Športová Forma (TSB): {tsb} (Ak je pod -30, Martin je pretrénovaný).
        - DNEŠNÝ ODMAKANÝ TRÉNING: {dnesny_trenig}
        - DÁTUM NA JEDÁLNIČEK (Pozajtra): {day_after_tomorrow_str}
        
        Odpovedaj Martinovi na jeho otázku priateľsky, povzbudivo, čisto po slovensky. 
        Ak ťa žiada o analýzu, zhodnoť tie surové dáta z bicykla/behu a tsb. 
        Ak ťa žiada o jedálniček obdeň, zostav mu gramážami podložený plán na krabičkovanie sacharidov/bielkovín na dátum {day_after_tomorrow_str}.
        """
        
        try:
            # Volanie skutočného ChatGPT modelu cez oficiálne API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7
            )
            odpoved_ai = response.choices[0].message.content
        except Exception as ai_err:
            odpoved_ai = f"Chyba pri komunikácii s AI: {ai_err}. Skontroluj, či máš na OpenAI nabitý ten 5$ kredit."
            
        st.write(odpoved_ai)
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
