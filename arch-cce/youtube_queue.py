#!/usr/bin/env python3
"""Bounded YouTube jobs owned by the CCE service, never by the SSH shell."""
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid

import media_control

BASE = Path(os.environ.get("PORCO_BASE_DIR", Path.home() / "porco-music-bot"))
QUEUE = BASE / "queue.txt"
STATE = BASE / "youtube-state.json"
SOCKET = os.environ.get("PORCO_SOCKET", "/tmp/porco.sock")
LOCK = BASE / "queue.txt.lock"
CACHE = BASE / "youtube-cache"
BATCH_SIZE = 5
MAX_TRACKS = 30  # Faixas aguardando; a música em reprodução fica separada.


@contextlib.contextmanager
def locked():
    BASE.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def read_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(STATE)


def read_queue():
    try:
        return [s for s in QUEUE.read_text().splitlines() if s.strip()]
    except OSError:
        return []


def write_queue(lines):
    tmp = QUEUE.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""))
    tmp.replace(QUEUE)


def ipc(command):
    try:
        with socket.socket(socket.AF_UNIX) as s:
            s.settimeout(1)
            s.connect(SOCKET)
            s.sendall((json.dumps({"command": command, "request_id": 73}) + "\n").encode())
            buf = b""
            while True:
                packet = s.recv(65536)
                if not packet:
                    return None
                buf += packet
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    data = json.loads(line)
                    if data.get("request_id") == 73:
                        return data
                if not buf:
                    return None
    except (OSError, ValueError):
        return None


def track_id(url):
    match = re.search(r"(?:[?&]v=|youtu\.be/)([\w-]{11})(?:[&?#]|$)", url)
    return match.group(1) if match else ""


def outstanding(state):
    current = state.get("current") or {}
    return len(read_queue()) + int(bool(current.get("generation")) and current.get("generation") == state.get("generation"))


def reserved(state):
    """Pending files + unfulfilled requests, always read under the queue lock."""
    active = state.get("active_job") or {}
    return (len(read_queue()) + active.get("remaining", 0)
            + sum(job["count"] for job in state.get("jobs", [])))


class QueueFull(Exception):
    def __init__(self, used, count):
        super().__init__(f"Fila: {used}/{MAX_TRACKS}, incluindo buscas em preparação. "
                         f"Adicionar até {count} ultrapassaria o limite de {MAX_TRACKS}.")


def cancel(clear=False):
    with locked():
        state = read_state()
        state.update(generation=uuid.uuid4().hex, jobs=[], active_job=None,
                     status="parado", query="", loop=False, history=[], last_track=None)
        save_state(state)
        if clear:
            write_queue([])
        (BASE / "loop-ativo.json").unlink(missing_ok=True)


def submit(query, more=False, loop=False, clear=False):
    with locked():
        old = read_state()
        query = query.strip() or (old.get("query", "") if more else "")
        if not query:
            return False, "Uso: play [busca] | play-artista [nome] | mais [busca opcional]"
        count = 2 if more else BATCH_SIZE
        if not clear and reserved(old) + count > MAX_TRACKS:
            raise QueueFull(reserved(old), count)
        current = old.get("current") or {}
        state = old
        if clear:
            state = {"generation": uuid.uuid4().hex, "current": old.get("current"),
                     "seen": [current["id"]] if current.get("id") else [],
                     "titles": [normalized_title(current["title"])] if current.get("id") else [],
                     "jobs": [], "active_job": None, "history": old.get("history", []),
                     "last_track": old.get("last_track")}
            write_queue([])
        if not (current.get("id") or read_queue() or state.get("jobs") or state.get("active_job")):
            state.update(seen=[], titles=[], ready_ids=[], history=[], last_track=None)
        state.setdefault("generation", uuid.uuid4().hex)
        # Só a primeira busca substitui o rádio; acrescentar músicas nunca
        # interrompe a música atual nem cancela a busca anterior.
        replace = not (current.get("id") or read_queue() and state.get("query")
                       or state.get("jobs") or state.get("active_job"))
        state.setdefault("jobs", []).append({"id": uuid.uuid4().hex, "query": query,
                                             "count": count, "replace": replace})
        state.update(query=query, loop=loop, error="", requested_at=time.time())
        if not state.get("active_job"):
            state["status"] = "buscando"
        (BASE / "loop-ativo.json").unlink(missing_ok=True)
        save_state(state)
    return True, f"Adicionando ao final: {query}. Até {count} faixas em segundo plano; acompanhe com fila."


def submit_confirmed(query, more=False, loop=False):
    try:
        return submit(query, more=more, loop=loop)
    except QueueFull as exc:
        print(str(exc))
        # Nunca aguardar entrada segurando o lock usado pelo player/worker.
        try:
            answer = input("Deseja limpar a fila aguardando, mantendo a música atual? [sim/não]: ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            return False, "Pedido cancelado. A fila foi mantida."
        if answer not in ("sim", "s"):
            return False, "Pedido cancelado. A fila foi mantida."
        return submit(query, more=more, loop=loop, clear=True)


def show_status():
    with locked():
        state = read_state()
        lines = read_queue()
    playing = ipc(["get_property", "idle-active"])
    active = bool(playing and playing.get("data") is False)
    spotify = media_control.selected(active)
    if spotify:
        _, status, metadata = spotify
        title = metadata.get("xesam:title", {}).get("data") or "Faixa sem título"
        artists = metadata.get("xesam:artist", {}).get("data") or []
        track = " — ".join([", ".join(artists), title]) if artists else title
        print(f"Spotify | {'Pausado' if status == 'Paused' else 'Tocando'}: {track}")
    elif active:
        title = (ipc(["get_property", "media-title"]) or {}).get("data") or "Carregando…"
        paused = (ipc(["get_property", "pause"]) or {}).get("data")
        print(f"{'Pausado' if paused else 'Tocando'}: {title}")
    elif state.get("current"):
        print(f"Carregando: {state['current']['title']}")
    else:
        print("Reprodução parada.")
    try:
        volume = int((BASE / "volume-atual.txt").read_text().strip())
    except (OSError, ValueError):
        pass
    else:
        muted = (BASE / "mute-ativo.txt").exists()
        print(f"Volume geral: {volume}%" + (" | mudo" if muted else ""))
    if state.get("query"):
        print(f"YouTube | {state.get('status', '')} | {state['query']}" + (" | loop ativo" if state.get("loop") else ""))
        if state.get("error"):
            print(state["error"])
    print(f"Fila: {len(lines)}/{MAX_TRACKS} músicas aguardando.")
    active = state.get("active_job") or {}
    if active:
        print(f"Preparando: {active['query']} (até {active['remaining']} restantes)")
    for job in state.get("jobs", []):
        print(f"Busca aguardando: {job['query']} (até {job['count']} faixas)")
    for i, line in enumerate(lines, 1):
        vid = track_id(line.rsplit(" | ", 1)[-1])
        ready = "pronta" if vid in state.get("ready_ids", []) else "na fila"
        print(f"{i}. {line.split(' | ', 1)[0]} [{ready}]")
    if not lines:
        print("Fila vazia.")


def import_ytdlp():
    bundled = BASE / "tools" / "yt-dlp"
    if bundled.is_file():
        sys.path.insert(0, str(bundled))
    try:
        import yt_dlp
    except ImportError:
        executable = shutil.which("yt-dlp")
        if not executable:
            raise RuntimeError("yt-dlp não instalado")
        sys.path.insert(0, executable)
        import yt_dlp
    return yt_dlp


def normalized_title(title):
    text = title.split(" - ", 1)[-1].lower()
    text = re.sub(r"\([^)]*\)|\[[^]]*\]", "", text)
    text = re.sub(r"\b(official|video|audio|lyrics|remastered|hd|4k)\b", "", text)
    return re.sub(r"\W+", " ", text).strip()


def error_detail(error):
    return re.sub(r"https?://\S+", "[URL]", str(error)).replace("\n", " ")[:240]


class Cancelled(Exception):
    pass


class Pipeline:
    def __init__(self):
        self.yt = import_ytdlp()
        self.ready = {}
        self.guard = threading.Lock()
        self.closed = threading.Event()
        self.catalog = {}
        self.preparing = {}

    def valid(self, generation):
        return not self.closed.is_set() and read_state().get("generation") == generation

    def check(self, generation):
        if not self.valid(generation):
            raise Cancelled()

    def options(self):
        opts = {"quiet": True, "noprogress": True, "socket_timeout": 8,
                "retries": 1, "extractor_retries": 1, "fragment_retries": 1,
                "noplaylist": True, "format": "bestaudio[acodec=opus]/bestaudio",
                "source_address": "0.0.0.0",
                "cachedir": str(BASE / ".yt-dlp-cache"),
                "outtmpl": str(CACHE / "%(id)s.%(ext)s"),
                "logger": self}
        deno = BASE / "tools" / "deno"
        if deno.is_file():
            opts["js_runtimes"] = {"deno": {"path": str(deno)}}
        cookies = BASE / "youtube-cookies.txt"
        if cookies.is_file():
            opts["cookiefile"] = str(cookies)
        return opts

    def debug(self, message):
        pass

    def warning(self, message):
        print(f"YouTube aviso: {message}", flush=True)

    def error(self, message):
        # URLs de mídia temporárias não são registradas no log.
        print(f"YouTube: {error_detail(message)}", flush=True)

    def local_audio(self, vid):
        for directory in (CACHE, BASE / "dl"):
            for ext in ("webm", "m4a", "opus", "mp3", "ogg"):
                path = directory / f"{vid}.{ext}"
                if path.is_file() and path.stat().st_size > 4096 and not Path(str(path) + ".part").exists():
                    return str(path)
        return ""

    def resolve(self, url):
        vid = track_id(url)
        local = self.local_audio(vid) if vid else ""
        if local:
            return {"path": local, "local": True}
        with self.yt.YoutubeDL(self.options()) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info or not info.get("url"):
            raise RuntimeError("YouTube não forneceu áudio reproduzível.")
        duration = info.get("duration")
        if info.get("is_live") or (duration and not 35 <= duration <= 480):
            raise RuntimeError("Faixa ignorada: live ou duração fora de 35 segundos a 8 minutos.")
        return {"path": info["url"], "local": False, "headers": info.get("http_headers", {}), "info": info}

    def source(self, url):
        vid = track_id(url)
        with self.guard:
            result = self.ready.get(vid)
        if result:
            if result.get("local") and not Path(result["path"]).is_file():
                result = None
            elif not result.get("local") and time.time() - result.get("ts", 0) > 3600:
                result = None
        return result or self.resolve(url)

    def prepare(self, song, generation, download):
        with self.guard:
            lock = self.preparing.setdefault(song["id"], threading.Lock())
        with lock:
            return self._prepare(song, generation, download)

    def _prepare(self, song, generation, download):
        self.check(generation)
        source = self.source(song["url"])
        self.check(generation)
        if download and not source["local"]:
            def progress(_data):
                self.check(generation)
            opts = self.options()
            opts["progress_hooks"] = [progress]
            try:
                CACHE.mkdir(exist_ok=True)
                with self.yt.YoutubeDL(opts) as ydl:
                    ydl.process_info(dict(source["info"]))
                self.check(generation)
                local = self.local_audio(song["id"])
                if local:
                    source = {"path": local, "local": True}
            except Cancelled:
                raise
            except Exception:
                self.check(generation)
                print(f"Cache indisponível; áudio direto: {song['title']}", flush=True)
        source["ts"] = time.time()
        with self.guard:
            self.ready[song["id"]] = source
            if len(self.ready) > 100:
                self.ready.pop(next(iter(self.ready)))
        return source

    def candidates(self, query):
        key = query.casefold().strip()
        cached = self.catalog.get(key)
        if cached and time.time() - cached["ts"] < 6 * 3600:
            yield from cached["songs"]
            return
        opts = self.options()
        opts.update(extract_flat=True, skip_download=True, lazy_playlist=True,
                    playlistend=20, noplaylist=False)
        if query.startswith(("https://", "http://")):
            from urllib.parse import urlparse
            if urlparse(query).hostname not in ("youtube.com", "www.youtube.com", "music.youtube.com", "youtu.be"):
                raise RuntimeError("Para músicas, use uma busca ou um link do YouTube.")
            target = query
        else:
            target = "ytsearch20:" + query
        with self.yt.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(target, download=False)
            entries = result.get("entries") if result else []
            if result and entries is None:
                entries = [result]
            songs = []
            for entry in entries or []:
                if not entry:
                    continue
                vid, title = entry.get("id", ""), entry.get("title", "")
                duration = entry.get("duration")
                if not re.fullmatch(r"[\w-]{11}", vid) or not title:
                    continue
                if entry.get("is_live") or entry.get("live_status") in ("is_live", "is_upcoming"):
                    continue
                if duration is not None and not 35 <= duration <= 480:
                    continue
                songs.append({"id": vid, "title": re.sub(r"[\x00-\x1f\x7f|]", " ", title)[:160],
                              "url": f"https://www.youtube.com/watch?v={vid}", "channel": entry.get("channel", "")})
                yield songs[-1]
            self.catalog[key] = {"ts": time.time(), "songs": songs}
            if len(self.catalog) > 30:
                self.catalog.pop(next(iter(self.catalog)))

    def update(self, generation, **fields):
        with locked():
            state = read_state()
            if state.get("generation") == generation:
                state.update(fields)
                save_state(state)

    def execute(self, generation, job):
        self.update(generation, status="buscando", error="")
        added, failures, last_failure = 0, 0, ""
        for song in self.candidates(job["query"]):
            self.check(generation)
            with locked():
                state = read_state()
                if song["id"] in state.get("seen", []) or normalized_title(song["title"]) in state.get("titles", []):
                    continue
                if len(read_queue()) >= MAX_TRACKS:
                    break
            self.update(generation, status="preparando")
            try:
                self.prepare(song, generation, download=added > 0 or not job["replace"])
            except Cancelled:
                raise
            except Exception as exc:
                failures += 1
                last_failure = error_detail(exc)
                print(f"Faixa ignorada: {song['title']} ({last_failure})", flush=True)
                if failures >= 5:
                    break
                continue
            with locked():
                state = read_state()
                self.check(generation)
                if len(read_queue()) >= MAX_TRACKS:
                    break
                if added == 0 and job["replace"]:
                    spotify = media_control.spotify()
                    if spotify and spotify[1] == "Playing":
                        media_control.spotify_command(spotify[0], "pause")
                write_queue(read_queue() + [f"{song['title']} | {song['url']}"])
                state["seen"] = (state.get("seen", []) + [song["id"]])[-200:]
                state["titles"] = (state.get("titles", []) + [normalized_title(song["title"])])[-200:]
                state["ready_ids"] = (state.get("ready_ids", []) + [song["id"]])[-200:]
                active = state.get("active_job") or {}
                if active.get("id") == job.get("id"):
                    active["remaining"] = max(0, active["remaining"] - 1)
                save_state(state)
                if added == 0 and job["replace"]:
                    (BASE / "radio-atual.txt").unlink(missing_ok=True)
                    ipc(["stop"])
            added += 1
            print(f"YouTube pronta {added}/{job['count']}: {song['title']}", flush=True)
            if added >= job["count"]:
                break
        message = "" if added else "Não encontrei novas faixas reproduzíveis para essa busca."
        if not added and last_failure:
            message += f" Última falha: {last_failure}"
        self.update(generation, status="pronto" if added else "erro", error=message)
        self.prune()

    def prune(self):
        CACHE.mkdir(exist_ok=True)
        with locked():
            state = read_state()
            protected = {track_id(line.rsplit(" | ", 1)[-1]) for line in read_queue()}
            protected.add((state.get("current") or {}).get("id"))
        files = sorted((p for p in CACHE.iterdir() if re.fullmatch(r"[\w-]{11}\.(webm|m4a|opus|mp3|ogg)", p.name)),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        size = 0
        for i, path in enumerate(files):
            size += path.stat().st_size
            if (i >= MAX_TRACKS + 1 or size > 250 * 1024 * 1024) and path.stem not in protected:
                path.unlink(missing_ok=True)
        # Somente fragmentos do cache novo; downloads antigos são preservados.
        for path in CACHE.iterdir():
            if path.suffix in (".part", ".ytdl") and time.time() - path.stat().st_mtime > 3600:
                path.unlink(missing_ok=True)

    def worker(self):
        while not self.closed.is_set():
            with locked():
                state = read_state()
                jobs = state.get("jobs", [])
                job = jobs.pop(0) if jobs else None
                generation = state.get("generation")
                if (not job and state.get("loop") and state.get("query")
                        and outstanding(state) <= 2
                        and time.time() - state.get("last_auto_fill", 0) > 30):
                    job = {"query": state["query"], "count": 2, "replace": False}
                    state["last_auto_fill"] = time.time()
                if job:
                    job.setdefault("id", uuid.uuid4().hex)
                    state["active_job"] = dict(job, remaining=job["count"])
                    state["status"] = "buscando"
                    save_state(state)
            if job:
                try:
                    self.execute(generation, job)
                except Cancelled:
                    pass
                except Exception as exc:
                    self.update(generation, status="erro", error=f"A busca falhou: {error_detail(exc)}")
                    print(f"Busca YouTube falhou: {error_detail(exc)}", flush=True)
                finally:
                    with locked():
                        state = read_state()
                        if (state.get("generation") == generation
                                and (state.get("active_job") or {}).get("id") == job["id"]):
                            state["active_job"] = None
                            if state.get("jobs"):
                                state["status"] = "buscando"
                            save_state(state)
            self.closed.wait(0.2)


def main():
    args = sys.argv[1:]
    action = args.pop(0) if args else "status"
    if action == "status":
        show_status()
        return 0
    if action == "playing":
        result = ipc(["get_property", "idle-active"])
        return 0 if result and result.get("data") is False else 1
    if action == "stop":
        ipc(["stop"])
        return 0
    if action == "cancel":
        cancel(clear="--clear" in args)
        return 0
    subprocess.run(["systemctl", "--user", "start", "porco.service"], check=True)
    ok, message = submit_confirmed(" ".join(args), more=action == "more")
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
