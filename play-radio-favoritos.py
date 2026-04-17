#!/usr/bin/env python3

from radio_state import load_favorites, remove_favorite_by_number, tune_station


def listar_e_tocar_favoritos():
    passo = 10
    idx = 0

    while True:
        favorites = load_favorites()
        total = len(favorites)

        if total == 0:
            print("📭 Nenhuma rádio favorita salva ainda.")
            print("💡 Use: play-radio-busca-favoritos [nome]")
            return

        if idx >= total:
            idx = max(0, ((total - 1) // passo) * passo)

        print(f"\n--- ❤️ FAVORITOS ({idx + 1} a {min(idx + passo, total)} de {total}) ---")
        page = favorites[idx: idx + passo]
        for i, station in enumerate(page, idx + 1):
            print(f"[{i}] {station['name'][:50]} [{station.get('country', '??')}]")

        print("-" * 45)
        print("[0] Sair")

        msg = "\n👉 Digite o número para tocar"
        if idx + passo < total:
            msg += " | [m] Próxima"
        if idx > 0:
            msg += " | [v] Anterior"
        msg += " | [r N] Remover favorito"
        msg += ": "

        cmd = input(msg).strip().lower()

        if cmd == "0":
            return
        if cmd == "m" and idx + passo < total:
            idx += passo
            continue
        if cmd == "v" and idx > 0:
            idx -= passo
            continue

        if cmd.startswith("r "):
            part = cmd[2:].strip()
            if part.isdigit():
                num = int(part)
                removed = remove_favorite_by_number(num)
                if removed is None:
                    print("❌ Número inválido para remover.")
                else:
                    print(f"🗑️ Removido dos favoritos: {removed['name']}")
            else:
                print("❌ Use assim: r 3")
            continue

        if cmd.isdigit():
            escolha = int(cmd)
            if 1 <= escolha <= total:
                station = favorites[escolha - 1]
                ok, message, item = tune_station(station)
                if not ok:
                    print(message)
                else:
                    print(f"✅ Tocando favorito: {item['name']}")
                return

        print("❌ Opção inválida.")


if __name__ == "__main__":
    listar_e_tocar_favoritos()
