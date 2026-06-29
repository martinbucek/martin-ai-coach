import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google import genai

# ── Konfigurácia ──────────────────────────────────────────────────────────────
ATHLETE_ID = "i527191"
INTERVALS_BASE = "https://intervals.icu"
INTERVALS_API  = f"{INTERVALS_BASE}/api/v1/athlete/{ATHLETE_ID}"

def intervals_auth():
    return ("API_KEY", st.secrets["INTERVALS_API_KEY"])

def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ── Intervals.icu helpery ─────────────────────────────────────────────────────
def fetch_activities(weeks: int = 4) -> pd.DataFrame:
    since = (datetime.utcnow() - timedelta(weeks=weeks)).strftime("%Y-%m-%dT00:00:00")
    url   = f"{INTERVALS_API}/activities"
    r = requests.get(url, auth=intervals_auth(), params={"oldest": since}, timeout=15)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    return df

def fetch_wellness() -> pd.DataFrame:
    since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    url   = f"{INTERVALS_API}/wellness"
    r = requests.get(url, auth=intervals_auth(), params={"oldest": since}, timeout=15)
    r.raise_for_status()
    return pd.DataFrame(r.json())

def fetch_laps(activity_id: str) -> pd.DataFrame:
    url = f"{INTERVALS_BASE}/api/v1/activity/{activity_id}/laps"
    r = requests.get(url, auth=intervals_auth(), timeout=15)
    r.raise_for_status()
    return pd.DataFrame(r.json())

# ── Gemini chat s bezpečným exec() ───────────────────────────────────────────
def extract_python_block(text: str) -> str | None:
    """Vytiahne prvý ```python blok z textu, ak existuje."""
    import re
    pattern = r"```python\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None

def safe_exec(code: str) -> str:
    """Spustí kód cez exec() a vráti stdout alebo chybu – nikdy nezacyklí UI."""
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {"st": st, "pd": pd, "np": np})  # noqa: S102
        return buf.getvalue() or "✅ Kód úspešne vykonaný."
    except Exception as exc:
        return f"❌ Chyba pri exec(): {exc}"

def chat_with_gemini(client, history: list, user_msg: str) -> str:
    history.append({"role": "user", "parts": [{"text": user_msg}]})
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
    )
    reply = response.text
    history.append({"role": "model", "parts": [{"text": reply}]})

    # Bezpečné spustenie python blokov – NIKDY neblokuje UI
    code = extract_python_block(reply)
    if code:
        result = safe_exec(code)
        st.code(code, language="python")
        st.info(result)

    return reply

# ── Streamlit UI ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Martin AI Coach", page_icon="🏃", layout="wide")
st.title("🏃 Martin AI Coach – Dashboard")

# Sidebar – stav systému
with st.sidebar:
    st.header("⚙️ Systém")
    st.write(f"Athlete ID: `{ATHLETE_ID}`")
    if st.button("🔄 Načítať aktivity"):
        st.session_state.pop("activities", None)
        st.session_state.pop("wellness", None)

# Načítanie dát
@st.cache_data(ttl=600, show_spinner="Načítavam tréningové dáta…")
def load_data():
    acts     = fetch_activities(weeks=4)
    wellness = fetch_wellness()
    return acts, wellness

try:
    activities, wellness = load_data()
    st.sidebar.success("✅ Intervals.icu: OK")
except requests.HTTPError as e:
    st.sidebar.error(f"❌ HTTP chyba: {e.response.status_code}")
    activities, wellness = pd.DataFrame(), pd.DataFrame()
except Exception as e:
    st.sidebar.error(f"❌ {e}")
    activities, wellness = pd.DataFrame(), pd.DataFrame()

# Prehľad aktivít
tab1, tab2, tab3 = st.tabs(["📊 Aktivity", "💬 AI Coach", "📈 Wellness"])

with tab1:
    st.subheader("Posledné 4 týždne")
    if not activities.empty:
        cols = [c for c in ["start_date_local","name","type","distance","moving_time",
                             "average_heartrate","training_load","icu_atl","icu_ctl","icu_tsb"]
                if c in activities.columns]
        st.dataframe(activities[cols], use_container_width=True)
        # Rýchle štatistiky
        if "distance" in activities.columns:
            total_km = activities["distance"].sum() / 1000
            st.metric("Celková vzdialenosť", f"{total_km:.1f} km")
    else:
        st.info("Žiadne aktivity – skontroluj API kľúč.")

with tab2:
    st.subheader("Chat s AI Coachem")
    client = get_gemini_client()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "gemini_history" not in st.session_state:
        st.session_state.gemini_history = []

    # Zobraz históriu
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Napíš správu pre AI Coacha…")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Premýšľam…"):
                # Pridáme kontext aktivít do prvej správy
                context = ""
                if not activities.empty:
                    context = f"\n\nTréningový kontext (posledné 4 týždne):\n{activities.head(20).to_json(orient='records', force_ascii=False)}"
                full_msg = user_input + context if not st.session_state.gemini_history else user_input

                reply = chat_with_gemini(client, st.session_state.gemini_history, full_msg)
            st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

with tab3:
    st.subheader("Wellness & TSB")
    if not wellness.empty:
        st.dataframe(wellness, use_container_width=True)
        if "tsb" in wellness.columns:
            st.line_chart(wellness.set_index("id")["tsb"] if "id" in wellness.columns else wellness["tsb"])
    else:
        st.info("Wellness dáta nie sú dostupné.")
