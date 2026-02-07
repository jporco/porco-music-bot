# 🐷 Porco Music Bot (Versão Linux Mint)

Bot de música otimizado para **Linux Mint / Debian**.

## 🛠️ Comandos Principais
- `acordar-porco`: Inicia o motor do bot.
- `play [busca]`: Busca e toca músicas do YouTube.
- `play-radio-busca [nome]`: Busca rádios com paginação (`m` para mais, `v` para voltar).
- `volume [0-100]`: Ajusta o volume via socket IPC.
- `wipe`: Faxina total (para tudo, limpa fila e reinicia).
- `tocando`: Mostra a barra de progresso da música atual.
- `update-interno`: Sincroniza o código com o Gitea e atualiza os comandos do sistema.

## 📁 Estrutura
- **Pasta oficial:** `~/porco-music-bot`
- **Socket:** `/tmp/porco.sock`
- **Logs:** `~/porco-music-bot/bot.log`
