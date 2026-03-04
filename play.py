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
        print(f"🔎 Buscando '{query}' no YouTube...", flush=True)
        # USAR --print para extrair apenas o necessário em uma única chamada
        # --flat-playlist evita processar playlists inteiras se o resultado for uma
        cmd = [
            "yt-dlp",
            "--print", "%(title)s|%(id)s|%(duration_string)s",
            "--no-playlist", "--flat-playlist",
            "--default-search", "ytsearch10",
            "--ignore-errors", "--no-warnings",
            "--no-check-certificates", "--socket-timeout", "5",
            f"ytsearch10:{query}"
        ]
    
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result = proc.stdout.splitlines()
    
    songs = []
    # O formato agora é uma linha por vídeo: Título|ID|Duração
    for line in result:
        if "|" in line:
            try:
                title, vid_id, duration = line.split("|", 2)
                songs.append(f"[{duration}] {title} | https://www.youtube.com/watch?v={vid_id}")
            except ValueError:
                continue
    
    if not songs:
        print("❌ Nada encontrado.")
        return

    # MODO DE SELEÇÃO
    selected_songs = []
    
    if sys.stdout.isatty():
        try:
            # Tenta usar FZF primeiro
            subprocess.run(["fzf", "--version"], capture_output=True, check=True)
            fzf_input = "\n".join(songs)
            fzf_proc = subprocess.Popen(
                [
                    "fzf", "-m", 
                    "--header", "TAB: selecionar | CTRL-A: todos | CTRL-D: nenhum", 
                    "--prompt", "🎵 Escolha: ",
                    "--bind", "ctrl-a:select-all,ctrl-d:deselect-all"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            stdout, _ = fzf_proc.communicate(input=fzf_input)
            if stdout:
                selected_songs = [s.strip() for s in stdout.splitlines() if s.strip()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # FALLBACK: Lista numerada
            print("\n" + "="*40)
            print("🎵 RESULTADOS DA BUSCA (Selecione o número)")
            print("="*40)
            for idx, song in enumerate(songs, 1):
                print(f"{idx}. {song.split('|')[0]}")
            print("="*40)
            try:
                choice = input("👉 Escolha o(s) número(s) (ex: 1 3 ou 'a'): ")
                if choice.lower() == 'a':
                    selected_songs = songs
                else:
                    indices = [int(i)-1 for i in choice.split() if i.isdigit()]
                    selected_songs = [songs[i] for i in indices if 0 <= i < len(songs)]
            except (ValueError, EOFError, KeyboardInterrupt):
                pass
    else:
        # Se não for TTY, pega o primeiro
        selected_songs = songs[:1]

    if not selected_songs:
        print("🚫 Seleção cancelada.")
        return

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
