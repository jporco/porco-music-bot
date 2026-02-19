#!/usr/bin/env python3
import sys, os, json, urllib.request, time

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
RADIO_ATUAL = os.path.join(BASE_DIR, "radio-atual.txt")
SOCKET_PATH = "/tmp/porco.sock"

def limpar_reproducao_atual():
    """Para o áudio atual e limpa a playlist no MPV de forma silenciosa."""
    # 1. Limpa o arquivo de fila
    with open(QUEUE_FILE, "w") as f:
        f.write("")
    
    # 2. Comando via Socket para o MPV
    if os.path.exists(SOCKET_PATH):
        try:
            # Para e limpa a memória do player sem mostrar JSON na tela
            os.system(f'echo \'{{"command":["stop"]}}\' | socat - {SOCKET_PATH} >/dev/null 2>&1')
            os.system(f'echo \'{{"command":["playlist-clear"]}}\' | socat - {SOCKET_PATH} >/dev/null 2>&1')
            time.sleep(0.5)
        except:
            pass

def buscar_por_genero(genero):
    try:
        # Busca rádios pela tag (gênero) e ordena pelas mais votadas/populares
        url = f"https://de1.api.radio-browser.info/json/stations/bytag/{genero.replace(' ', '%20')}?order=votes&reverse=true&limit=50"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'PorcoBot/1.0'})
        with urllib.request.urlopen(req) as response:
            all_stations = json.loads(response.read().decode())
        
        if not all_stations:
            print(f"❌ Nenhuma rádio encontrada para o gênero: {genero}")
            return

        idx = 0
        passo = 10
        total = len(all_stations)

        while True:
            os.system('clear')
            print(f"--- 🎷 GÊNERO: {genero.upper()} ({idx+1} a {min(idx+passo, total)} de {total}) ---")
            pagina = all_stations[idx : idx + passo]
            
            for i, s in enumerate(pagina, 1):
                tags = s.get('tags', '')[:30]
                print(f"[{idx + i}] {s['name'][:40]} | {tags}...")

            print("-" * 45)
            print("[0] Cancelar")
            msg = "\n👉 Escolha o número"
            if idx + passo < total: msg += " | [m] Mais"
            if idx > 0: msg += " | [v] Voltar"
            msg += ": "
            
            cmd = input(msg).lower().strip()

            if cmd == 'm' and idx + passo < total:
                idx += passo
            elif cmd == 'v' and idx > 0:
                idx -= passo
            elif cmd == '0':
                break
            elif cmd.isdigit():
                escolha = int(cmd)
                if 1 <= escolha <= total:
                    sel = all_stations[escolha - 1]
                    
                    print(f"\n🧹 Faxina na playlist... (Prioridade Gênero)")
                    limpar_reproducao_atual()
                    
                    # Salva na fila
                    with open(QUEUE_FILE, "w") as f:
                        f.write(f"📻 RADIO: {sel['name']} | {sel['url_resolved']}\n")
                    
                    # Salva o nome para o status
                    with open(RADIO_ATUAL, "w") as f:
                        f.write(sel['name'] + "\n")
                        
                    print(f"✅ Tocando {genero}: {sel['name']}")
                    break
    except Exception as e:
        print(f"❌ Erro na busca: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        buscar_por_genero(" ".join(sys.argv[1:]))
    else:
        print("💡 Uso: play-radio-genero [rock, jazz, pop...]")