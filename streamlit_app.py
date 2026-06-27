import streamlit as st
import requests
import json
import datetime
from google import genai

# Inicializácia BEZPLATNEJ Google AI
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

API_KEY = "s1u96tzs3987hqqh5cyo7hc7"
ATHLETE_ID = "i527191"

st.title("🏃‍♂️ Martin's AI Coach v2.1")

# --- 🚀 NOVÁ SEKCOA: PRIAME NAHRÁVANIE TRÉNINGOV DO INTERVALS.ICU ---
st.write("### 📥 Nahraj nový tréning (.TCX / .GPX) priamo do cloudu")
uploaded_file = st.file_uploader("Vyber stiahnutý súbor z Kinomapu:", type=["tcx", "gpx", "fit"])

if uploaded_file is not None:
    if st.button("🚀 Odoslať tréning do Intervals.icu"):
        with st.spinner("Posielam súbor do tvojho športového kalendára..."):
            # Príprava payloadu pre oficiálne Intervals.icu API
            url_upload = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/activities"
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/octet-stream')}
            
            # Bezpečná základná autentifikácia (Basic Auth) pod tvojím kľúčom
            response_upload = requests.post(url_upload, auth=("API_KEY", API_KEY), files=files)
            
            if response_upload.status_code in [200, 201]:
                st.success(f"✅ Úspech! Tréning '{uploaded_file.name}' bol bezpečne nahraný do Intervals.icu. Systém ho okamžite spracoval.")
            else:
                st.error(f"❌ Chyba pri nahrávaní: {response_upload.text}")

st.write("---")

# --- 💬 CHATOVÉ ROZHRANIE SO VŠETKÝMI FUNKCIAMI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Som tvoj bezplatný tréner prepojený na Intervals.icu. Ako sa dnes cítiš? Napíš mi a hneď ti zhodnotím tréning a pripravím jedálniček!"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# SŤAHOVANIE DÁT Z INTERVALS.ICU PRE AI MOZOG
today_str = datetime.date.today().strftime("%Y-%m-%d")
day_after_tomorrow_str = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

ctl, atl, tsb = 0, 0, 0
try:
    url_stats = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/wellness?oldest={today_str}&newest={today_str}"
    stats_resp = requests.get(url_stats, auth=("API_KEY", API_KEY))
    if stats_resp.status_code == 200 and stats_resp.json():
        w = stats_resp.json()[-1]
        ctl, atl, tsb = w.get("ctl", 0), w.get("atl", 0), w.get("tsb", 0)
except:
    pass

dnesny_trenig = "Žiadna aktivita."
try:
    url_act = f"https://intervals.icu/api/v1/athlete/{ATHLETE_ID}/activities"
    act_resp = requests.get(url_act, params={"oldest": today_str, "newest": today_str}, auth=("API_KEY", API_KEY))
    if act_resp.status_code == 200 and act_resp.json():
        a = act_resp.json()[-1]
        dnesny_trenig = f"Typ: {a.get('type')}, Čas: {round(a.get('moving_time', 0)/60, 1)} min, Vzdialenosť: {round(a.get('distance', 0)/1000, 2)} km, Tep: {a.get('average_heartrate', 0)} bpm, Load: {a.get('icu_training_load', 0)}."
except:
    pass

user_input = st.chat_input("Napíš svojmu trénerovi...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        st.write("🔄 *Čítam tvoje najnovšie športové reporty a formu z Intervals.icu...*")
        
        system_context = f"""
        Si elitný multišportový tréner a nutričný poradca pre bežcov. Tvoj zverenec sa volá Martin.
        Martin behá 4x týždenne (Long Runy nad 10 km) a vracia sa do formy po chorobe. Neznáša rigidné príkazy.
        Doma cvičí na rotopede Hop-Sport HS-4500H Creft cez iPad (Zwift/Kinomap).
        
        AKTUÁLNE REÁLNE METRIKY Z CLOUDU DNEŠNÉHO DŇA:
        - Dlhodobá kondícia (CTL): {ctl}
        - Akútna únava (ATL): {atl}
        - Športová Forma (TSB): {tsb}
        - DNEŠNÝ ODMAKANÝ TRÉNING: {dnesny_trenig}
        - DÁTUM NA JEDÁLNIČEK (Pozajtra): {day_after_tomorrow_str}
        
        Odpovedaj Martinovi na jeho otázku priateľsky, povzbudivo, čisto po slovensky. 
        Ak ťa žiada o analýzu, zhodnoť tie surové dáta z bicykla/behu a tsb. 
        Ak ťa žiada o jedálniček obdeň, zostav mu gramážami podložený plán na krabičkovanie sacharidov/bielkovín na dátum {day_after_tomorrow_str}.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_context}\n\nOtázka od Martina: {user_input}"
            )
            odpoved_ai = response.text
        except Exception as ai_err:
            odpoved_ai = f"Chyba pri komunikácii s Google AI: {ai_err}"
            
        st.write(odpoved_ai)
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
