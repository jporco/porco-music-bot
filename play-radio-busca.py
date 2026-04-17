#!/usr/bin/env python3
import json
import sys
import urllib.request

from radio_state import tune_station


def buscar_radio(termo):
    try:
        url = (
            "https://de1.api.radio-browser.info/json/stations/byname/"
            f"{termo.replace(' ', '%20')}?order=votes&reverse=true&limit=100"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "PorcoBot/1.0"})
        with urllib.request.urlopen(req) as response:
            all_stations = json.loads(response.read().decode())

        if not all_stations:
            print(f"❌ Nenhuma rádio encontrada para: {termo}")
            return

        idx = 0
        passo = 10
        total = len(all_stations)

        while True:
            print(f"\n--- 📻 ESTAÇÕES: {termo.upper()} ({idx + 1} a {min(idx + passo, total)} de {total}) ---")
            pagina = all_stations[idx: idx + passo]
            for i, station in enumerate(pagina, 1):
                country = station.get("countrycode", "??")
                print(f"[{idx + i}] {station['name'][:50]} [{country}]")

            print("-" * 45)
            print("[0] Cancelar")

            msg = "\n👉 Escolha o número"
            if idx + passo < total:
                msg += " | [m] Próxima"
            if idx > 0:
                msg += " | [v] Anterior"
            msg += ": "

            cmd = input(msg).lower().strip()

            if cmd == "m" and idx + passo < total:
                idx += passo
            elif cmd == "v" and idx > 0:
                idx -= passo
            elif cmd == "0":
                break
            elif cmd.isdigit():
                escolha = int(cmd)
                if 1 <= escolha <= total:
                    selected = all_stations[escolha - 1]
                    ok, message, item = tune_station(selected)
                    if not ok:
                        print(message)
                    else:
                        print(f"✅ Sintonizando AGORA: {item['name']}")
                    break
    except Exception as e:
        print(f"❌ Erro na busca: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        buscar_radio(" ".join(sys.argv[1:]))
    else:
        print("💡 Uso: play-radio-busca [nome]")
