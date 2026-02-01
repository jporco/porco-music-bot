#!/bin/bash
# 🐷 Porco Music Bot - ARCH LINUX VERSION

echo -e "\e[1;35m📦 Instalando dependências no Arch Linux...\e[0m"
# No Arch, o yt-dlp e o mpv estão nos repositórios oficiais
sudo pacman -S --noconfirm mpv yt-dlp python-requests

echo -e "\e[1;34m🔗 Criando links simbólicos...\e[0m"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Criando os atalhos para os comandos funcionarem de qualquer lugar
sudo ln -sf "$DIR/play.py" /usr/local/bin/play
sudo ln -sf "$DIR/play-radio" /usr/local/bin/play-radio
sudo ln -sf "$DIR/play-radio-busca" /usr/local/bin/play-radio-busca
sudo ln -sf "$DIR/porco-help" /usr/local/bin/porco-help
sudo ln -sf "$DIR/engine.py" /usr/local/bin/acordar-porco

# No Arch, às vezes o /usr/local/bin não está no PATH por padrão. 
# Vamos garantir que os arquivos sejam executáveis.
chmod +x "$DIR"/*

echo -e "\e[1;32m✅ Instalação concluída no Arch!\e[0m"
echo "Digite 'porco-help' para ver os comandos."
