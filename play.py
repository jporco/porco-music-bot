#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from datetime import datetime

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
HIST_FILE = os.path.join(BASE_DIR, "historico.txt")
CACHE_FILE = os.path.join(BASE_DIR, "play-cache.json")
CACHE_TTL_SECONDS = 6 * 60 * 60


def append_history(query, is_mix=False):
    try:
        with open(HIST_FILE, "a", encoding="utf-8") as h:
            prefix = "MIX: " if is_mix else ""
            h.write(f"[{datetime.now().strftime('%d/%m %H:%M')}] {prefix}{query}\n")
    except Exception:
        pass


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def cache_key(query):
    return " ".join(query.lower().split())


def get_cached_songs(query):
    key = cache_key(query)
    data = load_cache()
    item = data.get(key)
    if not isinstance(item, dict):
        return None

    ts = item.get("ts", 0)
    songs = item.get("songs", [])
    if not isinstance(songs, list) or not songs:
        return None

    if time.time() - ts > CACHE_TTL_SECONDS:
        return None

    return songs


def set_cached_songs(query, songs):
    key = cache_key(query)
    data = load_cache()
    data[key] = {"ts": int(time.time()), "songs": songs}

    # Mantem cache enxuto (ultimas 120 buscas)
    if len(data) > 120:
        ordered = sorted(data.items(), key=lambda kv: kv[1].get("ts", 0), reverse=True)
        data = dict(ordered[:120])

    save_cache(data)


def run_yt_search(search_target, max_items, allow_playlist=False):
    cmd = [
        "yt-dlp",
        "--print",
        "[%(duration_string)s] %(title)s | https://www.youtube.com/watch?v=%(id)s",
        "--flat-playlist",
        "--ignore-errors",
        "--no-warnings",
        "--playlist-end",
        str(max_items),
    ]

    if not allow_playlist:
        cmd.append("--no-playlist")

    cmd.append(search_target)

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = result.stdout.splitlines()
    return [line for line in lines if line.strip() and "| https://" in line][:max_items]


def append_songs_to_queue(songs):
    if not songs:
        return 0
    try:
        with open(QUEUE_FILE, "a", encoding="utf-8") as f:
            for s in songs:
                f.write(s.replace("[NA]", "[??:??]") + "\n")
        return len(songs)
    except Exception:
        return 0


def search(query, is_mix=False):
    os.makedirs(BASE_DIR, exist_ok=True)
    append_history(query, is_mix=is_mix)

    if is_mix:
        print("🌀 Gerando mix baseado no link...")
        songs = run_yt_search(query, max_items=10, allow_playlist=True)
        added = append_songs_to_queue(songs)
        if added > 0:
            print(f"✅ {added} músicas adicionadas à fila!")
        else:
            print("❌ Nenhuma música encontrada para essa busca.")
        return

    cached = get_cached_songs(query)
    if cached:
        added = append_songs_to_queue(cached)
        print(f"⚡ Cache local: {added} músicas adicionadas instantaneamente!")
        return

    print(f"🔎 Busca rápida no YouTube: '{query}' (Top 5)")
    songs = run_yt_search(f"ytsearch5:{query}", max_items=5, allow_playlist=False)

    if songs:
        set_cached_songs(query, songs)
        added = append_songs_to_queue(songs)
        print(f"✅ {added} músicas adicionadas à fila!")
    else:
        print("❌ Nenhuma música encontrada para essa busca.")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--mix":
        search(sys.argv[2], is_mix=True)
    elif len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
    else:
        print("Uso: play [musica]")


if __name__ == "__main__":
    main()
