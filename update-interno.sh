#!/bin/bash
echo "🔄 Atualizando links internos do sistema..."
cd ~/porco-music-bot
chmod +x *.py *.sh
sudo ln -sf ~/porco-music-bot/engine.py /usr/local/bin/acordar-porco
sudo ln -sf ~/porco-music-bot/play.py /usr/local/bin/play
sudo ln -sf ~/porco-music-bot/play-radio-busca.py /usr/local/bin/play-radio-busca
sudo ln -sf ~/porco-music-bot/volume.py /usr/local/bin/volume
echo "✅ Links atualizados!"
