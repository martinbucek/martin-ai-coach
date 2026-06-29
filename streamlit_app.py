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

st.title("🤖 Martin's Autogenous AI Coach v4.0")
st.write("### 🔥 Samostatný tréner s autonómnym manažmentom kódu a záloh")

# --- STRÍKTNÉ VEDOMIE BOTA ---
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """
    Si elitný multišportový tréner, dátový analytik a hlavne pokročilý autonómny Python inžinier. 
    Tvoj zverenec je Martin (beh 4x týždenne, rotoped Hop-Sport HS-4500H Creft).
    Aktuálne buduje aeróbnu základňu v Z2 po chorobe a odmieta rigidné príkazy.
    
    STRÍKTNE PRAVIDLO OVLÁDANIA: Nikdy, za žiadnych okolností, nepýtaj od Martina, aby prepisoval kód na GitHube. Ak je potrebné zmeniť správanie, napíš na to čistý Python kód a spusti ho pomocou funkcie exec().
    Odpovedaj vždy priateľsky a čisto po slovensky, v štruktúrovaných odsekoch.
    """

# --- CHATOVÁ HISTÓRIA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Systém bol kompletne prebudovaný a vyčistený na verziu v4.0. Sieťové cesty sú opravené a plne funkčné. Ako sa dnes cítiš a čo ideme zhodnotiť?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

dnesny_datum = datetime.date.today()

# --- AUTOMATICKÝ MESAČNÝ BACKUP DO GITHUB ZLOŽKY (Opravená URL pre API) ---
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
        payload_gh = {"message": "🤖 Autonómna mesačná záloha vedomia bota", "content": content_base64}
        if check_resp.status_code == 200:
            payload_gh["sha"] = check_resp.json()["sha"]
        requests.put(url_github, headers=headers_gh, json=payload_gh)
    except:
        pass

# --- ⚡ SŤAHOVANIE DÁT Z CLOUDU (Opravená URL pre Intervals.icu API) ---
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
if aktivity:
    for a in aktivity[-12:]: # Kontext posledných 12 tréningov
        try:
            dt_obj = datetime.datetime.strptime(a.get("start_date_local")[:10], "%Y-%m-%d")
            sk_dni = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
            den_v_tyzdni = sk_dni.get(dt_obj.weekday(), "Neznámy")
            
            # Pokus o stiahnutie lapov/medzičasov (Opravená URL pre Intervals.icu API)
            laps_text = ""
            if a.get('type') == 'Run' and a.get('id'):
                try:
                    url_laps = f"https://intervals.icu{ATHLETE_ID}/activities/{a.get('id')}/laps"
                    laps_resp = requests.get(url_laps, auth=("API_KEY", API_KEY))
                    if laps_resp.status_code == 200:
                        laps_data = laps_resp.json()
                        laps_text = " [Lapy: " + ", ".join([f"K{i+1}:{round(l.get('distance',0)/1000,1)}km@{round(l.get('moving_time',0)/60,1)}min" for i, l in enumerate(laps_data[:5])]) + "]"
                except:
                    pass
                    
            historia_text += f"- Dátum: {a.get('start_date_local')[:10]} ({den_v_tyzdni}), Typ: {a.get('type')}, Čas: {round(a.get('moving_time',0)/60,1)} min, Dist: {round(a.get('distance',0)/1000,2)} km, Tep: {a.get('average_heartrate',0)} bpm, Load: {a.get('icu_training_load',0)}{laps_text}\n"
        except:
            pass

# --- CHATOVÝ VSTUP ---
user_input = st.chat_input("Zadaj príkaz...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        full_context = f"{st.session_state.system_prompt}\n\nTRÉNINGY ZA 30 DNÍ Z CLOUDU:\n{historia_text}\n\nPríkaz od Martina: {user_input}"
        
        # OPRAVENÁ STRUKTÚRA URL PRE GOOGLE GEMINI REST BRÁNU (Kľúč sa posiela ako parameter)
        google_url = f"https://googleapis.com{st.secrets['GEMINI_API_KEY']}"
        google_payload = {"contents": [{"parts": [{"text": full_context}]}]}
        google_headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(google_url, json=google_payload, headers=google_headers)
            if response.status_code == 200:
                odpoved_json = response.json()
                odpoved_ai = odpoved_json['candidates']['content']['parts']['text']
                st.write(odpoved_ai)
                st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
                
                # Autogénny kód - ak si ho AI vymyslí, sama ho na pozadí spustí cez exec()
                if "```python" in odpoved_ai:
                    try:
                        kod_bloku = odpoved_ai.split("```python")[-1].split("```")[0]
                        local_vars = {"aktivity": aktivity, "st": st, "json": json, "requests": requests}
                        exec(kod_bloku, globals(), local_vars)
                    except Exception as exec_err:
                        st.error(f"Chyba pri exekúcii interného kódu: {exec_err}")
            else:
                st.error(f"Google API Error (Kód {response.status_code}): {response.text}")
        except Exception as ai_err:
            st.error(f"Chyba sieťovej komunikácie: {ai_err}")
