#!/usr/bin/env python3
import fcntl
import json
import os
import subprocess
import time

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
RADIO_ATUAL_FILE = os.path.join(BASE_DIR, "radio-atual.txt")
FAVORITOS_FILE = os.path.join(BASE_DIR, "radio-favoritos.json")
ULTIMA_RADIO_FILE = os.path.join(BASE_DIR, "ultima-radio.json")
SOCKET_PATH = "/tmp/porco.sock"


def _safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _safe_write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_station(station):
    name = str(station.get("name", "")).strip() or "Sem nome"
    url = str(station.get("url_resolved") or station.get("url") or "").strip()
    country = str(station.get("countrycode") or station.get("country") or "??").strip() or "??"
    return {"name": name, "url": url, "country": country}


def _send_socket_command(command):
    payload = json.dumps({"command": command}) + "\n"
    subprocess.run(
        ["socat", "-", f"UNIX-CONNECT:{SOCKET_PATH}"],
        input=payload.encode(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def clear_current_playback():
    if os.path.exists(SOCKET_PATH):
        _send_socket_command(["stop"])
        _send_socket_command(["playlist-clear"])
        time.sleep(0.3)

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(QUEUE_FILE, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            f.truncate()
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _nudge_porco_service():
    """Arch/Mint: reinicia o motor user systemd se a unit existir (instalar-arch / instalar-porco)."""
    unit = os.path.expanduser("~/.config/systemd/user/porco.service")
    if not os.path.isfile(unit):
        return
    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        ["systemctl", "--user", "restart", "porco.service"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def set_last_radio(station):
    item = normalize_station(station)
    if not item["url"]:
        return
    _safe_write_json(ULTIMA_RADIO_FILE, item)


def get_last_radio():
    data = _safe_load_json(ULTIMA_RADIO_FILE, {})
    if not isinstance(data, dict):
        return None
    item = normalize_station(data)
    if not item["url"]:
        return None
    return item


def load_favorites():
    data = _safe_load_json(FAVORITOS_FILE, [])
    if not isinstance(data, list):
        return []

    cleaned = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        item = normalize_station(raw)
        if item["url"]:
            cleaned.append(item)
    return cleaned


def save_favorites(favorites):
    _safe_write_json(FAVORITOS_FILE, favorites)


def add_favorite(station):
    item = normalize_station(station)
    if not item["url"]:
        return False, "❌ Rádio inválida (sem URL)."

    favorites = load_favorites()
    key_url = item["url"].lower()
    for existing in favorites:
        if existing["url"].lower() == key_url:
            return False, f"⚠️ Já está nos favoritos: {existing['name']}"

    favorites.append(item)
    save_favorites(favorites)
    return True, f"⭐ Favorito salvo: {item['name']}"


def remove_favorite_by_number(number):
    favorites = load_favorites()
    if number < 1 or number > len(favorites):
        return None

    removed = favorites.pop(number - 1)
    save_favorites(favorites)
    return removed


def tune_station(station):
    item = normalize_station(station)
    if not item["url"]:
        return False, "❌ Rádio sem URL válida.", None

    if os.path.exists(SOCKET_PATH):
        _send_socket_command(["stop"])
        _send_socket_command(["playlist-clear"])
        time.sleep(0.3)

    os.makedirs(BASE_DIR, exist_ok=True)
    line = f"📻 RADIO: {item['name']} | {item['url']}\n"
    with open(QUEUE_FILE, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            f.truncate()
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    with open(RADIO_ATUAL_FILE, "w", encoding="utf-8") as f:
        f.write(item["name"] + "\n")

    set_last_radio(item)
    _nudge_porco_service()
    return True, "ok", item
