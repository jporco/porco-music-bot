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

function proxima {
    echo '{"command":["playlist-next"]}' | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo "⏭️  Pulando para a próxima..."
}

function volume {
    [ ! -S "$SOCKET_PATH" ] && { echo "⚠️ Off"; return; }
    echo "{\"command\":[\"set_property\",\"volume\",$1]}" | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo "📢 Vol: $1%"
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
        printf "⏱️  No ar há: %02d:%02d:%02d\n" $((C/3600)) $(((C%3600)/60)) $((C%60))
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
    echo -e "--- \e[1;33mPORCO MUSIC BOT\e[0m ---"
    echo -e "  \e[1;32macordar-porco\e[0m | \e[1;32mwipe\e[0m"
    echo -e "  \e[1;32mplay [busca]\e[0m | \e[1;32mplay-radio-busca\e[0m"
    echo -e "  \e[1;32mvolume [0-100]\e[0m | \e[1;32mtocando-radio\e[0m"
    echo -e "  \e[1;32mupdate-geral\e[0m | \e[1;32mupdate-git\e[0m"
}

# --- MANUTENÇÃO ---
function update-git {
    echo "📤 Enviando para o Git..."
    cd "$BASE_DIR"
    git add .
    local MSG="${*:-Update Geral $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG"
    git push origin main
    echo "✅ Git atualizado!"
}

function update-geral {
    echo "🐷 Atualização Geral..."
    if [ -f /etc/arch-release ]; then
        sudo pacman -Syu yt-dlp mpv socat --noconfirm
    else
        sudo apt update && sudo apt install yt-dlp mpv socat -y
    fi
    update-git "Update Geral via $(hostname)"
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
