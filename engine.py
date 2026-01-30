import os
import time
import subprocess
import sys

QUEUE_FILE = os.path.expanduser("~/porco-bot/queue.txt")
SOCKET = "/tmp/porco.sock"

def log(msg):
    print(f"🐷 {msg}", flush=True)

def play_next():
    if not os.path.exists(QUEUE_FILE) or os.stat(QUEUE_FILE).st_size == 0:
        return

    with open(QUEUE_FILE, "r") as f:
        lines = f.readlines()
    
    if not lines:
        return

    next_song = lines[0].strip()
    with open(QUEUE_FILE, "w") as f:
        f.writelines(lines[1:])

    try:
        if "|" not in next_song:
            log(f"Linha inválida na fila: {next_song}")
            return
            
        url = next_song.split("|")[1].strip()
        log(f"Tocando agora: {next_song.split('|')[0]}")
        
        # Remove socket antigo se existir
        if os.path.exists(SOCKET):
            os.remove(SOCKET)

        subprocess.run([
            "mpv", "--no-video", 
            f"--input-ipc-server={SOCKET}",
            url
        ])
    except Exception as e:
        log(f"Erro ao tocar: {e}")

if __name__ == "__main__":
    log("Motor iniciado e aguardando fila...")
    while True:
        play_next()
        time.sleep(2)
