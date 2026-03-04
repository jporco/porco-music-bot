#!/usr/bin/env python3
import subprocess, sys, os, json, urllib.request, time

QUEUE_FILE = os.path.expanduser("~/porco-music-bot/queue.txt")

def buscar_radio(termo):
    try:
        url = f"https://de1.api.radio-browser.info/json/stations/byname/{termo.replace(' ', '%20')}"
        with urllib.request.urlopen(url) as response:
            all_stations = json.loads(response.read().decode())
        
        if not all_stations:
            print("❌ Nenhuma rádio encontrada.")
            return

        idx = 0
        passo = 10

        while True:
            os.system('clear')
            print(f"--- 📻 ESTAÇÕES ENCONTRADAS (Pág: {(idx//passo)+1}) ---")
            pagina = all_stations[idx : idx + passo]
            
            for i, s in enumerate(pagina, 1):
                print(f"[{idx + i}] {s['name'][:50]} [{s['countrycode']}]")

            print("-" * 30)
            print("[0] Cancelar")
            msg = "\n👉 Digite o número"
            if idx + passo < len(all_stations): msg += " | [m] Próxima"
            if idx > 0: msg += " | [v] Anterior"
            msg += ": "
            
            cmd = input(msg).lower().strip()

            if cmd == 'm' and idx + passo < len(all_stations):
                idx += passo
            elif cmd == 'v' and idx > 0:
                idx -= passo
            elif cmd == '0':
                break
            elif cmd.isdigit():
                escolha = int(cmd)
                if 1 <= escolha <= len(all_stations):
                    sel = all_stations[escolha - 1]
                    with open(QUEUE_FILE, "w") as f:
                        f.write(f"📻 RADIO: {sel['name']} | {sel['url_resolved']}\n")
                    print(f"\n✅ Tocando: {sel['name']}")
                    break
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        buscar_radio(" ".join(sys.argv[1:]))
