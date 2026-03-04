#!/usr/bin/env python3
import subprocess, os, time, sys

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
SOCKET_PATH = "/tmp/porco_mpv.sock"
RADIO_FILE = os.path.join(BASE_DIR, "radio-atual.txt")

def play_next():
    if not os.path.exists(QUEUE_FILE): return False
    with open(QUEUE_FILE, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if not lines: return False

    current = lines[0]
    with open(QUEUE_FILE, "w") as f:
        f.writelines("\n".join(lines[1:]) + "\n")
    
    # Extrair título e URL
    parts = current.split("|")
    title = parts[0].strip()
    url = parts[-1].strip()
    
    print(f"🎶 Processando: {title}", flush=True)
    
    # REGISTRO IMEDIATO: Atualiza o status antes mesmo do MPV carregar
    with open(RADIO_FILE, "w") as f:
        f.write(title)

    # PRE-RESOLUÇÃO ULTRA-RÁPIDA DO URL REAL
    print(f"🛰️  Resolvendo link para {title}...", flush=True)
    direct_url = url
    try:
        ytdl_cmd = [
            "yt-dlp", "--get-url", 
            "--format", "bestaudio[ext=m4a]/bestaudio/best",
            "--no-check-certificates", "--socket-timeout", "5",
            url
        ]
        direct_url = subprocess.check_output(ytdl_cmd, text=True).strip()
    except Exception as e:
        print(f"⚠️  Aviso: Falha ao resolver URL direto ({e}). Usando fallback.", flush=True)

    # Remove socket antigo se existir
    if os.path.exists(SOCKET_PATH):
        try: os.remove(SOCKET_PATH)
        except: pass

    # Comando MPV INSTANTÂNEO
    cmd = [
        "mpv", "--no-video", "--no-terminal",
        f"--input-ipc-server={SOCKET_PATH}",
        "--ao=pulse", "--cache=yes", 
        "--no-config", "--idle=no",
        "--audio-buffer=1.0", 
        "--force-window=no", "--osd-level=0",
        f"--force-media-title={title}",
        direct_url
    ]
    
    try:
        with open(os.path.join(BASE_DIR, "bot.log"), "a") as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=log)
        
        # POLVERIZA A ESPERA: O socket agora nasce quase na hora!
        for _ in range(30):
            if os.path.exists(SOCKET_PATH): break
            time.sleep(0.1)
        
        proc.wait()
    except Exception as e:
        print(f"❌ Falha crítica no motor MPV: {e}", flush=True)
    
    # Limpa o status ao terminar a música
    if os.path.exists(RADIO_FILE): 
        try: os.remove(RADIO_FILE)
        except: pass
    
    return True

if __name__ == "__main__":
    print("🚀 MOTOR PORCO (ARCH VERSION) ATIVO", flush=True)
    while True:
        try:
            if not play_next():
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"🧨 Erro no loop do motor: {e}", flush=True)
            time.sleep(2)
