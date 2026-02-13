#!/usr/bin/env python3
import sys, os, json, urllib.request

QUEUE_FILE = os.path.expanduser("~/porco-music-bot/queue.txt")
RADIO_ATUAL = os.path.expanduser("~/porco-music-bot/radio-atual.txt")

def buscar_por_genero(genero):
    try:
        # Busca rádios pela tag (gênero) e ordena pelas mais votadas/populares
        url = f"https://de1.api.radio-browser.info/json/stations/bytag/{genero.replace(' ', '%20')}?order=votes&reverse=true&limit=50"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'PorcoBot/1.0'})
        with urllib.request.urlopen(req) as response:
            all_stations = json.loads(response.read().decode())
        
        if not all_stations:
            print(f"❌ Nenhum rádio encontrada para o gênero: {genero}")
            return

        idx = 0
        passo = 10

        while True:
            os.system('clear')
            print(f"--- 🎷 GÊNERO: {genero.upper()} (Pág: {(idx//passo)+1}) ---")
            pagina = all_stations[idx : idx + passo]
            
            for i, s in enumerate(pagina, 1):
                # Mostra o nome e um pouco das tags para confirmar o estilo
                tags = s.get('tags', '')[:30]
                print(f"[{idx + i}] {s['name'][:40]} | {tags}...")

            print("-" * 30)
            print("[0] Cancelar")
            msg = "\n👉 Escolha o número"
            if idx + passo < len(all_stations): msg += " | [m] Mais"
            if idx > 0: msg += " | [v] Voltar"
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
                    
                    # Salva na fila
                    with open(QUEUE_FILE, "w") as f:
                        f.write(f"📻 RADIO: {sel['name']} | {sel['url_resolved']}\n")
                    
                    # Salva o nome para o status
                    with open(RADIO_ATUAL, "w") as f:
                        f.write(sel['name'] + "\n")
                        
                    print(f"\n✅ Tocando {genero}: {sel['name']}")
                    break
    except Exception as e:
        print(f"❌ Erro na busca: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        buscar_por_genero(" ".join(sys.argv[1:]))
    else:
        print("💡 Uso: play-radio-genero [rock, jazz, pop...]")
