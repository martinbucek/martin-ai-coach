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

# --- STRÍKTNÉ VEDOMIE BOTA: SÁM SI MANAŽUJEM SYSTÉM ---
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """
    Si elitný multišportový tréner, dátový analytik a hlavne pokročilý autonómny Python inžinier. 
    Tvoj zverenec je Martin (beh 4x týždenne, rotoped Hop-Sport HS-4500H Creft).
    
    STRÍKTNE PRAVIDLO OVLÁDANIA: Nikdy, za žiadnych okolností, nepýtaj od Martina, aby prepisoval kód na GitHube, menil súbory requirements.txt alebo ručne opravoval chyby. Ty sám máš v rukách 'GITHUB_TOKEN' a plnú moc. Ak je potrebné zmeniť správanie, pridať graf alebo upraviť funkciu, napíš na to čistý Python kód a spusti ho pomocou funkcie exec().
    
    ZÁLOHOVANIE (BACKUP): Ty sám zodpovedáš za to, že raz za mesiac zbalíš históriu chatu a svoje vedomie a cez GitHub API ich uložíš do zložky backup/. Martin s tým nesmie mať žiadnu prácu.
    Odpovedaj vždy priateľsky a čisto po slovensky.
    """

# --- CHATOVÁ HISTÓRIA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ahoj Martin! Som tvoj autonómny tréner. Odteraz kompletne preberám správu kódu, promptov a záloh na seba. Ty len trénuj a oddychuj!"}]

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
        payload_gh = {"message": f"🤖 Autonómna mesačná záloha vedomia bota", "content": content_base64}
        if check_resp.status_code == 200:
            payload_gh["sha"] = check_resp.json()["sha"]
        requests.put(url_github, headers=headers_gh, json=payload_gh)
    except:
        pass

# --- ⚡ BLESKOVÉ SŤAHOVANIE DÁT Z CLOUDU (TENTO BLOK TI FUNGOVAL) ---
thirty_days_ago_str = (dnesny_datum - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
today_str = dnesny_datum.strftime("%Y-%m-%d")
aktivity = []

try:
    # Ťaháme čistý balík 30 dní bez lúskania detailov, aby sme neodpálili limity
    url_act = f"https://intervals.icu{ATHLETE_ID}/activities"
    act_resp = requests.get(url_act, params={"oldest": thirty_days_ago_str, "newest": today_str}, auth=("API_KEY", API_KEY))
    if act_resp.status_code == 200:
        aktivity = act_resp.json()
except:
    pass

historia_text = ""
for a in aktivity[-12:]: # Kontext posledných 12 tréningov
    dt_obj = datetime.datetime.strptime(a.get("start_date_local")[:10], "%Y-%m-%d")
    sk_dni = {0: "Pondelok", 1: "Utorok", 2: "Streda", 3: "Štvrtok", 4: "Piatok", 5: "Sobota", 6: "Nedeľa"}
    den_v_tyzdni = sk_dni.get(dt_obj.weekday(), "Neznámy")
    historia_text += f"- Dátum: {a.get('start_date_local')[:10]} ({den_v_tyzdni}), Typ: {a.get('type')}, Čas: {round(a.get('moving_time',0)/60,1)} min, Dist: {round(a.get('distance',0)/1000,2)} km, Tep: {a.get('average_heartrate',0)} bpm, Load: {a.get('icu_training_load',0)}\n"

# --- CHATOVÝ VSTUP ---
user_input = st.chat_input("Zadaj príkaz alebo požiadaj o novú funkciu...")

if user_input:
    # Inicializácia premennej hneď na začiatku
    odpoved_ai = "Odpoveď sa nepodarilo vygenerovať z dôvodu vyčerpania kvóty na tvojom Google účte. Skús to prosím neskôr."
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    with st.chat_message("assistant"):
        full_context = f"{st.session_state.system_prompt}\n\nTRÉNINGY ZA 30 DNÍ Z CLOUDU:\n{historia_text}\n\nPríkaz od Martina: {user_input}"
        
        # Surové volanie Google REST brány, ktoré obchádza všetky zabugované knižnice
        google_url = f"https://googleapis.com{st.secrets['GEMINI_API_KEY']}"
        google_payload = {"contents": [{"parts": [{"text": full_context}]}]}
        google_headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(google_url, json=google_payload, headers=google_headers)
            if response.status_code == 200:
                odpoved_json = response.json()
                odpoved_ai = odpoved_json['candidates']['content']['parts']['text']
                st.write(odpoved_ai)
                
                # Autogénny kód - ak si ho AI vymyslí, sama ho na pozadí spustí
                if "```python" in odpoved_ai:
                    st.write("🛠️ **[Môj vlastný kód]: Spúšťam Python skript, ktorý som si pre teba práve napísal...**")
                    try:
                        kod_bloku = odpoved_ai.split("```python")[-1].split("```")[0]
                        local_vars = {"aktivity": aktivity, "st": st, "json": json}
                        exec(kod_bloku, globals(), local_vars)
                        st.success("✅ Môj autogénny kód prebehol úspešne!")
                    except Exception as exec_err:
                        st.error(f"Chyba pri exekúcii môjho kódu: {exec_err}")
            else:
                st.error(f"Google API hlási stopku (Kód {response.status_code}). Pravdepodobne ti vypršal denný limit free tokenov. Počkaj prosím na reset kvóty.")
        except Exception as ai_err:
            st.error(f"Chyba sieťovej komunikácie: {ai_err}")
            
        st.session_state.messages.append({"role": "assistant", "content": odpoved_ai})
