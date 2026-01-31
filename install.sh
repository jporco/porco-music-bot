#!/bin/bash
# 🐷 Porco Music Bot - Script de Instalação Automática

echo "📦 Instalando dependências..."
sudo apt update && sudo apt install -y mpv yt-dlp python3-requests

echo "🔗 Criando links no sistema..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo ln -sf "$DIR/play.py" /usr/local/bin/play
sudo ln -sf "$DIR/play-radio" /usr/local/bin/play-radio
sudo ln -sf "$DIR/play-radio-busca" /usr/local/bin/play-radio-busca
sudo ln -sf "$DIR/porco-help" /usr/local/bin/porco-help
sudo ln -sf "$DIR/engine.py" /usr/local/bin/acordar-porco

# Garante que tudo na pasta seja executável
chmod +x "$DIR"/*

echo "✅ Instalação concluída! Digite 'porco-help' para começar."
