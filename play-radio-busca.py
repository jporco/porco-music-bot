#!/usr/bin/env python3
import subprocess, sys, os, json, urllib.request, time

BASE_DIR = os.path.expanduser("~/porco-music-bot")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.txt")
RADIO_ATUAL = os.path.join(BASE_DIR, "radio-atual.txt")
SOCKET_PATH = "/tmp/porco.sock"

def limpar_reproducao_atual():
    """Limpa a fila e para o que estiver tocando agora para dar prioridade à rádio."""
    # 1. Limpa o arquivo de fila fisicamente
    with open(QUEUE_FILE, "w") as f:
        f.write("")
    
    # 2. Envia comandos silenciosos para o MPV via socket
    if os.path.exists(SOCKET_PATH):
        try:
            # 'stop' para o áudio e 'playlist-clear' limpa a memória do player
            # Redirecionamos a saída para /dev/null para não aparecer JSON no terminal
            os.system(f'echo \'{{"command":["stop"]}}\' | socat - {SOCKET_PATH} >/dev/null 2>&1')
            os.system(f'echo \'{{"command":["playlist-clear"]}}\' | socat - {SOCKET_PATH} >/dev/null 2>&1')
            # Pequena pausa para o motor respirar
            time.sleep(0.5)
        except:
            pass

def buscar_radio(termo):
    try:
        # Busca otimizada: 100 resultados ordenados por votos
        url = f"https://de1.api.radio-browser.info/json/stations/byname/{termo.replace(' ', '%20')}?order=votes&reverse=true&limit=100"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'PorcoBot/1.0'})
        with urllib.request.urlopen(req) as response:
            all_stations = json.loads(response.read().decode())
        
        if not all_stations:
            print(f"❌ Nenhuma rádio encontrada para: {termo}")
            return

        idx = 0
        passo = 10
        total = len(all_stations)

        while True:
            os.system('clear')
            print(f"--- 📻 ESTAÇÕES: {termo.upper()} ({idx+1} a {min(idx+passo, total)} de {total}) ---")
            
            pagina = all_stations[idx : idx + passo]
            for i, s in enumerate(pagina, 1):
                print(f"[{idx + i}] {s['name'][:50]} [{s.get('countrycode', '??')}]")

            print("-" * 45)
            print("[0] Cancelar")
            
            msg = "\n👉 Escolha o número"
            if idx + passo < total: msg += " | [m] Próxima"
            if idx > 0: msg += " | [v] Anterior"
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
                    
                    print(f"\n🧹 Faxina na playlist... (Prioridade Máxima)")
                    limpar_reproducao_atual()
                    
                    # Salva a nova rádio
                    with open(QUEUE_FILE, "w") as f:
                        f.write(f"📻 RADIO: {sel['name']} | {sel['url_resolved']}\n")
                    
                    with open(RADIO_ATUAL, "w") as f:
                        f.write(sel['name'] + "\n")
                        
                    print(f"✅ Sintonizando AGORA: {sel['name']}")
                    break
    except Exception as e:
        print(f"❌ Erro na busca: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        buscar_radio(" ".join(sys.argv[1:]))
    else:
        print("💡 Uso: play-radio-busca [nome]")