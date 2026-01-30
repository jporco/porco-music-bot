import os
import sys
import subprocess
from datetime import datetime

def search(query):
    # Salvar no histórico
    hist_path = os.path.expanduser("~/porco-bot/historico.txt")
    with open(hist_path, "a") as h:
        timestamp = datetime.now().strftime("%d/%m %H:%M")
        h.write(f"[{timestamp}] {query}\n")

    # Limpar cache do yt-dlp para resolver lentidão
    subprocess.run(["yt-dlp", "--rm-cache-dir"], capture_output=True)

    # Busca otimizada: --no-playlist e limitando o que ele baixa de info
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
    
    print(f"🔎 Buscando '{query}' no YouTube... Aguarde.", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()
    
    songs = []
    for i in range(0, len(result), 3):
        if i+2 < len(result):
            title = result[i]
            vid_id = result[i+1]
            duration = result[i+2]
            songs.append(f"[{duration}] {title} | https://www.youtube.com/watch?v={vid_id}")
    
    if songs:
        with open(os.path.expanduser("~/porco-bot/queue.txt"), "a") as f:
            for s in songs:
                f.write(s + "\n")
        print(f"✅ Adicionadas {len(songs)} músicas.")
    else:
        print("❌ Nenhuma música encontrada (Filtro: 7min).")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search(" ".join(sys.argv[1:]))
