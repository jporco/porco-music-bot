#!/usr/bin/env python3
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


def _socket_alive():
    return os.path.exists(SOCKET_PATH)


def _send_socket_command(command):
    if not _socket_alive():
        return False
    payload = json.dumps({"command": command}) + "\n"
    try:
        r = subprocess.run(
            ["socat", "-", f"UNIX-CONNECT:{SOCKET_PATH}"],
            input=payload.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
        return r.returncode == 0
    except Exception:
        return False


def _kill_mpv():
    subprocess.run(
        ["pkill", "-u", str(os.getuid()), "-x", "mpv"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    time.sleep(0.25)
    try:
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
    except OSError:
        pass


def clear_current_playback():
    from youtube_queue import cancel
    cancel(clear=True)
    if _socket_alive():
        _send_socket_command(["stop"])
        time.sleep(0.2)
    _kill_mpv()


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
    return item if item["url"] else None


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
    key = item["url"].lower()
    for i, existing in enumerate(favorites):
        if existing["url"].lower() == key:
            # sobe pro topo p/ aparecer na 1a pagina
            favorites.pop(i)
            favorites.insert(0, existing)
            save_favorites(favorites)
            return True, (
                f"⚠️ Já estava nos favoritos: {existing['name']} "
                f"(posição {i + 1}) — movido para [1]"
            )
    # novos entram no topo
    favorites.insert(0, item)
    save_favorites(favorites)
    return True, f"⭐ Favorito salvo em [1]: {item['name']}"


def remove_favorite_by_number(number):
    favorites = load_favorites()
    if number < 1 or number > len(favorites):
        return None
    removed = favorites.pop(number - 1)
    save_favorites(favorites)
    return removed


def apply_play_volume():
    env = os.environ.copy()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    env.setdefault("PULSE_SERVER", f"unix:{env['XDG_RUNTIME_DIR']}/pulse/native")
    subprocess.run(
        ["bash", "-c", f"source {BASE_DIR}/funcoes.sh && volume_play"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        timeout=8,
        check=False,
    )


def tune_station(station):
    """Sintoniza já; se mpv estiver tocando, troca o stream sem travar."""
    item = normalize_station(station)
    if not item["url"]:
        return False, "❌ Rádio sem URL válida.", None

    from youtube_queue import cancel, locked, write_queue
    cancel(clear=True)

    title = f"📻 RADIO: {item['name']}"
    set_last_radio(item)
    with open(RADIO_ATUAL_FILE, "w", encoding="utf-8") as f:
        f.write(item["name"] + "\n")

    # O serviço permanece dono da reprodução ao alternar entre música e rádio.
    _send_socket_command(["stop"])
    with locked():
        apply_play_volume()
        write_queue([f"{title} | {item['url']}"])
    return True, "ok", item
