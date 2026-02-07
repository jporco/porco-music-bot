#!/bin/bash

INSTALL_DIR="$HOME/porco-music-bot/arch-edition"

echo "🤖 Iniciando Instalação: Porco Music Bot (Arch Linux Edition)..."

# 1. Instalando dependências via Pacman
echo "📦 Instalando pacotes do sistema (pacman)..."
sudo pacman -Syu --needed mpv socat python-pip git --noconfirm

# 2. Instalando yt-dlp
# No Arch, o ideal é instalar via pacman ou usar a flag de sistema se necessário
echo "🎥 Instalando yt-dlp..."
sudo pacman -S yt-dlp --noconfirm

# 3. Configurando o .bashrc
echo "📝 Configurando aliases no Arch..."
if ! grep -q "arch-edition/funcoes.sh" ~/.bashrc; then
    echo -e "\n# Porco Music Bot - Arch Edition\nsource $INSTALL_DIR/funcoes.sh" >> ~/.bashrc
    echo "✅ Funções adicionadas ao .bashrc"
fi

# 4. Criando links globais
echo "🔗 Criando links de comando..."
sudo ln -sf $INSTALL_DIR/engine.py /usr/local/bin/acordar-porco
sudo ln -sf $INSTALL_DIR/play.py /usr/local/bin/play
sudo ln -sf $INSTALL_DIR/volume.py /usr/local/bin/volume

# 5. Permissões
chmod +x $INSTALL_DIR/*.py
chmod +x $INSTALL_DIR/*.sh

echo "✨ Pronto! O Porco agora fala Arch (RTFM!)."
echo "👉 Rode 'source ~/.bashrc' para ativar."
