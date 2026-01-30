# 🐷 Porco Music Bot 🎶

> **O player de música via terminal mais roots e eficiente que você já viu.**

Este projeto é um bot de música leve, focado em performance e simplicidade, feito para rodar direto no seu Linux (especialmente Arch e Ubuntu/Debian).

---

## 🐽 O Mascote Oficial
\`\`\`text
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣶⣶⣶⣶⣦⣤⣄⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢀⡶⢻⡦⢀⣠⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⢀⣴⣾⡿⠀⣠⠀⠀
⠀⠠⣬⣷⣾⣡⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣌⣋⣉⣄⠘⠋⠀⠀
⠀⠀⠀⠀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⣿⡄⠀⠀⠀
⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣾⣿⣷⣶⡄⠀
⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
⠀⠀⠀⠀⠸⣿⣿⣿⠛⠛⠛⠛⠛⠛⠛⠛⠻⠿⣿⣿⡿⠛⠛⠛⠋⠉⠉⠀⠀⠀
⠀⠀⠀⠀⠀⢻⣿⣿⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⢻⣿⠃⠸⣿⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⠿⠇⠀⠀⠀⠻⠇⠀⠀⠀⠀⠀⠈⠿⠀⠀⠻⠿⠀⠀⠀⠀⠀⠀
\`\`\`

---

## ✨ Funcionalidades

* 🔍 **Busca Inteligente**: Encontra as 10 melhores correspondências no YouTube.
* 🛡️ **Filtro Anti-Show**: Ignora automaticamente vídeos com mais de 7 minutos.
* 📊 **Progresso Real-time**: Barra de progresso visual estilizada no terminal.
* 📜 **Histórico**: Registro automático de buscas dos últimos 2 dias.
* 🚀 **Git-Sync**: Comandos integrados para backup e restauração no GitHub.

---

## 🛠️ Comandos Disponíveis

| Comando | Função |
| :--- | :--- |
| \`play [busca]\` | Busca e adiciona 10 músicas à fila |
| \`fila\` | Mostra o que está tocando e as próximas |
| \`tocando\` | Exibe a barra de progresso e tempo atual |
| \`proxima\` | Pula para a próxima faixa |
| \`volume [0-100]\` | Ajusta o volume (ou \`volume +\` / \`volume -\`) |
| \`historico\` | Lista as últimas buscas realizadas |
| \`limpar\` | Reseta o bot e limpa a fila de reprodução |
| \`update-git\` | Sincroniza suas mudanças com o repositório |

---

## 🚀 Como Instalar

1. **Clone o repositório:**
   \`\`\`bash
   git clone https://github.com/jporco/porco-music-bot.git
   cd porco-music-bot
   \`\`\`

2. **Rode o instalador:**
   \`\`\`bash
   chmod +x install.sh
   ./install.sh
   \`\`\`

3. **Carregue os comandos:**
   \`\`\`bash
   source ~/porco-bot/funcoes.sh
   \`\`\`

---

## 🛡️ Requisitos do Sistema
* **Python 3**
* **MPV** (O cérebro do áudio)
* **yt-dlp** (Para buscar no YouTube)
* **socat** (Comunicação entre scripts)

---
*Feito com 🐷 por jporco.*
