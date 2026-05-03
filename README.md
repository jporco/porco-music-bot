# 🐷 Porco Music Bot (Versão Linux Mint)

Bot de música otimizado para **Linux Mint / Debian**.

## 🛠️ Comandos Principais
- `acordar-porco`: Inicia o motor do bot.
- `play [busca]`: Coloca **1 resultado principal** na fila e até **5 sugestões** do Mix do YouTube (parecidas, até ~7min cada) — não repete 5× a mesma música da busca.
- `play-radio-busca [nome]`: Busca rádios por nome e toca na seleção.
- `play-radio-busca-favoritos [nome]`: Busca rádios por nome e salva a selecionada nos favoritos.
- `play-radio-favoritos` (atalho: **`favoritos`**): Lista favoritos com paginação, opção de remover (`r N`) e tocar por número.
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

- **Obrigatório no Arch:** o `./instalar-arch.sh` instala `~/.config/systemd/user/porco.service` (motor = `arch-edition/engine.py`) e faz `enable --now`. Sem isso, `acordar-porco` / rádio / `favoritos` não têm motor a processar a fila.
- Opcional: `sudo loginctl enable-linger "$USER"` para o serviço sobreviver ao logout.
- O instalador acrescenta `source …/arch-edition/funcoes.sh` em `~/.bashrc`, `~/.zshrc` e `~/.profile` (cria o ficheiro se não existir).
- **Git:** no Arch, `update-git` envia só para o **GitHub** (`git push github main`). No **Mint** continua o teu fluxo com **update-interno** (Gitea) e o que usares para o GitHub; o `update-git` da **raiz** (Mint) ainda encadeia o interno.

Comandos no shell vêm de `arch-edition/funcoes.sh` (a raiz do repo continua a ser a edição Mint).
