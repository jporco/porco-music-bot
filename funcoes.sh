#!/bin/bash

# --- CONFIGURAÇÃO ---
BASE_DIR="$HOME/porco-music-bot"
SOCKET_PATH="/tmp/porco.sock"

# --- MOTOR ---
acordar-porco() {
    echo "🐷 Acordando o porco em porco-music-bot..."
    pkill -9 -f engine.py >/dev/null 2>&1
    pkill -9 mpv >/dev/null 2>&1
    rm -f "$SOCKET_PATH"
    # CORREÇÃO: Caminho para a pasta correta
    python3 "$BASE_DIR/engine.py" > "$BASE_DIR/bot.log" 2>&1 &
    sleep 1
    echo "✅ O porco está de pé!"
}

# --- FUNÇÕES DE COMANDO ---
function play {
    python3 "$BASE_DIR/play.py" "$*"
}

function volume {
    [ ! -S "$SOCKET_PATH" ] && { echo "⚠️ Off"; return; }
    echo "{\"command\":[\"set_property\",\"volume\",$1]}" | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo "📢 Vol: $1%"
}

# --- OUTROS ---
function update-interno {
    echo "📤 Enviando para o Gitea Interno..."
    cd ~/porco-music-bot
    
    # Adiciona tudo da pasta atual
    git add .
    
    # Faz o commit com data/hora se não passar mensagem
    local MSG="${*:-Update Interno $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG"
    
    # Envia para o servidor interno (Gitea)
    # Se o nome do seu remote não for 'origin' no interno, mude abaixo
    git push origin main
    
    # Atualiza os links do sistema para garantir que rodem desta pasta
    echo "🔄 Sincronizando comandos no sistema..."
    sudo ln -sf ~/porco-music-bot/engine.py /usr/local/bin/acordar-porco
    sudo ln -sf ~/porco-music-bot/play.py /usr/local/bin/play
    sudo ln -sf ~/porco-music-bot/play-radio-busca.py /usr/local/bin/play-radio-busca
    sudo ln -sf ~/porco-music-bot/volume.py /usr/local/bin/volume
    
    echo "✅ Gitea e Sistema atualizados!"
}

function wipe {
    echo "🧹 WIPE: Faxina total iniciada..."
    # Mata todos os processos relacionados
    pkill -9 -f engine.py >/dev/null 2>&1
    pkill -9 mpv >/dev/null 2>&1
    
    # Limpa arquivos temporários e fila
    > ~/porco-music-bot/queue.txt
    rm -f /tmp/porco.sock
    rm -f ~/porco-music-bot/bot.log
    
    echo "✨ Fila limpa e processos encerrados."
    
    # Reinicia o motor automaticamente
    acordar-porco
    echo "🚀 Bot reiniciado e pronto para outra!"
}
