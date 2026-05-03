#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
HIST_FILE = os.path.join(BASE_DIR, "historico.txt")
CACHE_FILE = os.path.join(BASE_DIR, "play-cache.json")
CACHE_TTL_SECONDS = 6 * 60 * 60

MAX_SEC = 420  # 7 min — evita megamix / álbuns inteiros
MIN_SEC = 35   # evita shorts quebrados
RELATED = 5


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
            return data if isinstance(data, dict) else {}
    except Exception:
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
    if time.time() - item.get("ts", 0) > CACHE_TTL_SECONDS:
        return None
    songs = item.get("songs", [])
    return songs if isinstance(songs, list) and songs else None


def set_cached_songs(query, songs):
    key = cache_key(query)
    data = load_cache()
    data[key] = {"ts": int(time.time()), "songs": songs}
    if len(data) > 120:
        ordered = sorted(data.items(), key=lambda kv: kv[1].get("ts", 0), reverse=True)
        data = dict(ordered[:120])
    save_cache(data)


def yt_base():
    return [
        "yt-dlp",
        "--no-warnings",
        "--ignore-errors",
        "--flat-playlist",
    ]


def extract_id_from_line(line):
    m = re.search(r"v=([0-9A-Za-z_-]{6,})", line)
    return m.group(1) if m else ""


def extract_title_from_line(line):
    if "|" not in line:
        return ""
    left = line.split("|", 1)[0]
    left = re.sub(r"^\[[^\]]+\]\s*", "", left.strip())
    return left.strip()


def norm_title(t):
    t = t.lower()
    for w in (
        "official video",
        "official music video",
        "official audio",
        "legendado",
        "tradução",
        "lyrics",
        "live",
        "remaster",
        "remastered",
        "hd",
        "4k",
        "720p",
        "mv",
    ):
        t = t.replace(w, "")
    t = re.sub(r"\[[^\]]+\]", "", t)
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def too_similar(seed_title, cand_title):
    a = norm_title(seed_title)
    b = norm_title(cand_title)
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.82


def fetch_seed_line(query):
    filters = [
        f"duration>={MIN_SEC} & duration<={MAX_SEC} & !is_live",
        f"duration>={MIN_SEC} & duration<={MAX_SEC}",
        f"duration<={MAX_SEC + 60} & !is_live",
    ]
    target = f"ytsearch1:{query}"
    for flt in filters:
        cmd = yt_base() + [
            "--match-filter",
            flt,
            "--playlist-end",
            "1",
            "--print",
            "[%(duration_string)s] %(title)s | https://www.youtube.com/watch?v=%(id)s",
            target,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        line = (r.stdout or "").strip().splitlines()
        if line and "| https://" in line[0]:
            return line[0]
    return None


def fetch_related_lines(seed_id, seed_title):
    mix = f"https://www.youtube.com/watch?v={seed_id}&list=RD{seed_id}"
    cmd = yt_base() + [
        "--match-filter",
        f"duration>={MIN_SEC} & duration<={MAX_SEC} & !is_live",
        "--playlist-items",
        "2-40",
        "--print",
        "[%(duration_string)s] %(title)s | https://www.youtube.com/watch?v=%(id)s",
        mix,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    raw = [ln for ln in (r.stdout or "").splitlines() if ln.strip() and "| https://" in ln]

    out = []
    seen = {seed_id}
    for ln in raw:
        vid = extract_id_from_line(ln)
        if not vid or vid in seen:
            continue
        title = extract_title_from_line(ln)
        if too_similar(seed_title, title):
            continue
        seen.add(vid)
        out.append(ln.replace("[NA]", "[??:??]"))
        if len(out) >= RELATED:
            break

    if len(out) < RELATED:
        cmd2 = yt_base() + [
            "--match-filter",
            f"duration>={MIN_SEC} & duration<={MAX_SEC}",
            "--playlist-items",
            "2-60",
            "--print",
            "[%(duration_string)s] %(title)s | https://www.youtube.com/watch?v=%(id)s",
            mix,
        ]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
        raw2 = [ln for ln in (r2.stdout or "").splitlines() if ln.strip() and "| https://" in ln]
        for ln in raw2:
            vid = extract_id_from_line(ln)
            if not vid or vid in seen:
                continue
            title = extract_title_from_line(ln)
            if too_similar(seed_title, title):
                continue
            seen.add(vid)
            out.append(ln.replace("[NA]", "[??:??]"))
            if len(out) >= RELATED:
                break

    return out


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
        cmd = yt_base() + [
            "--playlist-end",
            "10",
            "--print",
            "[%(duration_string)s] %(title)s | https://www.youtube.com/watch?v=%(id)s",
            query,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        lines = [ln for ln in r.stdout.splitlines() if ln.strip() and "| https://" in ln][:10]
        added = append_songs_to_queue(lines)
        if added > 0:
            print(f"✅ {added} faixas adicionadas à fila!")
        else:
            print("❌ Não consegui ler essa playlist/link.")
        return

    cached = get_cached_songs(query)
    if cached:
        added = append_songs_to_queue(cached)
        print(f"⚡ Cache: {added} faixas reaplicadas na fila.")
        return

    print(f"🔎 Buscando: '{query}'")
    seed = fetch_seed_line(query)
    if not seed:
        print("❌ Não achei uma música compatível (tente outras palavras).")
        return

    seed = seed.replace("[NA]", "[??:??]")
    sid = extract_id_from_line(seed)
    stitle = extract_title_from_line(seed)

    print(f"🎯 Agora: {stitle}")

    rel = []
    if sid:
        print("🎛️ Montando fila com o Mix do YouTube (parecidas / mesmo clima)...")
        rel = fetch_related_lines(sid, stitle)

    block = [seed] + rel
    set_cached_songs(query, block)
    added = append_songs_to_queue(block)

    print(
        f"✅ Fila +{added}: 1 principal + {len(rel)} sugestões (cada uma até {MAX_SEC//60}min)."
    )


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--mix":
        search(sys.argv[2], is_mix=True)
    elif len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
    else:
        print("Uso: play [musica]")


if __name__ == "__main__":
    main()
