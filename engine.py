#!/usr/bin/env python3
import os
import subprocess
import time

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
VOL_FILE = os.path.join(BASE_DIR, "volume-atual.txt")
COOKIES_FILE = os.path.join(BASE_DIR, "youtube-cookies.txt")
SOCKET_PATH = "/tmp/porco.sock"


def get_last_volume():
    if os.path.exists(VOL_FILE):
        try:
            with open(VOL_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "80"


def extract_stream_url(line):
    line = line.strip()
    pos = line.rfind("https://")
    if pos != -1:
        return line[pos:].split()[0]
    pos = line.rfind("http://")
    if pos != -1:
        return line[pos:].split()[0]
    return line.rsplit("|", 1)[-1].strip()


def build_mpv_command(url, vol):
    cmd = [
        "mpv",
        "--no-video",
        "--ytdl-format=bestaudio/best",
        "--no-terminal",
        f"--input-ipc-server={SOCKET_PATH}",
        f"--volume={vol}",
    ]
    if os.path.isfile(COOKIES_FILE):
        cmd.append(f"--ytdl-raw-options=cookies={COOKIES_FILE}")
    cmd.append(url)
    return cmd


def play_next():
    if not os.path.exists(QUEUE_FILE):
        return False
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    if not lines:
        return False

    current = lines[0]
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines[1:]) + "\n")

    url = extract_stream_url(current)
    label = current.split("|", 1)[0].strip()
    print(f"🎶 Processando: {label}")

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    vol = get_last_volume()
    cmd = build_mpv_command(url, vol)

    proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    err = proc.stderr or ""

    if proc.returncode != 0:
        if "429" in err or "Too Many Requests" in err:
            print(
                "⚠️ YouTube limitou este IP (HTTP 429). Rádio segue ok porque não usa YouTube.\n"
                f"💡 Solução: exporte cookies do navegador (Netscape) para:\n   {COOKIES_FILE}\n"
                "   Depois: systemctl --user restart porco.service"
            )
        elif "Requested format is not available" in err:
            print("⚠️ Formato de áudio indisponível; tente atualizar: sudo yt-dlp -U")
        else:
            print("⚠️ Falha ao tocar URL. Verifique yt-dlp/mpv e tente atualizar o bot.")

    return True


if __name__ == "__main__":
    print("🚀 MOTOR PORCO (MINT VERSION) ATIVO")
    while True:
        if not play_next():
            time.sleep(1)
