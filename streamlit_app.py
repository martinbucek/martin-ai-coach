import streamlit as st
import requests
import json
import datetime
import base64
from google import genai

# 1. INICIALIZÁCIA BEZPLATNEJ GOOGLE AI (ťahá kľúč zo Secrets)
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Tvoje stále prístupové údaje do Intervals a GitHubu
API_KEY = "s1u96tzs3987hqqh5cyo7hc7"
ATHLETE_ID = "i527191"
GITHUB_USER = "martinbucek"
GITHUB_REPO = "martin-ai-coach"

st.title("🤖 Martin's Autogenous AI Coach v3.3")
st.write("### Stabilný športový cloud s automatickým zálohovaním na GitHub")

# --- SYSTÉMOVÝ PROMPT (VEDOMIE BOTA) ---
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """
    Si elitný multišportový tréner, dátový analytik a Python inžinier. Tvoj zverenec je Martin (beh 4x týždenne, rotoped Hop-Sport HS-4500H Creft).
    Máš absolútnu voľnosť. Ak ťa Martin požiada o pokročilú analýzu, graf, výpočet alebo novú funkciu, tvojou úlohou je napísať na to čistý Python kód.
    
    PRAVIDLO PRE KÓD: Ak generuješ Python kód na spustenie, vlož ho do odpovede medzi značky ```python a ```. 
    Tento kód must pracovať s premennou 'aktivity' (zoznam tréningov za 30 dní) a výsledok vypísať pomocou st.write() alebo st.dataframe().
    Odpovedaj vždy priateľsky a čisto po slovensky.
    """

with st.expander("👁️ Pozrieť sa do vedomia bota (Aktuálny Systémový Prompt)"):
    novy_prompt = st.text_area("AI môže tento prompt sama modifikovať podľa tvojich požiadaviek:", value=st.session_state.system_prompt, height=150)
    st.session_state.system_prompt = novy_prompt

# --- CHATOVÁ HISTÓRIA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Som tvoj stabilný autogénny tréner. Limity sú vynulované a zálohy letia do zložky backup/ na našom GitHube!"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- AUTOMATICKÝ MESAČNÝ BACKUP DO GITHUB ZLOŽKY (Vždy 1. dňa v mesiaci) ---
dnesny_datum = datetime.date.today()
je_prvy_den_v_mesiaci = dnesny_datum.day == 1

if je_prvy_den_v_mesiaci:
    st.info("📅 Detekovaný 1. deň v mesiaci. Spúšťam zálohovanie vedomia do GitHub zložky backup/ ...")
    
    backup_data = {
        "datum_zalohy": dnesny_datum.strftime("%Y-%m-%d"),
        "aktualny_prompt": st.session_state.system_prompt,
        "historia_chatu": st.session_state.messages
    }
    backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
    
    file_name = f"backup/ai_coach_backup_{dnesny_datum.strftime('%Y_%m')}.json"
    url_github = f"https://github.com{GITHUB_USER}/{GITHUB_REPO}/contents/{file_name}"
    
    content_base64 = base64.b64encode(backup_json.encode('utf-8')).decode('utf-8')
    
    headers_gh = {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    check_resp = requests.get(url_github, headers=headers_gh)
    
    payload_gh = {
        "message": f"🤖 Automatická mesačná záloha vedomia bota - {dnesny_datum.strftime('%B %Y')}",
        "content": content_base64
    }
    
    if check_resp.status_code == 200:
        payload_gh["sha"] = check_resp.json()["sha"]
        
    res_gh = requests.put(url_github, headers=headers_gh, json=payload_gh)
    
    if res_gh.status_code == 201 or res_gh.status_code == 200:
        st.success(f"💾 Geniálne! Záložný súbor bol úspešne uložený do zložky `backup/` priamo na tvojom GitHube.")
    else:
        st.warning(f"⚠️ Automatická záloha na GitHub zlyhala. Kód odpovede: {res_gh.text}")

# --- SŤAHOVANIE DÁT PRE EXPERIMENTY (30 DNÍ Z INTERVALS.ICU) ---
thirty_days_ago_str = (dnesny_datum - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
today_str = dnesny_datum.strftime("%Y-%m-%d")
aktivity = []

try:
    url_act = f"https://intervals.icu{ATHLETE_ID}/activities"
    act_resp = requests.get(url_act, params={"oldest": thirty_days_ago_str, "newest": today_str}, auth=("API_KEY", API_KEY))
    if act_resp.status_code == 200:
        aktivity = act_resp.json()
except:
    pass

historia_text = ""
for a in aktivity[-10:]:
    historia_text += f"- {a.get('start_date_local')[:10]}: {a.get('type')}, Čas: {round(a.get('moving_time',0)/60,1)} min, Dist: {round(a.get('distance',0)/1000,2)} km, Tep: {a.get('average_heartrate',0)} bpm\n"

# --- CHATOVÝ VSTUP ---
user_input = st.chat_input("Zadaj príkaz alebo požiadaj o novú funkciu...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        full_context = f"{st.session_state.system_prompt}\n\nPOSLEDNÉ TRÉNINGY Z CLOUDU:\n{historia_text}\n\nPríkaz od Martina: {user_input}"
        
        try:
            # Opravené volanie modelu pre novú knižnicu google-genai
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=full_context
            )
            odpoved_ai = response.text
            st.write(odpoved_ai)
            
            if "```python" in odpoved_ai:
                st.write("🛠️ **[Detekovaný autogénny kód]: Spúšťam Python skript, ktorý som si pre teba práve napísal...**")
                try:
                    kod_bloku = odpoved_ai.split("```python")[-1].split("```")[0]
                    local_vars = {"aktivity": aktivity, "st": st, "json": json}
                    exec(kod_bloku, globals(), local_vars)
                    st.success("✅ Autogénny kód prebehol úspešne!")
                except Exception as exec_err:
                    st.error(f"Chyba pri exekúcii kódu: {exec_err}")
                    
        except Exception as ai_err:
            odpoved_ai = f"Chyba pri komunikácii s Google AI: {ai_err}"
            st.write(odpoved_ai)
            
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
