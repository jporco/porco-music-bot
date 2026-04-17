#!/usr/bin/env python3

from radio_state import get_last_radio, tune_station


def tocar_ultima_radio():
    last = get_last_radio()
    if not last:
        print("📭 Nenhuma última rádio salva ainda.")
        print("💡 Use primeiro: play-radio-busca, play-radio-genero ou play-radio-favoritos")
        return

    ok, message, item = tune_station(last)
    if not ok:
        print(message)
        return

    print(f"🔁 Tocando última rádio: {item['name']}")


if __name__ == "__main__":
    tocar_ultima_radio()
