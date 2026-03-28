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

function tocando-radio {
    local S="/tmp/porco.sock"
    
    # 1. Verifica se o motor está rodando
    if [ ! -S "$S" ]; then
        echo "⚠️ Off (O motor não está tocando rádio agora)"
        return
    fi

    echo -e "\n📻 --- STATUS DA RÁDIO ---"
    
    # 2. Busca o nome da rádio que salvamos no queue.txt
    # O play-radio-busca salva como: 📻 RADIO: Nome | URL
    local NOME_RADIO=$(grep "RADIO:" ~/porco-music-bot/queue.txt | cut -d'|' -f1 | sed 's/📻 RADIO: //')
    
    if [ -z "$NOME_RADIO" ]; then
        echo "🎶 Sintonizando estação..."
    else
        echo "📡 Estação: $NOME_RADIO"
    fi

    # 3. Pega o tempo de transmissão direto do MPV
    local C_RAW=$(echo '{"command":["get_property","time-pos"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+')
    
    if [ ! -z "$C_RAW" ]; then
        local C=$(echo "$C_RAW" | cut -d. -f1)
        printf "⏱️  No ar há: %02d:%02d:%02d\n" $((C/3600)) $(((C%3600)/60)) $((C%60))
    fi
    echo -e "---------------------------\n"
}

function tocando-radio {
    local S="/tmp/porco.sock"
    
    # 1. Verifica se o motor está rodando
    if [ ! -S "$S" ]; then
        echo "⚠️ Off (O motor não está tocando rádio agora)"
        return
    fi

    echo -e "\n📻 --- STATUS DA RÁDIO ---"
    
    # 2. Busca o nome da rádio que salvamos no queue.txt
    # O play-radio-busca salva como: 📻 RADIO: Nome | URL
    local NOME_RADIO=$(grep "RADIO:" ~/porco-music-bot/queue.txt | cut -d'|' -f1 | sed 's/📻 RADIO: //')
    
    if [ -z "$NOME_RADIO" ]; then
        echo "🎶 Sintonizando estação..."
    else
        echo "📡 Estação: $NOME_RADIO"
    fi

    # 3. Pega o tempo de transmissão direto do MPV
    local C_RAW=$(echo '{"command":["get_property","time-pos"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+')
    
    if [ ! -z "$C_RAW" ]; then
        local C=$(echo "$C_RAW" | cut -d. -f1)
        printf "⏱️  No ar há: %02d:%02d:%02d\n" $((C/3600)) $(((C%3600)/60)) $((C%60))
    fi
    echo -e "---------------------------\n"
}

function update-geral {
    echo "🐷 Iniciando atualização geral do ecossistema Porco..."
    
    # 1. Atualiza repositórios do sistema
    echo "📦 [1/5] Atualizando repositórios do Linux Mint..."
    sudo apt update -y
    
    # 2. Instala/Atualiza dependências essenciais
    echo "🛠️ [2/5] Garantindo dependências (mpv, socat, python3)..."
    sudo apt install mpv socat python3 python3-pip -y
    
    # 3. Atualiza o yt-dlp (O mais importante para o YouTube não travar)
    echo "🎥 [3/5] Atualizando yt-dlp para a versão mais recente..."
    sudo python3 -m pip install -U yt-dlp
    
    # 4. Sincroniza o código do bot (Interno e Sistema)
    echo "🔄 [4/5] Rodando update-interno e reparando links..."
    update-interno "Update Geral: Sistema e Dependências"
    
    # 5. Limpeza de cache do yt-dlp
    echo "🧹 [5/5] Limpando cache de busca..."
    yt-dlp --rm-cache-dir >/dev/null 2>&1
    
    echo "✨ Sistema e Bot estão 100% atualizados!"
}

function update-git {
    echo "📤 Enviando atualizações para o Git (GitHub/Gitea)..."
    cd ~/porco-music-bot
    
    # Adiciona as mudanças
    git add .
    
    # Define a mensagem do commit
    local MSG="${*:-Update Geral $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG"
    
    # Tenta enviar para o origin (Gitea/GitHub)
    git push origin main
    
    echo "✅ Git atualizado com sucesso!"
}
