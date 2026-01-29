#!/bin/bash
sudo apt update && sudo apt install -y python3 mpv socat ffmpeg yt-dlp
mkdir -p ~/porco-bot/temp
cp engine.py play.py funcoes.sh ~/porco-bot/
chmod +x ~/porco-bot/*.py ~/porco-bot/funcoes.sh
