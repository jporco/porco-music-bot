#!/usr/bin/env python3
import subprocess, os, time, sys

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
VOL_FILE = os.path.join(BASE_DIR, "volume-atual.txt")
SOCKET_PATH = "/tmp/porco.sock"

def get_last_volume():
    if os.path.exists(VOL_FILE):
        try:
            with open(VOL_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return "80"

def play_next():
    if not os.path.exists(QUEUE_FILE): return False
    with open(QUEUE_FILE, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if not lines: return False

    current = lines[0]
    with open(QUEUE_FILE, "w") as f:
        f.writelines("\n".join(lines[1:]) + "\n")
    
    url = current.split("|")[-1].strip()
    print(f"🎶 Processando: {current.split('|')[0]}")

    if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)
    vol = get_last_volume()

    cmd = [
        "mpv", "--no-video", "--ytdl-format=bestaudio/best", "--no-terminal",
        f"--input-ipc-server={SOCKET_PATH}",
        f"--volume={vol}",
        url
    ]
    subprocess.run(cmd)
    return True

if __name__ == "__main__":
    print("🚀 MOTOR PORCO (MINT VERSION) ATIVO")
    while True:
        if not play_next():
            time.sleep(1)
