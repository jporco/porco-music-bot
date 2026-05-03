# 🐷 Porco Music Bot (Versão Linux Mint)

Bot de música otimizado para **Linux Mint / Debian**.

## 🛠️ Comandos Principais
- `acordar-porco`: Inicia o motor do bot.
- `play [busca]`: Coloca **1 resultado principal** na fila e até **5 sugestões** do Mix do YouTube (parecidas, até ~7min cada) — não repete 5× a mesma música da busca.
- `play-radio-busca [nome]`: Busca rádios por nome e toca na seleção.
- `play-radio-busca-favoritos [nome]`: Busca rádios por nome e salva a selecionada nos favoritos.
- `play-radio-favoritos`: Lista favoritos com paginação, opção de remover (`r N`) e tocar por número.
- `play-radio-ultimaradio`: Toca a última rádio selecionada no bot.
- `volume [0-100]`: Ajusta o volume via socket IPC.
- `wipe`: Faxina total (para tudo, limpa fila e reinicia).
- `tocando`: Mostra a barra de progresso da música atual.
- `update-interno`: Sincroniza o código com o Gitea e atualiza os comandos do sistema.

## ⚠️ YouTube / som não sai

O motor agora **resolve o stream direto** (`yt-dlp -g`) e toca no `mpv` **sem abrir a página** do YouTube (evita muitos casos de HTTP 429).

Se ainda falhar, rode `sudo yt-dlp -U`. Opcional: `youtube-cookies.txt` (Netscape) ajuda em bloqueios mais agressivos.

## 📁 Estrutura
- **Pasta oficial:** `~/porco-music-bot`
- **Socket:** `/tmp/porco.sock`
- **Logs:** `~/porco-music-bot/bot.log`

## 🐧 Arch / CachyOS (`arch-edition/`)

A pasta **`arch-edition`** traz o mesmo comportamento da edição Mint (motor com `yt-dlp` multi-cliente, `play` com mix + cache, rádio com `radio_state`, `fila` / `tocando`, systemd user).

```bash
cd ~/porco-music-bot/arch-edition
chmod +x instalar-arch.sh
./instalar-arch.sh
```

O serviço usa `arch-edition/engine.py` e `arch-edition/porco.service`. Comandos no shell vêm de `arch-edition/funcoes.sh` (não altera a edição Mint na raiz do repo).
