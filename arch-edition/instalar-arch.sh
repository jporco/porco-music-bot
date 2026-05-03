#!/bin/bash
# Instalação Arch/CachyOS — mesmas capacidades que a edição Mint (motor, play com mix, rádio, systemd user).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$SCRIPT_DIR"
BASE_DIR="$HOME/porco-music-bot"

echo "🤖 Porco Music Bot — Arch edition (motor em arch-edition/, dados em ~/porco-music-bot)"

echo "📦 Pacotes..."
sudo pacman -Syu --needed mpv socat python python-pip git --noconfirm
sudo pacman -S --needed yt-dlp --noconfirm
sudo python -m pip install -U yt-dlp 2>/dev/null || sudo python3 -m pip install -U yt-dlp

mkdir -p "$BASE_DIR"

echo "📝 source funcoes.sh (bash, zsh ou login shell)..."
_add_funcoes_snippet() {
    local rc="$1"
    [ -f "$rc" ] || touch "$rc"
    grep -q "arch-edition/funcoes.sh" "$rc" 2>/dev/null && return 0
    printf '\n# Porco Music Bot — Arch Edition\nsource %s/funcoes.sh\n' "$INSTALL_DIR" >> "$rc"
    echo "✅ Incluído em $rc"
}
_add_funcoes_snippet "$HOME/.bashrc"
_add_funcoes_snippet "$HOME/.zshrc"
_add_funcoes_snippet "$HOME/.profile"

echo "⚙️ systemd --user (porco.service)..."
mkdir -p "$HOME/.config/systemd/user"
cp "$INSTALL_DIR/porco.service" "$HOME/.config/systemd/user/porco.service"
systemctl --user daemon-reload
systemctl --user enable --now porco.service
echo "⚠️ Para o motor sobreviver ao logout (opcional): sudo loginctl enable-linger $USER"

echo "🔗 /usr/local/bin..."
sudo ln -sf "$INSTALL_DIR/engine.py" /usr/local/bin/acordar-porco
sudo ln -sf "$INSTALL_DIR/play.py" /usr/local/bin/play
sudo ln -sf "$INSTALL_DIR/volume.py" /usr/local/bin/volume

chmod +x "$INSTALL_DIR"/*.py "$INSTALL_DIR"/*.sh 2>/dev/null

echo ""
echo "📡 Verificação:"
if systemctl --user is-active --quiet porco.service 2>/dev/null; then
    echo "  porco.service: ativo"
else
    echo "  porco.service: inativo — rode: systemctl --user status porco.service"
fi

echo "✨ Pronto. Abra um terminal novo ou: source ~/.bashrc (ou ~/.zshrc)"
echo "👉 acordar-porco   |   porco-help   |   favoritos"
