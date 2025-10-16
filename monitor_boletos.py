import requests
from bs4 import BeautifulSoup
import json
import time
import unicodedata
import os

# --- CONFIGURACIÓN ---
URLS = {
    "Fedefut": "https://fedefutguate.gt/noticias/",
    "Fanaticks": "https://www.fanaticks.live/events?utm_source=chatgpt",
    "Todoticket": "https://www.todoticket.com/"
}

keywords_env = os.environ.get("KEYWORDS_ENV", "")
KEYWORDS = [word.strip() for word in keywords_env.split(",") if word.strip()]

CHECK_INTERVAL = 3600  # 1 hora en segundos

# --- Telegram ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# --- Estado para evitar alertas repetidas ---
STATE_FILE = "monitor_state.json"

# --- FUNCIONES ---
def normalize_text(text):
    """Convierte a minúsculas y elimina acentos/diacríticos"""
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
        print("[ALERTA ENVIADA] Telegram")
    except Exception as e:
        print(f"[ERROR Telegram]: {e}")

def check_site(name, url, previous_state):
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        text = normalize_text(text)

        alert_needed = any(normalize_text(word) in text for word in KEYWORDS)

        if alert_needed:
            if previous_state.get(name) != True:
                message = f"⚽ Venta de boletos detectada en {name}\nRevisa: {url}"
                send_telegram_message(message)
                previous_state[name] = True
        else:
            previous_state[name] = False

    except Exception as e:
        print(f"[ERROR] {name}: {e}")

# --- SCRIPT PRINCIPAL ---
def main():
    state = load_state()
    while True:
        print("[INFO] Revisando sitios...")
        for name, url in URLS.items():
            check_site(name, url, state)
        save_state(state)
        print(f"[INFO] Esperando {CHECK_INTERVAL/60} minutos para la siguiente revisión...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
