#!/usr/bin/env python3
import shlex
import sys
from pathlib import Path
from difflib import SequenceMatcher

COMMANDS = [
    (("radio", "busca", "favoritos"), "play-radio-busca-favoritos"),
    (("radio", "busca"), "play-radio-busca"),
    (("radio", "genero"), "play-radio-genero"),
    (("radio", "pais"), "play-radio-pais"),
    (("radio", "favoritos"), "play-radio-favoritos"),
    (("radio", "ultimaradio"), "play-radio-ultimaradio"),
    (("radio", "ultima"), "play-radio-ultimaradio"),
    (("radio", "tocando"), "tocando-radio"),
    (("play", "artista"), "play-artista"),
    (("playlist", "loop"), "playlist-loop"),
    (("ajuda",), "__help__"),
    (("help",), "__help__"),
    (("comandos",), "__help__"),
    (("acorda",), "acordar-porco"),
    (("para",), "porco-stop"),
    (("stop",), "porco-stop"),
    (("reseta",), "wipe"),
    (("wipe",), "wipe"),
    (("f5telas",), "f5telas"),
    (("f5",), "f5telas"),
    (("play",), "play"),
    (("loop",), "playlist-loop"),
    (("proxima",), "proxima"),
    (("proximo",), "proxima"),
    (("próxima",), "proxima"),
    (("próximo",), "proxima"),
    (("anterior",), "anterior"),
    (("pause",), "pause"),
    (("volume", "padrão"), "volume-padrao"),
    (("mais",), "mais"),
    (("fila",), "fila"),
    (("tocando",), "fila"),
    (("volume",), "volume"),
    (("volume", "padrao"), "volume-padrao"),
    (("mute",), "mute"),
    (("desmute",), "desmute"),
]
COMMANDS.sort(key=lambda item: (-len(item[0]), item[0]))

HELP = """Porco Music Bot | SSH no Arch-CCE
  porco abre o terminal interativo (ajuda | sair)

REPRODUÇÃO
  pause | play                Pausa ou retoma Spotify, YouTube ou rádio
  proximo | proxima | anterior Navega no Spotify ou nas músicas do YouTube
  fila | porco tocando        Mostra o que está tocando e a fila do Porco

YOUTUBE
  play [busca ou link]        Adiciona até 5 faixas em segundo plano
  play-artista [nome]         Busca músicas do artista
  mais [busca opcional]       Adiciona até 2; fila de até 30 faixas aguardando
  playlist-loop [busca|off]   Repõe faixas automaticamente

RÁDIO
  play-radio-busca [nome] | play-radio-genero [gênero]
  play-radio-pais [país] [filtro]
  play-radio-busca-favoritos [nome] | play-radio-favoritos
  play-radio-ultimaradio | tocando-radio

ÁUDIO
  volume [0-100|+|-|atual] | volume-padrao [1-100]
  mute | desmute

MOTOR
  acordar-porco | porco-stop | wipe | f5telas

Exemplos no modo porco
  porco play soad | porco pause | porco proximo | porco radio favoritos
"""


def take_words(tokens, n):
    words, rest = [], list(tokens)
    while len(words) < n:
        if not rest:
            return None, tokens
        parts = [p for p in rest.pop(0).split("-") if p]
        if not parts:
            continue
        need = n - len(words)
        words.extend(p.lower() for p in parts[:need])
        leftover = parts[need:]
        if leftover:
            rest.insert(0, "-".join(leftover))
    return words, rest


def flatten(tokens):
    out = []
    for t in tokens:
        out.extend(p.lower() for p in str(t).replace("-", " ").split() if p)
    return out


def phrases():
    seen, out = set(), []
    for key, _fn in COMMANDS:
        p = " ".join(key)
        if p in ("proximo", "próxima", "próximo"):
            continue
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def score_phrase(typed, phrase):
    ptoks = phrase.split()
    r = SequenceMatcher(None, " ".join(typed), phrase).ratio()
    if not ptoks:
        return r
    head, last = ptoks[:-1], ptoks[-1]
    if typed[: len(head)] != head:
        return r
    if len(typed) >= len(ptoks):
        last_r = SequenceMatcher(None, typed[len(head)], last).ratio()
        return max(r, last_r * 0.85 + 0.15)
    if len(typed) == len(head):
        return max(r, 0.62)
    return r


def suggest(tokens, cutoff=0.68):
    typed = flatten(tokens)
    if not typed:
        return ""
    ranked = sorted(
        ((score_phrase(typed, p), -len(p.split()), p) for p in phrases()),
        reverse=True,
    )
    if ranked and ranked[0][0] >= cutoff:
        return ranked[0][2]
    return ""


def resolve(tokens):
    tokens = [t for t in tokens if t]
    while tokens and tokens[0].lower() == "porco":
        tokens = tokens[1:]
    if not tokens:
        return None, []
    for key, fn in COMMANDS:
        words, rest = take_words(tokens, len(key))
        if words == list(key):
            return fn, rest
    return None, tokens


def parse_argv(argv):
    if argv and argv[0] == "--line":
        return shlex.split(argv[1] if len(argv) > 1 else "")
    return list(argv)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--help"]:
        sys.stdout.write(HELP)
        return 0
    try:
        tokens = parse_argv(argv)
    except ValueError:
        print("Verifique se as aspas do comando estão fechadas.", file=sys.stderr)
        return 2
    fn, args = resolve(tokens)
    if not fn:
        hit = suggest(args or tokens)
        if hit:
            print("fail: cmd", file=sys.stderr)
            print(f"quis dizer: {hit}", file=sys.stderr)
        else:
            print("fail: comando nao existe", file=sys.stderr)
        return 2
    audio_commands = {'volume': 'volume', 'volume-padrao': 'default', 'mute': 'mute', 'desmute': 'unmute'}
    if fn in audio_commands:
        # Tambem atualiza REPLs antigos: o despacho usa arquivo externo,
        # sem executar a funcao de volume que ficou carregada no shell.
        sys.stdout.write(str(Path(__file__).resolve().parent / 'audio-volume.sh') + '\n')
        sys.stdout.write(audio_commands[fn] + '\n')
    elif fn in ("pause", "proxima", "anterior") or (fn == "play" and not args):
        sys.stdout.write(sys.executable + "\n")
        sys.stdout.write(str(Path(__file__).resolve().parent / "media_control.py") + "\n")
        sys.stdout.write(fn + "\n")
    elif fn in ("play", "play-artista"):
        script = Path(__file__).resolve().parent / (fn + ".py")
        sys.stdout.write(sys.executable + "\n" + str(script) + "\n")
    else:
        sys.stdout.write(fn + "\n")
    for a in args:
        sys.stdout.write(a + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
