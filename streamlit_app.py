import streamlit as st
import requests
import json
import datetime
import base64

# Tvoje stále prístupové údaje do Intervals a GitHubu
API_KEY = "s1u96tzs3987hqqh5cyo7hc7"
ATHLETE_ID = "i527191"
GITHUB_USER = "martinbucek"
GITHUB_REPO = "martin-ai-coach"

st.title("🤖 Martin's Autogenous AI Coach v3.9.1")
st.write("### ⚡ Bezpečný športový cloud s priamym API")

# --- SYSTÉMOVÝ PROMPT (VEDOMIE BOTA) ---
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """
    Si elitný multišportový tréner, dátový analytik and Python inžinier. Tvoj zverenec je Martin (beh 4x týždenne, rotoped Hop-Sport HS-4500H Creft).
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
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Som tvoj optimalizovaný tréner. Celých 30 dní aj s detailnými lapmi pre intervaly načítavam jedným dychom!"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- AUTOMATICKÝ MESAČNÝ BACKUP DO GITHUB ZLOŽKY (Vždy 1. dňa v mesiaci) ---
dnesny_datum = datetime.date.today()
je_prvy_den_v_mesiaci = dnesny_datum.day == 1

if je_prvy_den_v_mesiaci:
    try:
        backup_data = {"datum_zalohy": dnesny_datum.strftime("%Y-%m-%d"), "aktualny_prompt": st.session_state.system_prompt, "historia_chatu": st.session_state.messages}
        backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
        file_name = f"backup/ai_coach_backup_{dnesny_datum.strftime('%Y_%m')}.json"
        url_github = f"https://github.com{GITHUB_USER}/{GITHUB_REPO}/contents/{file_name}"
        content_base64 = base64.b64encode(backup_json.encode('utf-8')).decode('utf-8')
        headers_gh = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}", "Accept": "application/vnd.github.v3+json"}
        check_resp = requests.get(url_github, headers=headers_gh)
        payload_gh = {"message": f"🤖 Automatická mesačná záloha", "content": content_base64}
        if check_resp.status_code == 200:
            payload_gh["sha"] = check_resp.json()["sha"]
        requests.put(url_github, headers=headers_gh, json=payload_gh)
    except:
        pass

# --- SŤAHOVANIE DÁT: 30 DNÍ + LAPY V JEDNOM SEGUNDOVOM DOPYTE ---
thirty_days_ago_str = (dnesny_datum - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
today_str = dnesny_datum.strftime("%Y-%m-%d")
aktivity = []

try:
    url_act = f"https://intervals.icu{ATHLETE_ID}/activities?include=laps"
    act_resp = requests.get(url_act, params={"oldest": thirty_days_ago_str, "newest": today_str}, auth=("API_KEY", API_KEY))
    if act_resp.status_code == 200:
        aktivity = act_resp.json()
except:
    pass

# Spracovanie dát pre AI
historia_text = ""
lapy_text = "\n📋 DETAILNÉ KOLO/LAPY PRE POSLEDNÉ TRÉNINGY:\n"

for a in aktivity[-10:]:
    dt_obj = datetime.datetime.strptime(a.get("start_date_local")[:10], "%Y-%m-%d")
    sk_dni = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
    den_v_tyzdni = sk_dni.get(dt_obj.weekday(), "Neznámy")
    
    historia_text += f"- Dátum: {a.get('start_date_local')[:10]} ({den_v_tyzdni}), Typ: {a.get('type')}, Čas: {round(a.get('moving_time',0)/60,1)} min, Dist: {round(a.get('distance',0)/1000,2)} km, Tep: {a.get('average_heartrate',0)} bpm, Load: {a.get('icu_training_load',0)}\n"
    
    if a.get("laps"):
        lapy_text += f"\nTréning dňa {a.get('start_date_local')[:10]} ({a.get('type')}):\n"
        km_counter = 1
        for lap in a.get("laps"):
            lap_dist = lap.get("distance", 0)
            if lap_dist > 100:
                lap_time = lap.get("moving_time", 0) or lap.get("elapsed_time", 0)
                lap_hr = lap.get("average_heartrate", 0)
                l_min = int(lap_time // 60)
                l_sec = int(lap_time % 60)
                lapy_text += f"  - Úsek {km_counter} ({round(lap_dist/1000,2)} km): Tempo {l_min}:{l_sec:02d} min/km | Tep: {round(lap_hr)} bpm\n"
                km_counter += 1

# --- CHATOVÝ VSTUP ---
user_input = st.chat_input("Zadaj príkaz alebo požiadaj o novú funkciu...")

if user_input:
    # OCHRANA PROTI NAMEERROR
    odpoved_ai = "Odpoveď sa nepodarilo vygenerovať."
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        full_context = f"{st.session_state.system_prompt}\n\nSUMÁR ZA 30 DNÍ:\n{historia_text}\n{lapy_text}\n\nPríkaz od Martina: {user_input}"
        
        # BEZPEČNÉ VOLANIE CEZ SECRETS - KĽÚČ JE SCHOVANÝ PRED GITHUBOM
        google_url = f"https://googleapis.com{st.secrets['GEMINI_API_KEY']}"
        google_payload = {"contents": [{"parts": [{"text": full_context}]}]}
        google_headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(google_url, json=google_payload, headers=google_headers)
            if response.status_code == 200:
                odpoved_json = response.json()
                odpoved_ai = odpoved_json['candidates']['content']['parts']['text']
                st.write(odpoved_ai)
                
                if "```python" in odpoved_ai:
                    st.write("🛠️ **[Detekovaný autogénny kód]: Spúšťam Python skript...**")
                    try:
                        kod_bloku = odpoved_ai.split("```python")[-1].split("```")[0]
                        local_vars = {"aktivity": aktivity, "st": st, "json": json}
                        exec(kod_bloku, globals(), local_vars)
                        st.success("✅ Autogénny kód prebehol úspešne!")
                    except Exception as exec_err:
                        st.error(f"Chyba pri exekúcii kódu: {exec_err}")
            else:
                odpoved_ai = f"Chyba Google API (Kód {response.status_code}): {response.text}"
                st.write(odpoved_ai)
        except Exception as ai_err:
            odpoved_ai = f"Chyba pri sieťovej komunikácii: {ai_err}"
            st.write(odpoved_ai)
            
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
