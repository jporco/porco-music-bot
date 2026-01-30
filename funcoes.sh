#!/bin/bash

porco-help() {
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
    echo -e "\e[1;32mplay [busca]\e[0m  -> Toca 10 músicas"
    echo -e "\e[1;32mfila\e[0m          -> Ver lista e atual (->)"
    echo -e "\e[1;32mtocando\e[0m       -> Ver progresso [####]"
    echo -e "\e[1;32mproxima\e[0m       -> Pula a música atual"
    echo -e "\e[1;32mvolume [0-100]\e[0m-> Ajustar som"
    echo -e "\e[1;32mlimpar\e[0m        -> Reset total"
    echo -e "\e[1;36mhistorico\e[0m     -> Ver buscas recentes"
    echo -e "\e[1;34mupdate-git\e[0m    -> Sobe para o GitHub"
    echo -e "\e[1;34mvoltar-git\e[0m    -> Restaura versão"
    echo -e "-----------------------\n"
}

historico() {
    echo -e "\n📜 HISTÓRICO DE BUSCAS (Últimas 20):"
    if [ -f ~/porco-bot/historico.txt ]; then
        tail -n 20 ~/porco-bot/historico.txt
    else
        echo "O histórico está vazio ou foi limpo recentemente."
    fi
    echo ""
}

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
    local T=$(echo '{"command":["get_property","media-title"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":"\K[^"]+')
    local C_RAW=$(echo '{"command":["get_property","time-pos"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+')
    local TT_RAW=$(echo '{"command":["get_property","duration"]}' | socat - "$S" 2>/dev/null | grep -oP '"data":\K[0-9.]+')
    local C=$(echo "$C_RAW" | cut -d. -f1)
    local TT=$(echo "$TT_RAW" | cut -d. -f1)
    echo -e "\n🎶 ${T:-Carregando...}"
    if [[ ! -z "$C" && ! -z "$TT" && "$TT" != "0" ]]; then
        local P=$((C * 100 / TT)); [ $P -gt 100 ] && P=100
        local B=$(printf "%$((P/5))s" | tr ' ' '#'); local DT=$(printf "%$((20-(P/5)))s" | tr ' ' '-')
        printf "[%s%s] %02d:%02d / %02d:%02d (%d%%)\n\n" "$B" "$DT" $((C/60)) $((C%60)) $((TT/60)) $((TT%60)) "$P"
    fi
}

proxima() {
    echo '{"command": ["quit"]}' | socat - "/tmp/porco.sock" >/dev/null 2>&1
    echo "⏭️ Pulando..."
}

update-git() {
    [ -z "$1" ] && { echo "⚠️ Use: update-git 'msg'"; return; }
    cd ~/porco-music-bot
    cp ~/porco-bot/{engine.py,play.py,funcoes.sh} .
    git add . && git commit -m "$1" && git push origin main
    echo "🚀 GitHub Atualizado!"
    cd - > /dev/null
}
