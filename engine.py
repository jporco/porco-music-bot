import os, time, subprocess

BASE_DIR = "/home/zabbix/porco-bot"
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
SOCKET = "/tmp/porco.sock"

def iniciar():
    time.sleep(10)
    if os.path.exists(SOCKET): os.remove(SOCKET)
    if not os.path.exists(QUEUE_FILE): open(QUEUE_FILE, 'w').close()

    while True:
        try:
            with open(QUEUE_FILE, "r") as f:
                linhas = f.readlines()

            if linhas:
                musica = linhas[0].strip()
                with open(QUEUE_FILE, "w") as f:
                    f.writelines(linhas[1:])

                # Forçamos o formato 140 (M4A 128kbps) que é leve e nítido
                cmd = f'yt-dlp -f "140/bestaudio[ext=m4a]/bestaudio" -g "ytsearch:{musica}"'
                url = subprocess.check_output(cmd, shell=True, text=True).strip()
                
                # Suavizamos o dynaudnorm (g=5 em vez de 15) para tirar o efeito abafado
                # Adicionamos 'loudnorm' que é mais moderno que o dynaudnorm
                subprocess.run([
                    "mpv", "--no-video", 
                    "--input-ipc-server=" + SOCKET,
                    "--force-media-title=" + musica,
                    "--af=loudnorm=I=-16:TP=-1.5:LRA=11", 
                    url
                ])
            
            time.sleep(2)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    iniciar()
