#!/usr/bin/env python3
"""Audio playback and YouTube preparation always run on this host."""
from pathlib import Path
import json
import re
import signal
import socket
import subprocess
import tempfile
import threading
import time
import uuid

import youtube_queue as ytq


def get_last_volume():
    volume = 43
    try:
        configured = int((ytq.BASE / "volume-padrao.txt").read_text().strip())
        if 1 <= configured <= 100:
            volume = configured
    except (OSError, ValueError):
        pass
    for name in ("volume-atual.txt", "volume-antes-mute.txt"):
        try:
            raw = int((ytq.BASE / name).read_text().strip())
            if 0 <= raw <= 100:
                volume = raw
                break
        except (OSError, ValueError):
            pass
    try:
        volume = min(volume, int((ytq.BASE / "test-volume-limit.txt").read_text().strip()))
    except (OSError, ValueError):
        pass
    return max(0, volume)


def take_line():
    with ytq.locked():
        lines = ytq.read_queue()
        if not lines:
            return None
        line = lines.pop(0)
        ytq.write_queue(lines)
        title, url = line.rsplit(" | ", 1) if " | " in line else line.rsplit("|", 1)
        state = ytq.read_state()
        vid = ytq.track_id(url.strip())
        current = {"id": vid, "title": title.strip(), "token": uuid.uuid4().hex,
                   "generation": state.get("generation") if vid and vid in state.get("seen", []) else None,
                   "started_at": time.time(), "line": line}
        state["current"] = current
        if vid:
            previous = state.get("last_track")
            if previous and previous != line:
                state["history"] = (state.get("history", []) + [previous])[-30:]
            state["last_track"] = line
        else:
            state.update(history=[], last_track=None)
        ytq.save_state(state)
        return title.strip(), url.strip(), current, state.get("generation")


def clear_current(token):
    with ytq.locked():
        state = ytq.read_state()
        if (state.get("current") or {}).get("token") == token:
            state["current"] = None
            ytq.save_state(state)


def build_command():
    command = ["mpv", "--no-config", "--no-video", "--no-ytdl", "--no-terminal",
               "--idle=yes", "--keep-open=no",
               "--cache=yes", "--cache-secs=10", "--demuxer-max-bytes=8M",
               "--audio-buffer=0.2", "--audio-device=pulse/radio_level",
               "--input-ipc-server=/tmp/porco.sock", "--volume=100", "--volume-max=100",
               "--stream-lavf-o=reconnect=1,reconnect_streamed=1,reconnect_delay_max=2",
               "--mute=yes" if (ytq.BASE / "mute-ativo.txt").exists() else "--mute=no"]
    return command


class Player:
    def __init__(self):
        Path("/tmp/porco.sock").unlink(missing_ok=True)
        self.errors = tempfile.TemporaryFile()
        self.proc = subprocess.Popen(build_command(), stdout=subprocess.DEVNULL, stderr=self.errors)
        self.connection = socket.socket(socket.AF_UNIX)
        self.connection.settimeout(.2)
        deadline = time.monotonic() + 30
        while True:
            try:
                self.connection.connect("/tmp/porco.sock")
                break
            except OSError:
                if self.proc.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Player não abriu o controle de áudio")
                time.sleep(.05)
        self.buffer = b""

    def events(self, pipeline):
        while not pipeline.closed.is_set() and self.proc.poll() is None:
            try:
                packet = self.connection.recv(65536)
                if not packet:
                    return
                self.buffer += packet
                while b"\n" in self.buffer:
                    line, self.buffer = self.buffer.split(b"\n", 1)
                    yield json.loads(line)
            except socket.timeout:
                continue

    def play(self, source, title, pipeline, generation):
        headers = [f"{key}: {value}" for key, value in source.get("headers", {}).items()
                   if key.lower() in ("user-agent", "referer", "origin")]
        options = {"force-media-title": title,
                   "http-header-fields": ",".join(h.replace(",", "\\,") for h in headers)}
        # Serialize loading with radio/stop/new-request generation changes.
        with ytq.locked():
            if ytq.read_state().get("generation") != generation:
                return
            ytq.ipc(["set_property", "volume", 100])
            ytq.ipc(["set_property", "mute", (ytq.BASE / "mute-ativo.txt").exists()])
            ytq.ipc(["set_property", "pause", False])
            answer = ytq.ipc(["loadfile", source["path"], "replace", -1, options])
            if not answer or answer.get("error") != "success":
                raise RuntimeError("Player recusou a faixa")
        active_id = None
        for event in self.events(pipeline):
            if event.get("event") == "start-file":
                active_id = event.get("playlist_entry_id")
            elif event.get("event") == "end-file" and active_id is not None and event.get("playlist_entry_id") == active_id:
                if event.get("reason") == "error":
                    self.errors.seek(0, 2)
                    length = self.errors.tell()
                    self.errors.seek(max(0, length - 1500))
                    detail = self.errors.read().decode("utf-8", "replace")
                    detail = re.sub(r"https?://\S+", "[mídia]", detail)
                    print(f"Falha na reprodução: {title}; detalhe: {detail[-700:]}", flush=True)
                    return False
                return True

    def close(self):
        self.connection.close()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.errors.close()


def play_next(pipeline, player):
    item = take_line()
    if not item:
        return False
    title, url, current, generation = item
    try:
        source = pipeline.source(url) if ytq.track_id(url) else {"path": url, "local": Path(url).is_file()}
        if ytq.read_state().get("generation") != generation:
            return True
        print(f"Tocando: {title} ({'cache local' if source.get('local') else 'áudio direto'})", flush=True)
        played = player.play(source, title, pipeline, generation)
        if played is False and not source.get("local") and ytq.track_id(url) and pipeline.valid(generation):
            print(f"Recuperando áudio em arquivo local: {title}", flush=True)
            with pipeline.guard:
                pipeline.ready.pop(ytq.track_id(url), None)
            retry = pipeline.prepare({"id": ytq.track_id(url), "url": url, "title": title}, generation, download=True)
            if retry.get("local"):
                player.play(retry, title, pipeline, generation)
    except Exception as exc:
        print(f"Faixa não reproduzida: {title} ({type(exc).__name__}); próxima faixa.", flush=True)
    finally:
        clear_current(current["token"])
    return True


def main():
    pipeline = ytq.Pipeline()
    with ytq.locked():
        state = ytq.read_state()
        state["current"] = None
        active = state.pop("active_job", None)
        if active and active.get("remaining", 0) > 0:
            active["count"] = active.pop("remaining")
            state.setdefault("jobs", []).insert(0, active)
        state["ready_ids"] = [vid for vid in state.get("ready_ids", []) if pipeline.local_audio(vid)]
        if not state.get("jobs") and state.get("status") in ("buscando", "preparando"):
            state.update(status="interrompido", error="Busca interrompida pelo reinício. Execute play novamente.")
        ytq.save_state(state)
    signal.signal(signal.SIGTERM, lambda *_: pipeline.closed.set())
    player = Player()
    threading.Thread(target=pipeline.worker, daemon=True).start()
    print("Motor Porco CCE ativo: buscas em sequência, até 30 músicas aguardando.", flush=True)
    try:
        while not pipeline.closed.is_set():
            if player.proc.poll() is not None:
                player.close()
                player = Player()
            if not play_next(pipeline, player):
                pipeline.closed.wait(0.1)
    finally:
        player.close()


if __name__ == "__main__":
    main()
