#!/bin/bash
# --- CONFIGURAÇÃO (Arch edition: Python em arch-edition/, dados em ~/porco-music-bot) ---
BASE_DIR="$HOME/porco-music-bot"
ARCH_PY="$HOME/porco-music-bot/arch-edition"
SOCKET_PATH="/tmp/porco.sock"
QUEUE_FILE="$BASE_DIR/queue.txt"
RADIO_FILE="$BASE_DIR/radio-atual.txt"
VOL_FILE="$BASE_DIR/volume-atual.txt"

_porco_arch_links() {
    sudo ln -sf "$ARCH_PY/engine.py" /usr/local/bin/acordar-porco
    sudo ln -sf "$ARCH_PY/play.py" /usr/local/bin/play
    sudo ln -sf "$ARCH_PY/volume.py" /usr/local/bin/volume
}

# --- MOTOR ---
acordar-porco() {
    echo "🐷 Acordando o porco (Arch edition, systemd --user)..."
    systemctl --user restart porco.service
    sleep 1
    echo "✅ O porco está de pé e rodando em background."
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
    python3 "$ARCH_PY/play.py" "$*"
}

function play-radio-busca {
    python3 "$ARCH_PY/play-radio-busca.py" "$*"
}

function play-radio-genero {
    python3 "$ARCH_PY/play-radio-genero.py" "$*"
}

function play-radio-busca-favoritos {
    python3 "$ARCH_PY/play-radio-busca-favoritos.py" "$*"
}

function play-radio-favoritos {
    python3 "$ARCH_PY/play-radio-favoritos.py" "$*"
}

function favoritos {
    python3 "$ARCH_PY/play-radio-favoritos.py" "$*"
}

function play-radio-ultimaradio {
    python3 "$ARCH_PY/play-radio-ultimaradio.py" "$*"
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

function tocando {
    fila
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
    echo -e "--- \e[1;33mPORCO MUSIC BOT (ARCH EDITION)\e[0m ---"
    echo -e "  \e[1;36mMOTOR\e[0m"
    echo -e "  \e[1;32macordar-porco\e[0m | \e[1;32mporco-stop\e[0m | \e[1;32mwipe\e[0m"
    echo -e ""
    echo -e "  \e[1;36mMÚSICA\e[0m"
    echo -e "  \e[1;32mplay [busca]\e[0m | \e[1;32mproxima\e[0m | \e[1;32mfila\e[0m | \e[1;32mtocando\e[0m"
    echo -e ""
    echo -e "  \e[1;36mRÁDIO\e[0m"
    echo -e "  \e[1;32mplay-radio-busca [nome]\e[0m"
    echo -e "  \e[1;32mplay-radio-genero [genero]\e[0m"
    echo -e "  \e[1;32mplay-radio-busca-favoritos [nome]\e[0m"
    echo -e "  \e[1;32mplay-radio-favoritos\e[0m | \e[1;32mfavoritos\e[0m  (atalho — número=toca | r N=remove)"
    echo -e "  \e[1;32mplay-radio-ultimaradio\e[0m | \e[1;32mtocando-radio\e[0m"
    echo -e ""
    echo -e "  \e[1;36mÁUDIO\e[0m"
    echo -e "  \e[1;32mvolume [+ / - / 0-100]\e[0m"
    echo -e ""
    echo -e "  \e[1;36mSINCRONIZAÇÃO\e[0m"
    echo -e "  \e[1;36mYOUTUBE (se nao sair som)\e[0m"
    echo -e "  o motor resolve stream direto; se falhar: \e[1;32msudo yt-dlp -U\e[0m"
    echo -e "  opcional: \e[1;32m~/porco-music-bot/youtube-cookies.txt\e[0m + \e[1;32msystemctl --user restart porco.service\e[0m"
    echo -e ""
    echo -e "  \e[1;32mupdate-git [msg]\e[0m → só GitHub (fluxo típico no Arch)"
    echo -e "  \e[1;32mupdate-interno [msg]\e[0m → Gitea, só se existir remote \e[1;36minterno\e[0m (no Mint usas isto + git)"
    echo -e "  \e[1;32mupdate-geral\e[0m"
    echo -e ""
    echo -e "  \e[1;32mporco-help\e[0m"
}


function volume {
    local VOL_FILE="$BASE_DIR/volume-atual.txt"
    local VOL_ATUAL=$(cat "$VOL_FILE" 2>/dev/null); : ${VOL_ATUAL:=80}
    local NOVO_VOL=$1
    if [[ "$1" == "+" ]]; then NOVO_VOL=$((VOL_ATUAL + 5))
    elif [[ "$1" == "-" ]]; then NOVO_VOL=$((VOL_ATUAL - 5))
    elif [[ -z "$1" ]]; then echo "📢 Volume Sincronizado: $VOL_ATUAL%"; return 0; fi
    [ "$NOVO_VOL" -gt 100 ] && NOVO_VOL=100; [ "$NOVO_VOL" -lt 0 ] && NOVO_VOL=0
    echo "$NOVO_VOL" > "$VOL_FILE"
    if [ -S "$SOCKET_PATH" ]; then echo "{\"command\":[\"set_property\",\"volume\",$NOVO_VOL]}" | socat - "$SOCKET_PATH" >/dev/null 2>&1; fi
    if command -v pactl >/dev/null 2>&1; then
        pactl set-sink-volume @DEFAULT_SINK@ "${NOVO_VOL}%" >/dev/null 2>&1
    fi
    echo "📢 Sincronizado: $NOVO_VOL% (Pipewire/Pulse + Bot)"
}

# --- MANUTENÇÃO ---
function update-interno {
    echo "🏠 Gitea interno (só se o remote existir neste clone)..."
    cd "$BASE_DIR"
    git add -A
    local MSG="${*:-Sync Interno $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG" >/dev/null 2>&1
    if git config --get remote.interno.url >/dev/null 2>&1; then
        git push interno main
        _porco_arch_links
        echo "✅ Push para interno concluído."
    else
        echo "⚠️ Sem remote 'interno'. No Mint costumas usar Gitea daí; no Arch o fluxo habitual é só: update-git"
    fi
}

function update-git {
    echo "🌐 Arch: GitHub (remote github)..."
    cd "$BASE_DIR"
    git add -A
    local MSG="${*:-Sync GitHub $(hostname) $(date +'%d/%m/%Y %H:%M')}"
    git commit -m "$MSG" >/dev/null 2>&1
    git push github main
    _porco_arch_links
    echo "✨ GitHub atualizado. (No Mint: update-interno + git/Gitea como preferires.)"
}

function update-geral {
    echo "🐷 Atualização Geral do Porco (Arch)..."
    sudo pacman -Syu --needed mpv socat python python-pip yt-dlp git --noconfirm
    sudo python -m pip install -U yt-dlp 2>/dev/null || sudo python3 -m pip install -U yt-dlp
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
