#!/usr/bin/env python3
import fcntl
import json
import os
import re
import subprocess
import sys
import time

from artista_yt import list_songs

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
LOOP_FILE = os.path.join(BASE_DIR, "loop-ativo.json")
LOCK_FILE = QUEUE_FILE + ".lock"
SOCKET = "/tmp/porco.sock"
TARGET = 5


def _load():
    if not os.path.exists(LOOP_FILE):
        return {}
    try:
        with open(LOOP_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data):
    with open(LOOP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def disable():
    try:
        os.remove(LOOP_FILE)
    except OSError:
        pass


def extract_id(url):
    m = re.search(r"(?:v=|/watch\?v=|youtu\.be/)([0-9A-Za-z_-]{11})", url or "")
    if m:
        return m.group(1)
    stem = os.path.basename(url or "").rsplit(".", 1)[0]
    return stem if re.fullmatch(r"[0-9A-Za-z_-]{11}", stem) else ""


def guess_artist(title):
    t = (title or "").strip()
    return t.split(" - ", 1)[0].strip() if " - " in t else t


def _qlock():
    fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR, 0o644)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def _qunlock(fd):
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)


def _read_lines():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def _write_lines(lines):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def _ids_from_lines(lines):
    return {extract_id(ln) for ln in lines if extract_id(ln)}


def pop_line():
    fd = _qlock()
    try:
        lines = _read_lines()
        if not lines:
            return None
        cur, rest = lines[0], lines[1:]
        _write_lines(rest)
        return cur
    finally:
        _qunlock(fd)


def _mpv(prop):
    try:
        r = subprocess.run(
            ["socat", "-", f"UNIX-CONNECT:{SOCKET}"],
            input=f'{{"command":["get_property","{prop}"]}}\n'.encode(),
            capture_output=True,
            timeout=2,
            check=False,
        )
        m = re.search(rb'"data"\s*:\s*"([^"]+)"', r.stdout or b"")
        return m.group(1).decode("utf-8", "replace") if m else ""
    except Exception:
        return ""


def _playing_id():
    return extract_id(_mpv("path"))


def note_played(url, title):
    st = _load()
    if not st.get("on"):
        return
    vid = extract_id(url)
    seen = st.get("seen") or []
    if vid and vid not in seen:
        seen.append(vid)
        st["seen"] = seen[-80:]
        st["last_id"] = vid
    if title:
        st["last_title"] = title
        st["artist"] = st.get("artist") or guess_artist(title)
    _save(st)


def _fetch(artist, seen, need):
    out = []
    for s in list_songs(artist, max(need + 2, 6)):
        if s["id"] in seen:
            continue
        out.append({"id": s["id"], "title": s["title"], "url": s["url"]})
        if len(out) >= need:
            break
    return out


def _try_fill_lock():
    fd = os.open(LOCK_FILE + ".fill", os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except OSError:
        os.close(fd)
        return None


def maybe_fill():
    st = _load()
    if not st.get("on"):
        return False
    fill_fd = _try_fill_lock()
    if fill_fd is None:
        return False
    try:
        return _fill_locked(st)
    finally:
        fcntl.flock(fill_fd, fcntl.LOCK_UN)
        os.close(fill_fd)


def _fill_locked(st):
    fd = _qlock()
    try:
        lines = _read_lines()
        need = TARGET - len(lines)
        queued = _ids_from_lines(lines)
    finally:
        _qunlock(fd)
    if need <= 0:
        return False
    artist = (st.get("artist") or guess_artist(st.get("last_title") or "")).strip()
    if not artist:
        return False
    seen = set(st.get("seen") or []) | queued
    pid = _playing_id()
    if pid:
        seen.add(pid)
    pool = [p for p in (st.get("pool") or []) if p.get("id") not in seen]
    now = time.time()
    if not pool:
        if now - float(st.get("last_fetch") or 0) < 40:
            return False
        pool = _fetch(artist, seen, need)
        st["last_fetch"] = now
        if not pool:
            _save(st)
            return False
    added = 0
    while pool and added < need:
        song = pool.pop(0)
        if song["id"] in seen:
            continue
        fd = _qlock()
        try:
            lines = _read_lines()
            if len(lines) >= TARGET:
                pool.insert(0, song)
                break
            if song["id"] in _ids_from_lines(lines):
                continue
            title = song["title"].replace("|", "-")
            _write_lines(lines + [f"{title} | {song['url']}"])
        finally:
            _qunlock(fd)
        seen.add(song["id"])
        added += 1
        print(f"loop: +1 {title[:60]}")
    st["pool"] = pool[:12]
    st["seen"] = list(seen)[-80:]
    st["artist"] = artist
    _save(st)
    return added > 0


def enable(query=""):
    title = (query or _mpv("media-title") or "").strip()
    artist = (query or guess_artist(title) or "").strip()
    seen = list(_ids_from_lines(_read_lines()))
    pid = _playing_id()
    if pid and pid not in seen:
        seen.append(pid)
    _save({"on": True, "seen": seen, "artist": artist, "last_title": title, "pool": []})
    print(f"loop on: {artist or title or 'artista atual'}")
    maybe_fill()


def main():
    args = sys.argv[1:]
    import youtube_queue as q
    if args and args[0].lower() in ("off", "stop", "para"):
        disable()
        with q.locked():
            state = q.read_state()
            state["loop"] = False
            q.save_state(state)
        print("loop off")
        return
    query = " ".join(args).strip() or q.read_state().get("query", "")
    if not query:
        print("Uso: playlist-loop [busca] | playlist-loop off")
        return
    subprocess.run(["systemctl", "--user", "start", "porco.service"], check=True)
    ok, message = q.submit_confirmed(query, loop=True)
    print(message)
    if ok:
        print("Loop ativado: reposição de até 2 faixas; fila limitada a 30.")


if __name__ == "__main__":
    main()
