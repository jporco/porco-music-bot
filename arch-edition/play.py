#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime

# Configuração de caminhos para a pasta correta
BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
HIST_FILE = os.path.join(BASE_DIR, "historico.txt")

def search(query, is_mix=False):
    # Garante que a pasta existe
    os.makedirs(BASE_DIR, exist_ok=True)

    # Registrar no histórico
    try:
        with open(HIST_FILE, "a") as h:
            timestamp = datetime.now().strftime("%d/%m %H:%M")
            h.write(f"[{timestamp}] {'MIX: ' if is_mix else ''}{query}\n")
    except:
        pass

    # Limpa cache do yt-dlp para evitar erros de busca
    subprocess.run(["yt-dlp", "--rm-cache-dir"], capture_output=True)

    if is_mix:
        print(f"🌀 Gerando mix baseado no link... Aguarde.", flush=True)
        # Lógica para Mix/Relacionados
        cmd = [
            "yt-dlp", "--get-title", "--get-id", "--get-duration",
            "--no-playlist", "--flat-playlist",
            "--match-filter", "duration < 600 & !is_live", # Limite aumentado para 10min
            "--ignore-errors", "--no-warnings",
            query
        ]
    else:
        print(f"🔎 Buscando '{query}' no YouTube...", flush=True)
        cmd = [
            "yt-dlp", "--get-title", "--get-id", "--get-duration",
            "--no-playlist", "--default-search", "ytsearch10",
            "--match-filter", "duration < 600 & !is_live",
            "--ignore-errors", "--no-warnings",
            f"ytsearch10:{query}"
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
    
    songs = []
    # Processa o output (Título, ID, Duração)
    for i in range(0, len(result), 3):
        if i+2 < len(result):
            title = result[i]
            vid_id = result[i+1]
            duration = result[i+2]
            songs.append(f"[{duration}] {title} | https://www.youtube.com/watch?v={vid_id}")
    
    if songs:
        with open(QUEUE_FILE, "a") as f:
            for s in songs:
                f.write(s + "\n")
        print(f"✅ {len(songs)} músicas adicionadas à fila do Porco!")
    else:
        print("❌ Nenhuma música encontrada (critério: menos de 10min).")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--mix":
        search(sys.argv[2], is_mix=True)
    elif len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
    else:
        print("Uso: play [musica] ou play --mix [link]")
