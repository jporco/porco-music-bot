#!/bin/bash
echo "📤 Enviando atualizações para o Git..."
cd ~/porco-music-bot
git add .
git commit -m "Update: Versão Mint com paginação e volume fix"
git push origin main
echo "✅ Git atualizado!"
