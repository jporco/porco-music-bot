#!/usr/bin/env python3
import subprocess, os, time, sys

QUEUE_FILE = os.path.expanduser("~/porco-music-bot/queue.txt")
SOCKET_PATH = "/tmp/porco.sock"

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

    # Remove socket antigo se existir
    if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)

    # Comando MPV OTIMIZADO PARA ALTA PERFORMANCE
    cmd = [
        "mpv", "--no-video", "--no-terminal",
        f"--input-ipc-server={SOCKET_PATH}",
        "--ao=pulse", "--cache=yes", 
        "--ytdl-format=bestaudio/best",
        "--ytdl-raw-options=ignore-config=,sub-format=en,write-auto-subs=",
        "--audio-buffer=0.2", "--initial-audio-buffer=0.2",
        "--force-window=no", "--osd-level=0",
        url
    ]
    subprocess.run(cmd)
    return True

if __name__ == "__main__":
    print("🚀 MOTOR PORCO (ARCH VERSION) ATIVO")
    while True:
        if not play_next():
            time.sleep(1)
