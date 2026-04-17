#!/bin/bash
# --- CONFIGURAÇÃO ---
BASE_DIR="$HOME/porco-music-bot"
SOCKET_PATH="/tmp/porco.sock"
QUEUE_FILE="$BASE_DIR/queue.txt"
RADIO_FILE="$BASE_DIR/radio-atual.txt"
VOL_FILE="$BASE_DIR/volume-atual.txt"

# --- MOTOR ---
acordar-porco() {
    echo "🐷 Acordando o porco em porco-music-bot (Systemd)..."
    systemctl --user restart porco.service
    sleep 1
    echo "✅ O porco está de pé e rodando em background absoluto!"
}

function porco-stop {
    echo "🛑 Parando o Porco Music Bot..."
    systemctl --user stop porco.service >/dev/null 2>&1
    pkill -9 mpv >/dev/null 2>&1
    > "$QUEUE_FILE"
    rm -f "$SOCKET_PATH" "$RADIO_FILE"
    echo "✅ Bot parado e fila limpa. Use 'acordar-porco' para ligar novamente."
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

function play-radio-busca-favoritos {
    python3 "$BASE_DIR/play-radio-busca-favoritos.py" "$*"
}

function play-radio-favoritos {
    python3 "$BASE_DIR/play-radio-favoritos.py" "$*"
}

function play-radio-ultimaradio {
    python3 "$BASE_DIR/play-radio-ultimaradio.py" "$*"
}

function proxima {
    echo '{"command":["quit"]}' | socat - "$SOCKET_PATH" >/dev/null 2>&1
    echo "⏭️ Pulando para a próxima música da fila..."
}

# --- STATUS E EXIBIÇÃO ---
function fila {
    local ROSA="\033[38;5;211m"; local CIANO="\033[36m"; local AMARELO="\033[33m"; local RESET="\033[0m"
    local SOCKET="/tmp/porco.sock"
    local TOCANDO=$(echo '{"command":["get_property","media-title"]}' | socat - "$SOCKET" 2>/dev/null | grep -oP '"data":"\K[^"]+')
    if [ -z "$TOCANDO" ]; then
        [ -f "$RADIO_FILE" ] && TOCANDO="$(cat "$RADIO_FILE")" || TOCANDO="(Silêncio ou carregando...)"
    fi
    echo -e "${ROSA}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${RESET}"
    echo -e "${ROSA}┃${RESET}  🎧 ${AMARELO}${TOCANDO:0:55}${RESET}"
    local POS=$(echo '{ "command": ["get_property", "time-pos"] }' | socat - "$SOCKET" 2>/dev/null | grep -oP '(?<="data":)[0-9.]+' | cut -d. -f1)
    local DUR=$(echo '{ "command": ["get_property", "duration"] }' | socat - "$SOCKET" 2>/dev/null | grep -oP '(?<="data":)[0-9.]+' | cut -d. -f1)
    if [ -n "$POS" ] && [ -n "$DUR" ] && [ "$DUR" -gt 0 ]; then
        local PERCENT=$(( POS * 100 / DUR )); local BARRA_LEN=$((PERCENT/5))
        local BARRA=$(printf "%${BARRA_LEN}s" | tr ' ' '#'); local RESTO_LEN=$((20-BARRA_LEN))
        local RESTO=$(printf "%${RESTO_LEN}s" | tr ' ' '-'); local M_POS=$((POS/60)); local S_POS=$((POS%60))
        local M_DUR=$((DUR/60)); local S_DUR=$((DUR%60))
        echo -e "${ROSA}┃${RESET}  ${CIANO}[${BARRA}${RESTO}] ${PERCENT}% | $(printf "%02d:%02d" $M_POS $S_POS)/$(printf "%02d:%02d" $M_DUR $S_DUR)${RESET}"
    else
        echo -e "${ROSA}┃${RESET}  ${CIANO}[--------------------] 0%${RESET}"
    fi
    echo -e "${ROSA}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${RESET}"
    echo -e "${ROSA}┃${RESET}  📋 FILA PRÓXIMAS:"
    if [ -s "$QUEUE_FILE" ]; then
        grep "|" "$QUEUE_FILE" | head -n 5 | while read -r linha; do
            local TITULO=$(echo "$linha" | cut -d'|' -f1)
            echo -e "${ROSA}┃${RESET}  - ${TITULO:0:55}"
        done
    else
        echo -e "${ROSA}┃${RESET}  (Vazia - Use 'play' para adicionar)"
    fi
    echo -e "${ROSA}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${RESET}"
}

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

function porco-help {
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
    echo -e "--- \e[1;33mPORCO MUSIC BOT (MINT)\e[0m ---"
    echo -e "  \e[1;36mMOTOR\e[0m"
    echo -e "  \e[1;32macordar-porco\e[0m | \e[1;32mporco-stop\e[0m | \e[1;32mwipe\e[0m"
    echo -e ""
    echo -e "  \e[1;36mMÚSICA\e[0m"
    echo -e "  \e[1;32mplay [busca]\e[0m | \e[1;32mproxima\e[0m | \e[1;32mfila\e[0m"
    echo -e ""
    echo -e "  \e[1;36mRÁDIO\e[0m"
    echo -e "  \e[1;32mplay-radio-busca [nome]\e[0m"
    echo -e "  \e[1;32mplay-radio-genero [genero]\e[0m"
    echo -e "  \e[1;32mplay-radio-busca-favoritos [nome]\e[0m"
    echo -e "  \e[1;32mplay-radio-favoritos\e[0m  (número=toca | r N=remove)"
    echo -e "  \e[1;32mplay-radio-ultimaradio\e[0m | \e[1;32mtocando-radio\e[0m"
    echo -e ""
    echo -e "  \e[1;36mÁUDIO\e[0m"
    echo -e "  \e[1;32mvolume [+ / - / 0-100]\e[0m"
    echo -e ""
    echo -e "  \e[1;36mSINCRONIZAÇÃO\e[0m"
    echo -e "  \e[1;32mupdate-git [msg]\e[0m | \e[1;32mupdate-interno [msg]\e[0m | \e[1;32mupdate-geral\e[0m"
    echo -e ""
    echo -e "  \e[1;32mporco-help\e[0m"
}


function volume {
    local VOL_FILE="$BASE_DIR/volume-atual.txt"; local SOCKET_PATH="/tmp/porco.sock"
    local VOL_ATUAL=$(cat "$VOL_FILE" 2>/dev/null); : ${VOL_ATUAL:=80}
    local NOVO_VOL=$1
    if [[ "$1" == "+" ]]; then NOVO_VOL=$((VOL_ATUAL + 5))
    elif [[ "$1" == "-" ]]; then NOVO_VOL=$((VOL_ATUAL - 5))
    elif [[ -z "$1" ]]; then echo "📢 Volume Sincronizado: $VOL_ATUAL%"; return 0; fi
    [ "$NOVO_VOL" -gt 100 ] && NOVO_VOL=100; [ "$NOVO_VOL" -lt 0 ] && NOVO_VOL=0
    echo "$NOVO_VOL" > "$VOL_FILE"
    if [ -S "$SOCKET_PATH" ]; then echo "{\"command\":[\"set_property\",\"volume\",$NOVO_VOL]}" | socat - "$SOCKET_PATH" >/dev/null 2>&1; fi
    pactl set-sink-volume @DEFAULT_SINK@ "${NOVO_VOL}%" >/dev/null 2>&1
    echo 192168 | sudo -S amixer -c 0 set Master "${NOVO_VOL}%" >/dev/null 2>&1
    echo 192168 | sudo -S amixer -c 0 set PCM "${NOVO_VOL}%" >/dev/null 2>&1
    echo "📢 Sincronizado: $NOVO_VOL% (Hardware + Sistema + Bot)"
}

# --- MANUTENÇÃO ---
function update-interno {
    echo "🏠 Sincronizando com Gitea Interno..."
    cd "$BASE_DIR"
    git add -A
    local MSG="${*:-Sync Interno $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG" >/dev/null 2>&1
    git push origin main
    git push interno main
    echo "✅ Sincronização Interna concluída!"
}

function update-git {
    echo "🌐 Sincronizando com GitHub..."
    cd "$BASE_DIR"
    git add -A
    local MSG="${*:-Sync Geral $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG" >/dev/null 2>&1
    git push github main
    echo "🏠 Chamando Sync Interno..."
    update-interno "$MSG"
    echo "✨ Sincronização Geral (GitHub + Gitea) concluída!"
}

function update-geral {
    echo "🐷 Atualização Geral do Porco..."
    if [ -f /etc/arch-release ]; then sudo pacman -Syu yt-dlp mpv socat --noconfirm
    else sudo apt update && sudo apt install yt-dlp mpv socat -y; fi
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
