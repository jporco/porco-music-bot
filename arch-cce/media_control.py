#!/usr/bin/env python3
"""Control the Spotify Connect receiver or the local Porco player."""
import json
import subprocess
import sys

PREFIX = "org.mpris.MediaPlayer2.spotifyd"
PATH = "/org/mpris/MediaPlayer2"
PLAYER = "org.mpris.MediaPlayer2.Player"
METHODS = {
    "pause": ("Pause", "CanPause", "Pausado"),
    "play": ("Play", "CanPlay", "Retomado"),
    "proxima": ("Next", "CanGoNext", "Próxima faixa solicitada"),
    "anterior": ("Previous", "CanGoPrevious", "Faixa anterior solicitada"),
}


def bus(*args):
    result = subprocess.run(
        ["busctl", "--user", "--no-pager", "--timeout=2s", *args],
        capture_output=True, text=True, timeout=3, check=True,
    )
    return result.stdout


def property_values(name, *properties):
    output = bus("--json=short", "get-property", name, PATH, PLAYER, *properties)
    return [json.loads(line)["data"] for line in output.splitlines()]


def spotify():
    try:
        names = bus("--no-legend", "list").splitlines()
        for line in names:
            name = line.split()[0]
            if name == PREFIX or name.startswith(PREFIX + "."):
                status, metadata = property_values(name, "PlaybackStatus", "Metadata")
                if status != "Stopped":
                    return name, status, metadata
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        pass
    return None


def selected(mpv_active):
    current = spotify()
    if current and (current[1] == "Playing" or not mpv_active):
        return current
    return None


def spotify_command(name, action):
    method, capability, message = METHODS[action]
    if property_values(name, "CanControl", capability) != [True, True]:
        raise RuntimeError("Spotify não disponibilizou esse comando nesta sessão.")
    bus("call", name, PATH, PLAYER, method)
    return message


def control(action):
    import youtube_queue as queue

    idle = queue.ipc(["get_property", "idle-active"])
    active = bool(idle and idle.get("data") is False)
    remote = selected(active)
    if remote:
        print(f"Spotify | {spotify_command(remote[0], action)}.")
        return
    if not active:
        if action == "proxima" and queue.read_queue():
            print("Porco | Aguardando a próxima faixa carregar.")
            return
        raise RuntimeError("Nenhuma reprodução ativa. Use play [busca] ou selecione o CCE no Spotify.")
    if action in ("play", "pause"):
        answer = queue.ipc(["set_property", "pause", action == "pause"])
        message = METHODS[action][2]
    else:
        with queue.locked():
            state = queue.read_state()
            lines = queue.read_queue()
            if action == "anterior":
                history = state.get("history", [])
                current = state.get("current") or {}
                if not current.get("id") or not history:
                    raise RuntimeError("Ainda não há uma faixa anterior na sessão do YouTube.")
                if queue.reserved(state) >= queue.MAX_TRACKS:
                    raise RuntimeError("Fila cheia. Libere uma posição para voltar à faixa anterior.")
                answer = queue.ipc(["stop"])
                if not answer or answer.get("error") != "success":
                    raise RuntimeError("O Porco não confirmou o comando.")
                queue.write_queue([history.pop(), current["line"], *lines])
                state["last_track"] = None
                queue.save_state(state)
            else:
                if not lines:
                    if state.get("active_job") or state.get("jobs"):
                        raise RuntimeError("A próxima faixa ainda está em preparação. Acompanhe com fila.")
                    raise RuntimeError("Não há próxima faixa na fila.")
                answer = queue.ipc(["stop"])
        message = METHODS[action][2]
    if not answer or answer.get("error") != "success":
        raise RuntimeError("O Porco não confirmou o comando.")
    print(f"Porco | {message}.")


def main():
    args = sys.argv[1:]
    if len(args) != 1 or args[0] not in METHODS:
        print("Uso: play | pause | próximo | anterior", file=sys.stderr)
        return 2
    try:
        control(args[0])
    except (RuntimeError, OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        message = str(error) if isinstance(error, RuntimeError) else "Não consegui enviar o comando ao player."
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
