#!/bin/bash

# --- CONFIGURAÇÃO ---
REPO_URL="http://gitea.cominformatica/lua.jesus/porco-music-bot-tea.git"
INSTALL_DIR="$HOME/porco-music-bot"

echo "🐷 Iniciando Instalação do Porco Music Bot (Mint Edition)..."

# 1. Atualizando sistema e instalando bases
echo "📦 Instalando dependências do sistema..."
sudo apt update -y
sudo apt install python3 python3-pip mpv socat git -y

# 2. Instalando yt-dlp via PIP (sempre a versão mais nova)
echo "🎥 Instalando yt-dlp..."
sudo python3 -m pip install -U yt-dlp

# 3. Configurando atalhos no .bashrc
echo "📝 Configurando ambiente do usuário..."
if ! grep -q "porco-music-bot/funcoes.sh" ~/.bashrc; then
    echo -e "\n# Porco Music Bot\nsource $INSTALL_DIR/funcoes.sh" >> ~/.bashrc
    echo "✅ Funções adicionadas ao .bashrc"
fi

# 4. Criando links globais no sistema
echo "🔗 Criando links em /usr/local/bin..."
sudo ln -sf $INSTALL_DIR/engine.py /usr/local/bin/acordar-porco
sudo ln -sf $INSTALL_DIR/play.py /usr/local/bin/play
sudo ln -sf $INSTALL_DIR/volume.py /usr/local/bin/volume

# 4.b Configurando Serviço Systemd para auto-inicialização no boot e persistência SSH
echo "⚙️ Configurando serviço autostart do Systemd (O porco nunca dorme!)..."
mkdir -p $HOME/.config/systemd/user/
cp $INSTALL_DIR/porco.service $HOME/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now porco.service
echo "⚠️ Habilitando 'linger' para que o bot inicie no boot (pode pedir senha sudo)..."
sudo loginctl enable-linger $USER

# 5. Permissões de execução
chmod +x $INSTALL_DIR/*.py
chmod +x $INSTALL_DIR/*.sh

echo "✨ Instalação Concluída!"
echo "👉 Rode 'source ~/.bashrc' ou abra outro terminal e digite 'acordar-porco' para ativar e limpar arquivos mortos."
