#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime

# Configuração de caminhos
BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
HIST_FILE = os.path.join(BASE_DIR, "historico.txt")

def search(query, is_mix=False):
    os.makedirs(BASE_DIR, exist_ok=True)

    # Registrar no histórico
    try:
        with open(HIST_FILE, "a") as h:
            timestamp = datetime.now().strftime("%d/%m %H:%M")
            prefix = "MIX: " if is_mix else ""
            h.write(f"[{timestamp}] {prefix}{query}\n")
    except:
        pass

    # Limpa cache do yt-dlp
    subprocess.run(["yt-dlp", "--rm-cache-dir"], capture_output=True)

    if is_mix:
        print(f"🌀 Gerando mix para: {query}", flush=True)
        cmd = [
            "yt-dlp", "--get-title", "--get-id", "--get-duration",
            "--no-playlist", "--flat-playlist",
            "--match-filter", "duration < 900 & !is_live",
            "--ignore-errors", "--no-warnings",
            query
        ]
    else:
        print(f"🔎 Buscando '{query}'...", flush=True)
        cmd = [
            "yt-dlp", "--get-title", "--get-id", "--get-duration",
            "--no-playlist", "--default-search", "ytsearch10",
            "--match-filter", "duration < 900 & !is_live",
            "--ignore-errors", "--no-warnings",
            f"ytsearch10:{query}"
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
    
    songs = []
    for i in range(0, len(result), 3):
        if i+2 < len(result):
            title = result[i]
            vid_id = result[i+1]
            duration = result[i+2]
            songs.append(f"[{duration}] {title} | https://www.youtube.com/watch?v={vid_id}")
    
    if not songs:
        print("❌ Nada encontrado.")
        return

    # MODO INTERATIVO COM FZF (Se disponível e terminal)
    selected_songs = songs
    if sys.stdout.isatty():
        try:
            # Verifica se fzf existe
            subprocess.run(["fzf", "--version"], capture_output=True, check=True)
            
            # Prepara entrada para o fzf
            fzf_input = "\n".join(songs)
            # -m permite seleção múltipla com TAB
            fzf_proc = subprocess.Popen(
                ["fzf", "-m", "--header", "TAB para selecionar múltiplas, ENTER para confirmar", "--prompt", "🎵 Escolha: "],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            stdout, _ = fzf_proc.communicate(input=fzf_input)
            
            if stdout:
                selected_songs = [s.strip() for s in stdout.splitlines() if s.strip()]
            else:
                print("🚫 Seleção cancelada.")
                return
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Se não tiver fzf, usa as 5 primeiras para ser "mais inteligente" e não poluir
            selected_songs = songs[:5]

    with open(QUEUE_FILE, "a") as f:
        for s in selected_songs:
            f.write(s + "\n")
    
    print(f"✅ {len(selected_songs)} música(s) enviada(s) pro chiqueiro!")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--mix":
        search(sys.argv[2], is_mix=True)
    elif len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
    else:
        print("💡 Uso: play [termo] ou play --mix [link]")
