import os
import sys
import subprocess
from datetime import datetime

def search(query, is_mix=False):
    hist_path = os.path.expanduser("~/porco-bot/historico.txt")
    with open(hist_path, "a") as h:
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        h.write(f"[{timestamp}] {'MIX: ' if is_mix else ''}{query}\n")

    subprocess.run(["yt-dlp", "--rm-cache-dir"], capture_output=True)

    if is_mix:
        # Pega vídeos relacionados ao link fornecido
        print(f"🌀 Gerando mix baseado no link... Aguarde.", flush=True)
        cmd = [
            "yt-dlp",
            "--get-title", "--get-id", "--get-duration",
            "--no-playlist",
            "--flat-playlist",
            "--match-filter", "duration < 420 & !is_live",
            "--ignore-errors",
            "--no-warnings",
            f"https://www.youtube.com/watch?v={query}" if len(query) == 11 else query
        ]
        # Adicionamos uma lógica extra para pegar os 'related' via --url-query se necessário,
        # mas o padrão mix do YT geralmente vem via playlist ou flat-playlist.
    else:
        # Busca normal
        print(f"🔎 Buscando '{query}'... Aguarde.", flush=True)
        cmd = [
            "yt-dlp",
            "--get-title", "--get-id", "--get-duration",
            "--no-playlist",
            "--default-search", "ytsearch10",
            "--match-filter", "duration < 420 & !is_live",
            "--ignore-errors",
            "--no-warnings",
            f"ytsearch10:{query}"
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
    
    songs = []
    # Limita a 10 músicas (cada música ocupa 3 linhas no output: título, id, duração)
    for i in range(0, min(len(result), 30), 3):
        if i+2 < len(result):
            title = result[i]
            vid_id = result[i+1]
            duration = result[i+2]
            songs.append(f"[{duration}] {title} | https://www.youtube.com/watch?v={vid_id}")
    
    if songs:
        with open(os.path.expanduser("~/porco-bot/queue.txt"), "a") as f:
            for s in songs:
                f.write(s + "\n")
        print(f"✅ Adicionadas {len(songs)} músicas ao Mix.")
    else:
        print("❌ Nenhuma música encontrada nos critérios (7min).")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--mix":
        search(sys.argv[2], is_mix=True)
    elif len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
