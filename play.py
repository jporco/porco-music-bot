#!/usr/bin/env python3
import os, sys, subprocess
from datetime import datetime

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
HIST_FILE = os.path.join(BASE_DIR, "historico.txt")

def search(query, is_mix=False):
    os.makedirs(BASE_DIR, exist_ok=True)
    try:
        with open(HIST_FILE, "a") as h:
            h.write(f"[{datetime.now().strftime('%d/%m %H:%M')}] {'MIX: ' if is_mix else ''}{query}\n")
    except: pass

    if is_mix:
        print(f"🌀 Gerando mix baseado no link...")
        search_target = query
        extra_args = ["--playlist-end", "10"]
    else:
        print(f"🔎 Buscando '{query}' no YouTube... (Top 5)")
        search_target = f"ytsearch15:{query}"
        extra_args = ["--default-search", "ytsearch15"]

    cmd = [
        "yt-dlp", "--print", "[%(duration_string)s] %(title)s | https://www.youtube.com/watch?v=%(id)s",
        "--no-playlist", "--flat-playlist",
        "--match-filter", "duration < 900 & !is_live",
        "--ignore-errors", "--no-warnings",
        *extra_args,
        search_target
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
    songs = [line for line in result if line.strip() and "| https://" in line][:5]
    
    if songs:
        with open(QUEUE_FILE, "a") as f:
            for s in songs:
                f.write(s.replace("[NA]", "[??:??]") + "\n")
        print(f"✅ {len(songs)} músicas adicionadas à fila!")
    else:
        print("❌ Nenhuma música encontrada nos critérios (máx 15min).")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--mix":
        search(sys.argv[2], is_mix=True)
    elif len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
    else:
        print("Uso: play [musica]")
