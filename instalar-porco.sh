#!/bin/bash

# --- CONFIGURAÇÃO ---
INSTALL_DIR="$HOME/porco-music-bot"

echo -e "\e[1;35m"
echo "  🐷 PORCO MUSIC BOT - INSTALADOR MULTI-DISTRO (v2.0)"
echo -e "\e[0m"

echo "Escolha sua distribuição:"
echo "1) Linux Mint / Ubuntu / Debian"
echo "2) Arch Linux / Manjaro / Endeavour"
read -p "Opção: " DISTRO

if [ "$DISTRO" == "1" ]; then
    echo "📦 [MINT] Instalando dependências..."
    sudo apt update -y
    sudo apt install python3 python3-pip mpv socat git fzf -y
    sudo python3 -m pip install -U yt-dlp
    
    DISTRO_NAME="Mint"

elif [ "$DISTRO" == "2" ]; then
    echo "📦 [ARCH] Instalando dependências..."
    sudo pacman -Syu yt-dlp mpv socat git python-requests fzf --noconfirm
    
    DISTRO_NAME="Arch"
    
    # Sincroniza arquivos da pasta arch-edition para a raiz
    echo "🔄 Aplicando otimizações para Arch Linux..."
    cp "$INSTALL_DIR/arch-edition/"* "$INSTALL_DIR/"
else
    echo "❌ Opção inválida. Saindo..."
    exit 1
fi

# --- CONFIGURAÇÃO DE AMBIENTE ---

setup_shell_config() {
    local CONFIG_FILE=$1
    if [ -f "$CONFIG_FILE" ]; then
        if ! grep -q "porco-music-bot/funcoes.sh" "$CONFIG_FILE"; then
            echo -e "\n# Porco Music Bot\nsource $INSTALL_DIR/funcoes.sh" >> "$CONFIG_FILE"
            echo "✅ Funções adicionadas ao $CONFIG_FILE"
        fi
    fi
}

echo "📝 Configurando ambiente do usuário..."
setup_shell_config "$HOME/.bashrc"
setup_shell_config "$HOME/.zshrc"

# --- LINKS GLOBAIS ---
# Removemos links antigos que causavam conflitos (ex: tocando como script)
sudo rm -f /usr/local/bin/tocando
sudo rm -f /usr/local/bin/porco-help

echo "🔗 Criando links em /usr/local/bin..."
sudo ln -sf "$INSTALL_DIR/engine.py" /usr/local/bin/acordar-porco
sudo ln -sf "$INSTALL_DIR/play.py" /usr/local/bin/play
sudo ln -sf "$INSTALL_DIR/volume.py" /usr/local/bin/volume

# --- PERMISSÕES ---
chmod +x "$INSTALL_DIR"/*.py
chmod +x "$INSTALL_DIR"/*.sh

echo -e "\e[1;32m"
echo "✨ Instalação Concluída ($DISTRO_NAME Edition)!"
echo "--------------------------------------------------"
echo "👉 IMPORTANTE: Reinicie seu terminal ou rode 'source ~/.zshrc' (ou .bashrc)"
echo "👉 Depois, rode 'acordar-porco' para iniciar o motor."
echo "👉 Digite 'ajuda' para ver os novos comandos modernos!"
echo -e "\e[0m"
