# shell: porco | porco radio busca [nome]
porco_dispatch() {
    local tmp rc fn
    local -a payload
    tmp=$(mktemp) || return 1
    python3 "$BASE_DIR/porco_cli.py" "$@" >"$tmp"
    rc=$?
    if [ "$rc" -ne 0 ]; then
        rm -f "$tmp"
        return "$rc"
    fi
    mapfile -t payload < "$tmp"
    rm -f "$tmp"
    fn="${payload[0]}"
    if [ "$fn" = "__help__" ]; then
        python3 "$BASE_DIR/porco_cli.py" --help
        return 0
    fi
    "$fn" "${payload[@]:1}"
}

porco_repl() {
    local line
    porco_logo
    echo "cmd: ajuda | sair"
    trap 'echo' INT
    while IFS= read -r -e -p "porco> " line || [ -n "$line" ]; do
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [ -z "$line" ] && continue
        case "$line" in
            sair|exit|quit|q) echo "ok: sai"; break ;;
        esac
        porco_dispatch --line "$line"
    done
    trap - INT
}

porco() {
    if [ $# -eq 0 ]; then
        porco_repl
        return
    fi
    porco_dispatch "$@"
}
