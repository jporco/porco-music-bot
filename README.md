# Porco Music Bot

Terminal-first music bot for **Linux Mint / Debian** (repo root) and **Arch Linux / CachyOS** (`arch-edition/`). It uses **Python**, **mpv**, **yt-dlp**, and **socat** (JSON IPC). YouTube playback prefers a **direct stream URL** from yt-dlp to reduce HTTP 429 issues.

---

## English

### Requirements

- **Python 3**, **mpv**, **socat**, **git**, **yt-dlp** (pip or distro package)
- User **systemd** (`systemctl --user`) for the engine service (recommended on both Mint and Arch)

### Install from GitHub

```bash
git clone https://github.com/jporco/porco-music-bot.git ~/porco-music-bot
cd ~/porco-music-bot
```

### Linux Mint / Debian (root edition)

Scripts and shell helpers live in **`~/porco-music-bot/`** (not in `arch-edition/`). The user service runs **`~/porco-music-bot/engine.py`**.

1. Clone the repo (see above).
2. Run the installer:

```bash
chmod +x ~/porco-music-bot/instalar-porco.sh
~/porco-music-bot/instalar-porco.sh
```

3. Reload your shell (or open a new terminal):

```bash
source ~/.bashrc
```

4. Optional: confirm the engine:

```bash
systemctl --user status porco.service
```

The installer adds `source ~/porco-music-bot/funcoes.sh` to **`~/.bashrc`**, creates symlinks under `/usr/local/bin`, copies **`porco.service`** to `~/.config/systemd/user/`, enables **`loginctl linger`** for your user, and starts the service.

### Arch Linux / CachyOS (`arch-edition/`)

Python motor and CLI helpers come from **`~/porco-music-bot/arch-edition/`**. Data files (queue, favourites JSON, volume file, logs) still live under **`~/porco-music-bot/`**.

1. Clone the repo (see above).
2. Run the Arch installer:

```bash
chmod +x ~/porco-music-bot/arch-edition/instalar-arch.sh
~/porco-music-bot/arch-edition/instalar-arch.sh
```

3. Reload your shell:

```bash
source ~/.bashrc    # and/or ~/.zshrc — the script also updates ~/.profile when needed
```

4. **Important:** `instalar-arch.sh` installs **`~/.config/systemd/user/porco.service`** pointing at **`arch-edition/engine.py`** and runs **`systemctl --user enable --now porco.service`**. Without this, `play`, radio, and `favoritos` will not have a running engine.

5. Optional: keep the user service after logout (headless / SSH-friendly):

```bash
sudo loginctl enable-linger "$USER"
```

### After installation (both distros)

- Start or restart the engine: **`acordar-porco`** (wraps `systemctl --user restart porco.service`).
- Help menu: **`porco-help`**.
- Logs: **`~/porco-music-bot/bot.log`**  
- IPC socket: **`/tmp/porco.sock`**

### Main commands

| Command | Description |
|--------|-------------|
| `play …` | One main YouTube match plus up to **5 related** tracks (mix-style), length-capped; uses a short-lived cache. |
| `play-radio-busca …` | Search internet radio by name (interactive). |
| `play-radio-genero …` | Browse radios by genre/tag. |
| `play-radio-busca-favoritos …` | Search and add the chosen station to **favourites**. |
| `play-radio-favoritos` / **`favoritos`** | List favourites, play by number, remove with `r N`. |
| `play-radio-ultimaradio` | Play the last selected station. |
| `proxima` | Skip to the next queued item (mpv IPC). |
| `fila` / `tocando` | Queue / now-playing style status (`tocando` mirrors `fila` on Arch). |
| `volume …` | Sync volume file + mpv IPC; Mint edition also touches ALSA where configured. |
| `wipe` | Stop playback, clear queue, restart engine. |
| `porco-stop` | Stop user service, kill mpv, clear queue/socket markers. |

### YouTube / no audio

1. Update yt-dlp: `sudo yt-dlp -U` (or distro equivalent).  
2. Optional: place a Netscape-format **`youtube-cookies.txt`** in **`~/porco-music-bot/`** and restart the service.  
3. Restart engine: `acordar-porco` or `systemctl --user restart porco.service`.

### Git workflow

- **Mint (root `funcoes.sh`):** `update-git` pushes to **`github`** and then calls **`update-interno`** (Gitea / `interno` remote, depending on how you configured remotes). Use whatever matches your `origin` / `interno` setup.
- **Arch (`arch-edition/funcoes.sh`):** **`update-git`** only runs **`git push github main`** (no automatic Gitea push). **`update-interno`** runs **`git push interno main`** only if the **`interno`** remote exists.

### Repository layout (short)

- **Mint:** `engine.py`, `play.py`, `funcoes.sh`, `instalar-porco.sh`, `porco.service` (root engine path).
- **Arch:** `arch-edition/` mirrors the motor + radio scripts; install via `instalar-arch.sh`.
- Shared runtime under **`~/porco-music-bot/`** (e.g. `queue.txt`, `radio-favoritos.json`).

---

## Português (Brasil)

### Requisitos

- **Python 3**, **mpv**, **socat**, **git**, **yt-dlp** (pip ou pacote da distro)
- **systemd** em modo utilizador (`systemctl --user`) para o serviço do motor (recomendado no Mint e no Arch)

### Instalar a partir do GitHub

```bash
git clone https://github.com/jporco/porco-music-bot.git ~/porco-music-bot
cd ~/porco-music-bot
```

### Linux Mint / Debian (edição na raiz do repositório)

Scripts e funções do shell ficam em **`~/porco-music-bot/`** (fora de `arch-edition/`). O serviço user corre **`~/porco-music-bot/engine.py`**.

1. Clonar o repositório (comando acima).
2. Correr o instalador:

```bash
chmod +x ~/porco-music-bot/instalar-porco.sh
~/porco-music-bot/instalar-porco.sh
```

3. Recarregar o shell (ou abrir terminal novo):

```bash
source ~/.bashrc
```

4. Opcional: verificar o motor:

```bash
systemctl --user status porco.service
```

O instalador acrescenta `source ~/porco-music-bot/funcoes.sh` ao **`~/.bashrc`**, cria links em **`/usr/local/bin`**, copia **`porco.service`** para **`~/.config/systemd/user/`**, ativa **`loginctl linger`** para o teu utilizador e inicia o serviço.

### Arch Linux / CachyOS (`arch-edition/`)

O motor Python e as funções do shell vêm de **`~/porco-music-bot/arch-edition/`**. Ficheiros de dados (fila, JSON de favoritos, volume, logs) continuam em **`~/porco-music-bot/`**.

1. Clonar o repositório (comando acima).
2. Correr o instalador Arch:

```bash
chmod +x ~/porco-music-bot/arch-edition/instalar-arch.sh
~/porco-music-bot/arch-edition/instalar-arch.sh
```

3. Recarregar o shell:

```bash
source ~/.bashrc    # e/ou ~/.zshrc — o script também trata do ~/.profile quando faz falta
```

4. **Importante:** o `instalar-arch.sh` instala **`~/.config/systemd/user/porco.service`** apontando para **`arch-edition/engine.py`** e executa **`systemctl --user enable --now porco.service`**. Sem isto, `play`, rádio e `favoritos` não têm motor a processar a fila.

5. Opcional: o serviço continuar depois do logout:

```bash
sudo loginctl enable-linger "$USER"
```

### Depois de instalar (ambas as distros)

- Arrancar ou reiniciar o motor: **`acordar-porco`** (equivale a `systemctl --user restart porco.service`).
- Ajuda: **`porco-help`**.
- Logs: **`~/porco-music-bot/bot.log`**
- Socket IPC: **`/tmp/porco.sock`**

### Comandos principais

| Comando | Descrição |
|--------|-----------|
| `play …` | Um resultado principal no YouTube + até **5 sugestões** no estilo mix (com limite de duração); usa cache temporário. |
| `play-radio-busca …` | Procurar rádio por nome (interativo). |
| `play-radio-genero …` | Rádios por género/tag. |
| `play-radio-busca-favoritos …` | Procurar e gravar a rádio escolhida nos **favoritos**. |
| `play-radio-favoritos` / **`favoritos`** | Listar favoritos, tocar por número, remover com `r N`. |
| `play-radio-ultimaradio` | Tocar a última rádio escolhida. |
| `proxima` | Saltar para o próximo item da fila (IPC do mpv). |
| `fila` / `tocando` | Estado da fila / “agora a tocar” (`tocando` na prática chama `fila` na edição Arch). |
| `volume …` | Sincroniza ficheiro de volume + IPC do mpv; na edição Mint também ajusta ALSA quando configurado. |
| `wipe` | Para tudo, limpa fila, reinicia o motor. |
| `porco-stop` | Para o serviço user, mata o mpv, limpa fila/socket. |

### YouTube / sem som

1. Atualizar yt-dlp: `sudo yt-dlp -U` (ou equivalente da distro).  
2. Opcional: ficheiro Netscape **`youtube-cookies.txt`** em **`~/porco-music-bot/`** e reiniciar o serviço.  
3. Reiniciar o motor: `acordar-porco` ou `systemctl --user restart porco.service`.

### Git

- **Mint (`funcoes.sh` na raiz):** o **`update-git`** faz push para **`github`** e de seguida chama **`update-interno`** (Gitea / remoto **`interno`**, conforme tiveres configurado).
- **Arch (`arch-edition/funcoes.sh`):** o **`update-git`** faz só **`git push github main`**. O **`update-interno`** só faz **`git push interno main`** se existir o remoto **`interno`**.

### Estrutura do repositório (resumo)

- **Mint:** `engine.py`, `play.py`, `funcoes.sh`, `instalar-porco.sh`, `porco.service` (motor na raiz).
- **Arch:** pasta **`arch-edition/`** com o mesmo tipo de motor e scripts de rádio; instalação com **`instalar-arch.sh`**.
- Estado partilhado em **`~/porco-music-bot/`** (ex.: `queue.txt`, `radio-favoritos.json`).
