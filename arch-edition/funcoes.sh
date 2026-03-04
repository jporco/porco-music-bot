#!/bin/bash

# --- CONFIGURAÇÃO ---
BASE_DIR="$HOME/porco-music-bot"
SOCKET_PATH="/tmp/porco.sock"
QUEUE_FILE="$BASE_DIR/queue.txt"
RADIO_FILE="$BASE_DIR/radio-atual.txt"

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
    echo '{"command":["playlist-next"]}' | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo "⏭️ Pulando para a próxima..."
}

function volume {
    [ ! -S "$SOCKET_PATH" ] && { echo "⚠️ Off"; return; }
    
    local VOL_ATUAL=$(echo '{"command":["get_property","volume"]}' | socat - "$SOCKET_PATH" 2>/dev/null | grep -oP '"data":\K[0-9.]+' | cut -d. -f1)
    : ${VOL_ATUAL:=50}

    local NOVO_VOL=$1

    if [[ "$1" == "+" ]]; then
        NOVO_VOL=$((VOL_ATUAL + 10))
    elif [[ "$1" == "-" ]]; then
        NOVO_VOL=$((VOL_ATUAL - 10))
    elif [[ -z "$1" ]]; then
        echo "📢 Volume atual: $VOL_ATUAL%"
        return
    fi

    [ "$NOVO_VOL" -gt 100 ] && NOVO_VOL=100
    [ "$NOVO_VOL" -lt 0 ] && NOVO_VOL=0

    echo "{\"command\":[\"set_property\",\"volume\",$NOVO_VOL]}" | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo "📢 Vol: $NOVO_VOL%"
}

# --- STATUS E EXIBIÇÃO ---
function tocando-radio {
    [ ! -S "$SOCKET_PATH" ] && { echo "⚠️ Off"; return; }
    echo -e "\n📻 --- STATUS DA RÁDIO ---"
    if [ -f "$RADIO_FILE" ]; then
        echo "📡 Estação: $(cat "$RADIO_FILE")"
    else
        echo "📡 Estação: Sintonizando..."
    fi
    local C_RAW=$(echo '{"command":["get_property","time-pos"]}' | socat - "$SOCKET_PATH" 2>/dev/null | grep -oP '"data":\K[0-9.]+')
    if [ ! -z "$C_RAW" ]; then
        local C=$(echo "$C_RAW" | cut -d. -f1)
        printf "⏱️ No ar há: %02d:%02d:%02d\n" $((C/3600)) $(((C%3600)/60)) $((C%60))
    fi
    echo -e "---------------------------\n"
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
    echo -e "  \e[1;32macordar-porco\e[0m | \e[1;32mwipe\e[0m"
    echo -e "  \e[1;32mplay [busca]\e[0m | \e[1;32mplay-radio-busca\e[0m"
    echo -e "  \e[1;32mplay-radio-genero [rock, jazz...]\e[0m"
    echo -e "  \e[1;32mvolume [+ / - / 0-100]\e[0m | \e[1;32mtocando-radio\e[0m"
    echo -e "  \e[1;32mupdate-geral\e[0m | \e[1;32mupdate-git\e[0m"
}

# --- MANUTENÇÃO ---
function update-git {
    echo "📤 Sincronizando Gitea e GitHub..."
    cd "$BASE_DIR"
    git add -A
    local MSG="${*:-Update Geral $(date +'%d/%m/%Y %H:%M')}"
    if git commit -m "$MSG"; then
        echo "✅ Mudanças registradas."
    else
        echo "ℹ️ Nada novo para commitar."
    fi
    echo "🏠 Enviando para o Gitea (origin)..."
    git push origin main
    echo "🌐 Enviando para o GitHub (github)..."
    git push github main
    echo "✨ Sincronização concluída com sucesso!"
}

function update-geral {
    echo "🐷 Atualização Geral do Porco (Arch Edition)..."
    # No Arch, o yt-dlp e o mpv estão nos repositórios oficiais
    sudo pacman -Syu yt-dlp mpv socat --noconfirm
    update-git "Update Geral via $(hostname) [Arch]"
}

function wipe {
    echo "🧹 WIPE: Faxina total iniciada..."
    pkill -9 -f engine.py >/dev/null 2>&1
    pkill -9 mpv >/dev/null 2>&1
    > "$QUEUE_FILE"
    rm -f "$SOCKET_PATH" "$RADIO_FILE"
    acordar-porco
    echo "🚀 Bot reiniciado e limpo!"
}
