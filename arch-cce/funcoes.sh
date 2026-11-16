#!/bin/bash
# --- CONFIGURAÇÃO ---
BASE_DIR="$HOME/porco-music-bot"
SOCKET_PATH="/tmp/porco.sock"
QUEUE_FILE="$BASE_DIR/queue.txt"
RADIO_FILE="$BASE_DIR/radio-atual.txt"
VOL_FILE="$BASE_DIR/volume-atual.txt"

porco_logo() { python3 "$BASE_DIR/porco_logo.py"; }

# --- MOTOR ---
acordar-porco() {
    echo "🐷 Acordando o porco em porco-music-bot (Systemd)..."
    systemctl --user restart porco.service
    sleep 1
    echo "✅ O porco está de pé e rodando em background absoluto!"
}

function porco-stop {
    python3 "$BASE_DIR/youtube_queue.py" cancel --clear
    echo "🛑 Parando o Porco Music Bot..."
    systemctl --user stop porco.service >/dev/null 2>&1
    > "$QUEUE_FILE"
    rm -f "$SOCKET_PATH" "$RADIO_FILE"
    echo "✅ Bot parado e fila limpa. Use 'acordar-porco' para ligar novamente."
}

# --- COMANDOS DE REPRODUÇÃO ---
function play {
    python3 "$BASE_DIR/play.py" "$*"
}

function play-artista {
    python3 "$BASE_DIR/play-artista.py" "$*"
}

function playlist-loop {
    python3 "$BASE_DIR/playlist_loop.py" "$*"
}

function mais {
    python3 "$BASE_DIR/youtube_queue.py" more "$*"
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

function play-radio-pais {
    python3 "$BASE_DIR/play-radio-pais.py" "$@"
}


function proxima { python3 "$BASE_DIR/media_control.py" proxima "$@"; }
function proximo { proxima "$@"; }
function próxima { proxima "$@"; }
function próximo { proxima "$@"; }
function anterior { python3 "$BASE_DIR/media_control.py" anterior "$@"; }
function pause { python3 "$BASE_DIR/media_control.py" pause "$@"; }

# --- STATUS E EXIBIÇÃO ---
function fila {
    python3 "$BASE_DIR/youtube_queue.py" status
}

function tocando-radio {
    porco_logo
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


function f5telas {
    export DISPLAY="${DISPLAY:-:0}"
    export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
    local WID
    WID=$(wmctrl -l 2>/dev/null | awk 'BEGIN{IGNORECASE=1} /Mozilla Firefox|Navigator/{print $1; exit}')
    if [ -z "$WID" ]; then
        echo "❌ Firefox nao encontrado"
        return 1
    fi
    xdotool windowactivate --sync "$WID" 2>/dev/null || true
    sleep 0.15
    xdotool key --window "$WID" --clearmodifiers F5
    echo "🔄 Pagina atualizada (F5)"
}

function porco-help {
    python3 "$BASE_DIR/porco_cli.py" --help
}


function audio_normalize {
    local MASTER=alsa_output.pci-0000_00_1b.0.analog-stereo
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    export PULSE_SERVER="${PULSE_SERVER:-unix:${XDG_RUNTIME_DIR}/pulse/native}"
    if ! pactl list short sinks 2>/dev/null | awk '{print $2}' | grep -qx normalize; then
        pactl load-module module-ladspa-sink sink_name=normalize sink_master="$MASTER" plugin=fast_lookahead_limiter_1913 label=fastLookaheadLimiter control=0,-3,0.1 >/dev/null 2>&1 || return 1
    fi
    if ! pactl list short sinks 2>/dev/null | awk '{print $2}' | grep -qx radio_level; then
        pactl load-module module-ladspa-sink sink_name=radio_level sink_master=normalize plugin=amp_1181 label=amp control=-12 >/dev/null 2>&1 || return 1
    fi
    pactl set-default-sink normalize >/dev/null 2>&1 || true
    # Limitador comum sem ganho extra. O radio recebe atenuacao fixa de 12 dB;
    # o Spotify preserva a normalizacao por faixa do proprio player.
    pactl --format=json list sink-inputs 2>/dev/null | python3 -c '
import json, sys
for stream in json.load(sys.stdin):
    binary = stream.get("properties", {}).get("application.process.binary", "")
    if binary in ("spotifyd", "mpv"):
        print(stream["index"], binary)
' | while read -r idx binary; do
        case "$binary" in
            spotifyd) pactl move-sink-input "$idx" normalize >/dev/null 2>&1 || true ;;
            mpv) pactl move-sink-input "$idx" radio_level >/dev/null 2>&1 || true ;;
        esac
    done
}

function volume_play {
    audio_normalize
    rm -f "$BASE_DIR/mute-ativo.txt"
    volume_restaurar
}

function volume_manha {
    audio_normalize
    rm -f "$BASE_DIR/mute-ativo.txt"
    volume_aplicar "$(volume_padrao_valor)"
}

function volume_padrao_valor {
    python3 "$BASE_DIR/audio_volume.py" default-value
}

function volume-padrao {
    python3 "$BASE_DIR/audio_volume.py" default "$@"
}

function volume_aplicar {
    python3 "$BASE_DIR/audio_volume.py" apply "$@"
}

function volume {
    python3 "$BASE_DIR/audio_volume.py" volume "$@"
}

function mute {
    python3 "$BASE_DIR/audio_volume.py" mute "$@"
}

function desmute {
    python3 "$BASE_DIR/audio_volume.py" unmute "$@"
}

function volume_restaurar {
    python3 "$BASE_DIR/audio_volume.py" restore "$@"
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
    python3 "$BASE_DIR/youtube_queue.py" cancel --clear
    echo "🧹 WIPE: Faxina total iniciada..."
    systemctl --user stop porco.service >/dev/null 2>&1
    > "$QUEUE_FILE"
    rm -f "$SOCKET_PATH" "$RADIO_FILE" "$BASE_DIR/loop-ativo.json"
    acordar-porco
    echo "🚀 Bot reiniciado e limpo!"
}

# nomes alternativos (porco-*)
# shellcheck source=/dev/null
source "$BASE_DIR/porco-aliases.sh"
# shellcheck source=/dev/null
source "$BASE_DIR/porco-cli.sh"
