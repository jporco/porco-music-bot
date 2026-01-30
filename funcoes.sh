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
    echo -e "\e[1;35mporco-log\e[0m     -> Ver log ao vivo"
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

porco-log() {
    echo -e "\e[1;33m👀 Monitorando o Porco... (Pressione Ctrl+C para sair)\e[0m"
    tail -f ~/porco-bot/bot.log
}

update-git() {
    local MSG="$*"
    [ -z "$MSG" ] && MSG="Update automático"
    cd ~/porco-music-bot
    cp ~/porco-bot/{engine.py,play.py,funcoes.sh} . 2>/dev/null
    git add .
    git commit -m "$MSG"
    echo "📥 Sincronizando com GitHub..."
    git pull origin main --rebase
    git push origin main
    cd - > /dev/null
}

update-interno() {
    local MSG="$*"
    [ -z "$MSG" ] && MSG="Update automático interno"
    cd ~/porco-music-bot
    cp ~/porco-bot/{engine.py,play.py,funcoes.sh} . 2>/dev/null
    git add .
    git commit -m "$MSG"
    echo "📥 Sincronizando com Gitea..."
    git pull interno main --rebase
    git push interno main -f
    cd - > /dev/null
}

# (Incluir aqui as outras funções: historico, limpar, volume, fila, tocando, proxima)
