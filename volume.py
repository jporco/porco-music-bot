#!/usr/bin/env python3
import subprocess, sys, os

SOCKET_PATH = "/tmp/porco.sock"

def set_volume(vol):
    if not os.path.exists(SOCKET_PATH):
        print("⚠️ Off (Motor não iniciado ou sem música tocando)")
        return

    # Comando JSON para o MPV
    cmd = f'{{ "command": ["set_property", "volume", {vol}] }}\n'
    
    try:
        # No Mint/Bash, usamos essa estrutura para garantir a entrega
        proc = subprocess.Popen(['socat', '-', f'UNIX-CONNECT:{SOCKET_PATH}'], 
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        proc.communicate(input=cmd.encode())
        
        if proc.returncode == 0:
            print(f"📢 Vol: {vol}%")
        else:
            print("❌ Erro ao comunicar com o som.")
    except Exception:
        print("❌ Erro: Verifique se o 'socat' está instalado.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        set_volume(sys.argv[1])
