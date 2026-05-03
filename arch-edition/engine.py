#!/usr/bin/env python3
import fcntl
import os
import re
import shutil
import subprocess
import time

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
VOL_FILE = os.path.join(BASE_DIR, "volume-atual.txt")
COOKIES_FILE = os.path.join(BASE_DIR, "youtube-cookies.txt")
SOCKET_PATH = "/tmp/porco.sock"

YTDLP = shutil.which("yt-dlp") or "/usr/local/bin/yt-dlp"

YOUTUBE_CLIENTS = (
    "android",
    "web",
    "web_embedded",
    "mweb",
    "tv_embedded",
)


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


def is_youtube_page(url):
    u = url.lower()
    return "youtube.com/" in u or "youtu.be/" in u


def sanitize_title(text):
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return text[:160]


def yt_dlp_base_cmd():
    cmd = [YTDLP]
    if os.path.isfile(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
    cmd.extend(
        [
            "--no-warnings",
            "--no-check-certificates",
            "-f",
            "ba/bestaudio/best",
            "-g",
        ]
    )
    return cmd


def yt_dlp_resolve_direct_stream(page_url):
    last_err = ""

    for client in YOUTUBE_CLIENTS:
        cmd = yt_dlp_base_cmd() + ["--extractor-args", f"youtube:player_client={client}", page_url]
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            out = (r.stdout or "").strip().splitlines()
            cand = out[0].strip() if out else ""
            if cand.startswith("http"):
                return cand, None
            last_err = (r.stderr or "")[-500:] or "yt-dlp: sem URL"
        except subprocess.TimeoutExpired:
            last_err = "yt-dlp: timeout ao resolver stream"
        except Exception as exc:
            last_err = str(exc)

    cmd = yt_dlp_base_cmd() + [page_url]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        out = (r.stdout or "").strip().splitlines()
        cand = out[0].strip() if out else ""
        if cand.startswith("http"):
            return cand, None
        last_err = (r.stderr or "")[-500:] or last_err
    except Exception as exc:
        last_err = str(exc)

    return None, last_err


def build_mpv_command(play_url, vol, media_title, use_ytdl_hook):
    cmd = ["mpv", "--no-video"]
    if use_ytdl_hook:
        cmd.append("--ytdl-format=bestaudio/best")
        if os.path.isfile(COOKIES_FILE):
            cmd.append(f"--ytdl-raw-options=cookies={COOKIES_FILE}")
    else:
        cmd.append("--no-ytdl")
    cmd.append("--no-terminal")
    if media_title:
        cmd.append(f"--force-media-title={sanitize_title(media_title)}")
    cmd.extend(
        [
            f"--input-ipc-server={SOCKET_PATH}",
            f"--volume={vol}",
            play_url,
        ]
    )
    return cmd


def play_next():
    if not os.path.exists(QUEUE_FILE):
        return False

    os.makedirs(BASE_DIR, exist_ok=True)
    current = None
    with open(QUEUE_FILE, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            raw = f.read()
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            if not lines:
                return False
            current = lines[0]
            rest = lines[1:]
            f.seek(0)
            f.truncate()
            f.write("\n".join(rest) + ("\n" if rest else ""))
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    url = extract_stream_url(current)
    label = current.split("|", 1)[0].strip()
    print(f"🎶 Processando: {label}")

    if os.path.exists(SOCKET_PATH):
        try:
            os.remove(SOCKET_PATH)
        except OSError:
            pass

    vol = get_last_volume()

    play_url = url
    use_ytdl = False

    if is_youtube_page(url):
        stream, err = yt_dlp_resolve_direct_stream(url)
        if stream:
            play_url = stream
            use_ytdl = False
        else:
            print(
                "⚠️ Não consegui obter URL direta do YouTube via yt-dlp.\n"
                f"Detalhe: {err if err else 'erro desconhecido'}\n"
                "↩️ Tentando modo legado (mpv + hook do ytdl)..."
            )
            play_url = url
            use_ytdl = True

    cmd = build_mpv_command(play_url, vol, media_title=label, use_ytdl_hook=use_ytdl)
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    err = proc.stderr or ""

    if proc.returncode != 0:
        if "429" in err or "Too Many Requests" in err:
            print(
                "⚠️ YouTube ainda retornou HTTP 429.\n"
                "💡 Atualize o yt-dlp: sudo yt-dlp -U"
            )
        elif "Requested format is not available" in err:
            print("⚠️ Formato indisponível; rode: sudo yt-dlp -U")
        else:
            tail_err = [ln for ln in err.strip().splitlines() if ln.strip()][-3:]
            if tail_err:
                print("⚠️ Falha no mpv:\n" + "\n".join(tail_err))

    return True


if __name__ == "__main__":
    print("🚀 MOTOR PORCO (ARCH EDITION) ATIVO")
    while True:
        if not play_next():
            time.sleep(1)
