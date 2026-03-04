#!/bin/bash

# --- CONFIGURAÇÃO ---
BASE_DIR="$HOME/porco-music-bot"
SOCKET_PATH="/tmp/porco.sock"
QUEUE_FILE="$BASE_DIR/queue.txt"
RADIO_FILE="$BASE_DIR/radio-atual.txt"

# --- MOTOR ---
function acordar-porco {
    echo -e "\e[1;35m🐷 Acordando o porco...\e[0m"
    
    # Mata processos antigos sem travar
    pkill -9 -f "engine.py" >/dev/null 2>&1 || true
    pkill -9 mpv >/dev/null 2>&1 || true
    
    # Limpa arquivos temporários
    rm -f "$SOCKET_PATH" "$RADIO_FILE"
    touch "$QUEUE_FILE"

    # Inicia o motor desvinculado do terminal
    # Portable way for both Bash and Zsh
    python3 "$BASE_DIR/engine.py" </dev/null >"$BASE_DIR/bot.log" 2>&1 & 
    disown %python3 2>/dev/null || disown $! 2>/dev/null
    
    echo -e "\e[1;32m✅ O chiqueiro está aberto!\e[0m"
}

# --- COMANDOS DE REPRODUÇÃO ---
function play {
    python3 "$BASE_DIR/play.py" "$*"
}

function play-radio-busca {
    python3 "$BASE_DIR/play-radio-busca.py" "$*"
}

function play-radio-genero {
    python3 "$BASE_DIR/play-radio-genero.py" "$*"
}

function proxima {
    # Mata o mpv atual para o motor carregar a próxima
    echo '{"command":["quit"]}' | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo -e "\e[1;34m⏭️  Pulei! Próxima música chegando...\e[0m"
}

function volume {
    [ ! -S "$SOCKET_PATH" ] && { echo "⚠️ Motor desligado."; return; }
    
    local VOL_ATUAL=$(echo '{"command":["get_property","volume"]}' | socat - "$SOCKET_PATH" 2>/dev/null | grep -oP '"data":\K[0-9.]+' | cut -d. -f1)
    : ${VOL_ATUAL:=50}

    local NOVO_VOL=$1

    if [[ "$1" == "+" ]]; then
        NOVO_VOL=$((VOL_ATUAL + 10))
    elif [[ "$1" == "-" ]]; then
        NOVO_VOL=$((VOL_ATUAL - 10))
    elif [[ -z "$1" ]]; then
        echo -e "\e[1;33m📢 Volume: $VOL_ATUAL%\e[0m"
        return
    fi

    [ "$NOVO_VOL" -gt 100 ] && NOVO_VOL=100
    [ "$NOVO_VOL" -lt 0 ] && NOVO_VOL=0

    echo "{\"command\":[\"set_property\",\"volume\",$NOVO_VOL]}" | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo -e "\e[1;32m📢 Volume ajustado: $NOVO_VOL%\e[0m"
}

# --- STATUS MODERNO ---
function tocando {
    [ ! -S "$SOCKET_PATH" ] && { echo -e "\e[1;31m⚠️  Nada tocando agora.\e[0m"; return; }

    local TITLE=$(echo '{"command":["get_property","media-title"]}' | socat - "$SOCKET_PATH" 2>/dev/null | grep -oP '"data":"\K[^"]+')
    
    # Fallback para rádios ou metadados lentos
    if [ -z "$TITLE" ] || [ "$TITLE" == "null" ]; then
        TITLE=$(echo '{"command":["get_property","metadata/by-key/icy-title"]}' | socat - "$SOCKET_PATH" 2>/dev/null | grep -oP '"data":"\K[^"]+')
    fi

    if [ -z "$TITLE" ] || [ "$TITLE" == "null" ]; then
        echo -e "\e[1;33m⏳ Sintonizando metadados...\e[0m"
        return
    fi

    local PER=0
    if [ ! -z "$DUR" ] && [ "$DUR" -gt 0 ]; then
        PER=$((100 * POS / DUR))
    fi

    local BAR_SIZE=20
    local FILLED=$((BAR_SIZE * PER / 100))
    local EMPTY=$((BAR_SIZE - FILLED))
    local BAR=$(printf "%${FILLED}s" | tr ' ' '█')$(printf "%${EMPTY}s" | tr ' ' '░')

    echo -e "\n\e[1;35m🎵 TOCANDO AGORA:\e[0m"
    echo -e "\e[1;37m$TITLE\e[0m"
    
    if [ ! -z "$DUR" ]; then
        printf "\e[1;32m%02d:%02d\e[0m [%s] \e[1;32m%02d:%02d\e[0m (%d%%)\n" $((POS/60)) $((POS%60)) "$BAR" $((DUR/60)) $((DUR%60)) "$PER"
    else
        printf "\e[1;34m📻 No ar há: %02d:%02d:%02d\e[0m [LIVE]\n" $((POS/3600)) $(((POS%3600)/60)) $((POS%60))
    fi
    echo ""
}

function fila {
    echo -e "\e[1;35m📋 PRÓXIMAS NA FILA:\e[0m"
    if [ -s "$QUEUE_FILE" ]; then
        head -n 10 "$QUEUE_FILE" | nl -w2 -s'. '
        local TOTAL=$(wc -l < "$QUEUE_FILE")
        [ "$TOTAL" -gt 10 ] && echo "... e mais $((TOTAL-10)) músicas."
    else
        echo "📭 Fila vazia."
    fi
}

function ajuda {
    echo -e "\e[1;35m"
    echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣶⣶⣶⣶⣦⣤⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
    echo "⠀⠀⢀⡶⢻⡦⢀⣠⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⢀⣴⣾⡿⠀⣠⠀⠀"
    echo "⠀⠠⣬⣷⣾⣡⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣌⣋⣉⣄⠘⠋⠀⠀"
    echo "⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⡄⠀⠀⠀"
    echo "⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣾⣿⣷⣶⡄⠀"
    echo "⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀"
    echo "⠀⠀⠀⠀⠸⣿⣿⣿⠛⠛⠛⠛⠛⠛⠛⠛⠻⠿⣿⣿⡿⠛⠛⠛⠋⠉⠉⠀⠀⠀"
    echo "⠀⠀⠀⠀⠀⢻⣿⣿⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⢻⣿⠃⠸⣿⡇⠀⠀⠀⠀⠀⠀"
    echo "⠀⠀⠀⠀⠀⠈⠿⠇⠀⠀⠀⠻⠇⠀⠀⠀⠀⠀⠈⠿⠀⠀⠻⠿⠀⠀⠀⠀⠀⠀"
    echo -e "\e[0m"
    echo -e "--- \e[1;33mPORCO MUSIC BOT (ARCH)\e[0m ---"
    echo -e "  \e[1;32macordar-porco\e[0m  | Inicia o motor"
    echo -e "  \e[1;32mplay [busca]\e[0m    | Busca (Interativo com FZF)"
    echo -e "  \e[1;32mtocando\e[0m         | Mostra progresso e título"
    echo -e "  \e[1;32mfila\e[0m            | Mostra próximas músicas"
    echo -e "  \e[1;32mproxima\e[0m         | Pula para a próxima"
    echo -e "  \e[1;32mvolume [0-100]\e[0m  | Ajusta som"
    echo -e "  \e[1;32mplay-radio\e[0m      | [busca/genero] Rádios online"
    echo -e "  \e[1;32mwipe\e[0m            | Limpa tudo e reinicia"
    echo -e "  \e[1;32majuda\e[0m           | Esta tela"
}

# --- ALIASES ---
alias porco-help="ajuda"
alias status="tocando"
alias next="proxima"

# --- MANUTENÇÃO ---
function update-git {
    echo -e "\e[1;34m📤 Sincronizando repositórios...\e[0m"
    cd "$BASE_DIR"
    
    # Adicionamos tudo (incluso novos arquivos como o 'subprocess' que o git detectou)
    git add -A
    
    local MSG="${*:-Update Geral $(date +'%d/%m/%Y %H:%M')}"
    if git commit -m "$MSG"; then
        echo -e "\e[1;32m✅ Mudanças commitadas localmente.\e[0m"
    else
        echo -e "\e[1;33mℹ️  Nada novo para commitar.\e[0m"
    fi

    # Tenta empurrar para os remotes que existirem
    for remote in $(git remote); do
        echo -e "\e[1;34m🏠 Enviando para $remote...\e[0m"
        if git push "$remote" main; then
            echo -e "\e[1;32m✅ Sucesso em $remote!\e[0m"
        else
            echo -e "\e[1;31m❌ Falha em $remote. Verifique suas credenciais/token.\e[0m"
        fi
    done
    
    echo -e "\e[1;32m✨ Processo de sincronização finalizado.\e[0m"
}

function update-geral {
    echo -e "\e[1;35m🐷 Atualização Geral (Arch Edition)...\e[0m"
    sudo pacman -Syu yt-dlp mpv socat fzf --noconfirm
    update-git "Update Geral via $(hostname) [Arch]"
}

function wipe {
    echo -e "\e[1;31m🧹 WIPE: Limpando tudo e atualizando comandos...\e[0m"
    # Remove e recria a fila para garantir que não há travas
    rm -f "$QUEUE_FILE"
    
    # Tenta recarregar as funções automaticamente para o usuário não ficar "no passado"
    source "$BASE_DIR/funcoes.sh" 2>/dev/null
    
    acordar-porco
    echo -e "\e[1;32m✨ Comandos atualizados e motor reiniciado!\e[0m"
}
