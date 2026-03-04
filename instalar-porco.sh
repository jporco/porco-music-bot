#!/bin/bash

# --- CONFIGURAÇÃO ---
INSTALL_DIR="$HOME/porco-music-bot"

echo -e "\e[1;35m"
echo "  🐷 PORCO MUSIC BOT - INSTALADOR MULTI-DISTRO"
echo -e "\e[0m"

echo "Escolha sua distribuição:"
echo "1) Linux Mint / Ubuntu / Debian"
echo "2) Arch Linux / Manjaro / Endeavour"
read -p "Opção: " DISTRO

if [ "$DISTRO" == "1" ]; then
    echo "📦 [MINT] Instalando dependências..."
    sudo apt update -y
    sudo apt install python3 python3-pip mpv socat git -y
    sudo python3 -m pip install -U yt-dlp
    
    # Sincroniza arquivos da raiz (Mint)
    SOURCE_DIR="$INSTALL_DIR"
    DISTRO_NAME="Mint"

elif [ "$DISTRO" == "2" ]; then
    echo "📦 [ARCH] Instalando dependências..."
    sudo pacman -Syu yt-dlp mpv socat git python-requests --noconfirm
    
    # Sincroniza arquivos da pasta arch-edition
    SOURCE_DIR="$INSTALL_DIR/arch-edition"
    DISTRO_NAME="Arch"
    
    # No Arch, vamos copiar os arquivos da arch-edition para a raiz para facilitar o uso
    echo "🔄 Configurando versão Arch..."
    cp "$INSTALL_DIR/arch-edition/"* "$INSTALL_DIR/"
else
    echo "❌ Opção inválida. Saindo..."
    exit 1
fi

# --- CONFIGURAÇÃO COMUM ---

# 1. Configurando atalhos no .bashrc
echo "📝 Configurando ambiente do usuário..."
if ! grep -q "porco-music-bot/funcoes.sh" ~/.bashrc; then
    echo -e "\n# Porco Music Bot\nsource $INSTALL_DIR/funcoes.sh" >> ~/.bashrc
    echo "✅ Funções adicionadas ao .bashrc"
fi

# 2. Criando links globais no sistema
echo "🔗 Criando links em /usr/local/bin..."
sudo ln -sf "$INSTALL_DIR/engine.py" /usr/local/bin/acordar-porco
sudo ln -sf "$INSTALL_DIR/play.py" /usr/local/bin/play
sudo ln -sf "$INSTALL_DIR/volume.py" /usr/local/bin/volume
sudo ln -sf "$INSTALL_DIR/play-radio-busca.py" /usr/local/bin/play-radio-busca

# 3. Permissões de execução
chmod +x "$INSTALL_DIR"/*.py
chmod +x "$INSTALL_DIR"/*.sh

echo -e "\e[1;32m✨ Instalação Concluída ($DISTRO_NAME Version)!\e[0m"
echo "👉 Rode 'source ~/.bashrc' e depois 'acordar-porco' para começar."
echo "👉 Dica: Digite 'ajuda' para ver os comandos."
