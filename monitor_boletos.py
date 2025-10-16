import requests
from bs4 import BeautifulSoup
import json
import unicodedata
import os

# --- CONFIGURACIÓN ---
URLS = {
    "Fedefut": "https://fedefutguate.gt/noticias/",
    "Fanaticks": "https://www.fanaticks.live/events?utm_source=chatgpt",
    "Todoticket": "https://www.todoticket.com/"
}

# Palabras clave desde variables de entorno
keywords_env = os.environ.get("KEYWORDS_ENV", "")
KEYWORDS = [word.strip() for word in keywords_env.split(",") if word.strip()]

# Variables de entorno para Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Archivo de estado para evitar alertas repetidas
STATE_FILE = "monitor_state.json"


# --- FUNCIONES AUXILIARES ---
def normalize_text(text: str) -> str:
    """Convierte a minúsculas y elimina acentos/diacríticos"""
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')


def load_state():
    """Carga el estado previo (alertas enviadas)"""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_state(state):
    """Guarda el estado actual"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram_message(text: str):
    """Envía mensaje a Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[ERROR] Faltan variables TELEGRAM_TOKEN o CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
        print(f"[ALERTA ENVIADA] {text}")
    except Exception as e:
        print(f"[ERROR Telegram]: {e}")


def check_site(name, url, previous_state):
    """Revisa un sitio en busca de palabras clave"""
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        text = normalize_text(soup.get_text())

        alert_needed = any(normalize_text(word) in text for word in KEYWORDS)

        if alert_needed:
            if not previous_state.get(name):
                message = f"⚽ Venta de boletos detectada en {name}\nRevisa: {url}"
                send_telegram_message(message)
                previous_state[name] = True
        else:
            previous_state[name] = False

    except Exception as e:
        print(f"[ERROR] {name}: {e}")


# --- MAIN ---
def main():
    state = load_state()
    print("[INFO] Iniciando revisión de sitios...")
    print(f"[INFO] Palabras clave: {KEYWORDS or '(ninguna definida)'}")

    for name, url in URLS.items():
        check_site(name, url, state)

    save_state(state)
    print("[INFO] Revisión completada correctamente ✅")


if __name__ == "__main__":
    main()
