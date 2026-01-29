import sys, subprocess, os

QUEUE_FILE = "/home/zabbix/porco-bot/queue.txt"

def format_time(seconds_str):
    try:
        seconds = int(float(seconds_str))
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"
    except:
        return "00:00"

def play():
    args = sys.argv[1:]
    if not args: return
    busca = " ".join(args)
    
    # Adicionamos "songs" ou "playlist" na busca interna para forçar variedade
    print(f"🐷 Buscando mix variado para: {busca}...")

    try:
        # Buscamos 40 resultados para ter de onde filtrar e evitar repetidas
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(title)s|%(duration)s",
            "--match-filter", "duration <= 600 & !is_live",
            f"ytsearch40:{busca} songs"
        ]
        
        processo = subprocess.run(cmd, capture_output=True, text=True)
        linhas = [l.strip() for l in processo.stdout.split('\n') if l.strip()]
        
        resultados = []
        titulos_vistos = set()

        for r in linhas:
            if "|" in r:
                partes = r.split("|")
                titulo = partes[0]
                segundos_raw = partes[1]
                
                # Normaliza o título para evitar versões quase iguais (Live, Remaster, etc)
                # Pega apenas as primeiras 15 letras para comparar se é a mesma música
                simplificado = titulo.lower()[:15]
                
                if simplificado not in titulos_vistos and "24/7" not in titulo.upper():
                    tempo = format_time(segundos_raw)
                    resultados.append(f"[{tempo}] {titulo}")
                    titulos_vistos.add(simplificado)
            
            # Quando atingir 10 músicas diferentes, para.
            if len(resultados) >= 10:
                break

        if not resultados:
            print("❌ Nenhuma música variada encontrada.")
            return

        with open(QUEUE_FILE, "a") as f:
            for m in resultados:
                f.write(m + "\n")
        
        print(f"✅ Adicionadas {len(resultados)} músicas diferentes à fila!")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    play()
