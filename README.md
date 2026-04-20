# 🐷 Porco Music Bot (Versão Linux Mint)

Bot de música otimizado para **Linux Mint / Debian**.

## 🛠️ Comandos Principais
- `acordar-porco`: Inicia o motor do bot.
- `play [busca]`: Busca e toca músicas do YouTube.
- `play-radio-busca [nome]`: Busca rádios por nome e toca na seleção.
- `play-radio-busca-favoritos [nome]`: Busca rádios por nome e salva a selecionada nos favoritos.
- `play-radio-favoritos`: Lista favoritos com paginação, opção de remover (`r N`) e tocar por número.
- `play-radio-ultimaradio`: Toca a última rádio selecionada no bot.
- `volume [0-100]`: Ajusta o volume via socket IPC.
- `wipe`: Faxina total (para tudo, limpa fila e reinicia).
- `tocando`: Mostra a barra de progresso da música atual.
- `update-interno`: Sincroniza o código com o Gitea e atualiza os comandos do sistema.

## ⚠️ YouTube / HTTP 429

Se o `play` adicionar músicas na fila, mas **não sair som** (enquanto rádio funciona), costuma ser **limite do YouTube no IP** (HTTP 429).

1. Exporte cookies do navegador no formato **Netscape**.
2. Salve em `~/porco-music-bot/youtube-cookies.txt`
3. Rode: `systemctl --user restart porco.service`

## 📁 Estrutura
- **Pasta oficial:** `~/porco-music-bot`
- **Socket:** `/tmp/porco.sock`
- **Logs:** `~/porco-music-bot/bot.log`
