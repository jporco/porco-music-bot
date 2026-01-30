import subprocess
import os
import time

QUEUE_FILE = os.path.expanduser("~/porco-bot/queue.txt")
SOCKET_PATH = "/tmp/porco.sock"

def play_next():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            lines = f.readlines()
        
        if lines:
            next_song = lines[0].strip()
            with open(QUEUE_FILE, "w") as f:
                f.writelines(lines[1:])
            
            url = next_song.split("|")[-1].strip()
            
            # Adicionado o filtro loudnorm para normalizar o volume
            cmd = [
                "mpv",
                "--no-video",
                f"--input-ipc-server={SOCKET_PATH}",
                "--af=loudnorm=I=-14:TP=-3:LRA=11", 
                "--no-terminal",
                url
            ]
            
            subprocess.run(cmd)
            return True
    return False

if __name__ == "__main__":
    while True:
        if not play_next():
            time.sleep(2)
