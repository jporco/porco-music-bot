#!/bin/bash

# ... (mantendo limpar, volume e fila como estão)
limpar() {
    > ~/porco-bot/queue.txt
    pkill -9 -f engine.py; pkill -9 mpv; rm -f ~/porco-bot/temp/*.mp3
    python3 ~/porco-bot/engine.py > ~/porco-bot/bot.log 2>&1 &
    echo "🧹 Resetado!"
}

volume() {
    local S="/tmp/porco.sock"
    [ ! -S "$S" ] && { echo "⚠️ Off"; return; }
    case "$1" in
        "") VOL=$(echo '{"command":["get_property","volume"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+' | cut -d. -f1)
           echo "🔈 Vol: ${VOL:-0}%" ;;
        "+") echo '{"command":["add","volume",10]}' | socat - "$S" >/dev/null; echo "🔊 +10%" ;;
        "-") echo '{"command":["add","volume",-10]}' | socat - "$S" >/dev/null; echo "🔉 -10%" ;;
        *) echo "{\"command\":[\"set_property\",\"volume\",$1]}" | socat - "$S" >/dev/null; echo "📢 Vol: $1%" ;;
    esac
}

fila() {
    local S="/tmp/porco.sock"
    echo -e "\n📋 FILA"
    local A=$(echo '{"command":["get_property","media-title"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":"\K[^"]+')
    [ ! -z "$A" ] && echo -e " -> $A (TOCANDO)\n ---"
    if [ ! -s ~/porco-bot/queue.txt ]; then [ -z "$A" ] && echo " Vazia."; else cat -n ~/porco-bot/queue.txt; fi
}

tocando() {
    local S="/tmp/porco.sock"
    [ ! -S "$S" ] && { echo "⚠️ Off"; return; }

    # Puxa os dados brutos e filtra com mais rigor
    local T=$(echo '{"command":["get_property","media-title"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":"\K[^"]+')
    local C_RAW=$(echo '{"command":["get_property","time-pos"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+')
    local TT_RAW=$(echo '{"command":["get_property","duration"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+')

    [ -z "$T" ] && { echo "⏳ Carregando..."; return; }

    # Converte para inteiro (remove decimais)
    local C=$(echo "$C_RAW" | cut -d. -f1)
    local TT=$(echo "$TT_RAW" | cut -d. -f1)

    # Se MPV falhar no tempo total, pega do nome [MM:SS]
    if [[ -z "$TT" || "$TT" == "0" ]]; then
        local TM=$(echo "$T" | grep -oP '^\[\K[0-9:]+')
        if [ ! -z "$TM" ]; then
            local M=$(echo $TM | cut -d: -f1); local S_SEC=$(echo $TM | cut -d: -f2)
            TT=$((10#$M * 60 + 10#$S_SEC))
        fi
    fi

    echo -e "\n🎶 $T"

    if [[ ! -z "$C" && ! -z "$TT" && "$TT" != "0" ]]; then
        local P=$((C * 100 / TT))
        [ $P -gt 100 ] && P=100
        local TAM=20
        local POS=$((P * TAM / 100))
        local B=$(printf "%${POS}s" | tr ' ' '#')
        local DT=$(printf "%$((TAM-POS))s" | tr ' ' '-')
        
        printf "[%s%s] %02d:%02d / %02d:%02d (%d%%)\n\n" "$B" "$DT" $((C/60)) $((C%60)) $((TT/60)) $((TT%60)) "$P"
    else
        echo -e "[--------------------] 00:00 / --:-- (Processando...)\n"
    fi
}

porco-help() {
    echo -e "\n--- COMANDOS ---\nplay, fila, tocando, volume, limpar\n----------------\n"
}

proxima() {
    local S="/tmp/porco.sock"
    if [ -S "$S" ]; then
        echo '{"command": ["quit"]}' | socat - "$S" >/dev/null 2>&1
        echo "⏭️ Pulando para a próxima..."
    else
        echo "⚠️ Nada tocando para pular."
    fi
}
