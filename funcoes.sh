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
    echo -e "\e[1;33macordar-porco\e[0m -> Inicia/Reinicia o bot"
    echo -e "\e[1;32mplay [busca]\e[0m  -> Toca 10 músicas"
    echo -e "\e[1;32mfila\e[0m          -> Ver lista e atual (->)"
    echo -e "\e[1;32mtocando\e[0m       -> Ver progresso [####]"
    echo -e "\e[1;32mproxima\e[0m       -> Pula a música atual"
    echo -e "\e[1;32mvolume [0-100]\e[0m-> Ajustar som"
    echo -e "\e[1;36mhistorico\e[0m     -> Ver buscas recentes"
    echo -e "\e[1;34mupdate-git\e[0m    -> Sincronizar GitHub"
    echo -e "\e[1;31mupdate-interno\e[0m-> Sincronizar Gitea"
    echo -e "-----------------------\n"
}

acordar-porco() {
    echo "🐷 Acordando o porco..."
    pkill -9 -f engine.py >/dev/null 2>&1
    pkill -9 mpv >/dev/null 2>&1
    rm -f /tmp/porco.sock
    python3 ~/porco-bot/engine.py > ~/porco-bot/bot.log 2>&1 &
    sleep 1
    echo "✅ O porco está de pé!"
}

historico() {
    echo -e "\n📜 HISTÓRICO DE BUSCAS:"
    [ -f ~/porco-bot/historico.txt ] && tail -n 20 ~/porco-bot/historico.txt || echo "Vazio."
}

limpar() {
    > ~/porco-bot/queue.txt
    acordar-porco
    echo "🧹 Fila limpa e bot resetado!"
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
    local C=$(echo "$C_RAW" | cut -d. -f1); local TT=$(echo "$TT_RAW" | cut -d. -f1)
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
    [ -z "$1" ] && { echo "⚠️ update-git 'msg'"; return; }
    cd ~/porco-music-bot
    cp ~/porco-bot/{engine.py,play.py,funcoes.sh} . 2>/dev/null
    git add . && git commit -m "$1" && git push origin main
    cd - > /dev/null
}

update-interno() {
    [ -z "$1" ] && { echo "⚠️ update-interno 'msg'"; return; }
    cd ~/porco-music-bot
    cp ~/porco-bot/{engine.py,play.py,funcoes.sh} . 2>/dev/null
    git add . && git commit -m "$1" && git push interno main -f
    cd - > /dev/null
}

# Ver os logs do porco em tempo real
porco-log() {
    echo -e "\e[1;33m👀 Monitorando o Porco... (Pressione Ctrl+C para sair)\e[0m"
    if [ -f ~/porco-bot/bot.log ]; then
        tail -f ~/porco-bot/bot.log
    else
        echo "⚠️ O arquivo de log ainda não existe. Tente rodar 'acordar-porco' primeiro."
    fi
}
