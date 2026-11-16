#!/usr/bin/env python3
"""play-radio-pais <pais> [filtro...]  ex: play-radio-pais brasil rock"""
import json
import sys
import urllib.parse
import urllib.request

from porco_logo import logo
from radio_state import tune_station

API_HOSTS = (
    "https://de1.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
    "https://at1.api.radio-browser.info",
)

# nome/alias -> ISO 3166-1 alpha-2
PAISES = {
    "br": "BR", "brasil": "BR", "brazil": "BR",
    "us": "US", "usa": "US", "eua": "US", "estadosunidos": "US", "unitedstates": "US",
    "ar": "AR", "argentina": "AR",
    "pt": "PT", "portugal": "PT",
    "es": "ES", "espanha": "ES", "spain": "ES",
    "mx": "MX", "mexico": "MX", "méxico": "MX",
    "cl": "CL", "chile": "CL",
    "co": "CO", "colombia": "CO", "colômbia": "CO",
    "uy": "UY", "uruguai": "UY", "uruguay": "UY",
    "py": "PY", "paraguai": "PY", "paraguay": "PY",
    "pe": "PE", "peru": "PE", "perú": "PE",
    "bo": "BO", "bolivia": "BO", "bolívia": "BO",
    "ve": "VE", "venezuela": "VE",
    "gb": "GB", "uk": "GB", "inglaterra": "GB", "reino unido": "GB", "uk": "GB",
    "de": "DE", "alemanha": "DE", "germany": "DE",
    "fr": "FR", "franca": "FR", "frança": "FR", "france": "FR",
    "it": "IT", "italia": "IT", "itália": "IT", "italy": "IT",
    "jp": "JP", "japao": "JP", "japão": "JP", "japan": "JP",
    "ca": "CA", "canada": "CA", "canadá": "CA",
    "au": "AU", "australia": "AU", "austrália": "AU",
}


def _norm(s):
    return (
        s.lower()
        .replace("ã", "a").replace("á", "a").replace("à", "a").replace("â", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u").replace("ü", "u")
        .replace("ç", "c")
        .strip()
    )


def resolve_country(token):
    t = _norm(token).replace(" ", "")
    if len(t) == 2 and t.isalpha():
        return t.upper()
    return PAISES.get(t)


def api_get(path_query):
    last = None
    for host in API_HOSTS:
        url = f"{host}{path_query}"
        req = urllib.request.Request(url, headers={"User-Agent": "PorcoBot/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            last = e
    raise RuntimeError(last or "API indisponivel")


def buscar_pais(pais_token, filtro=""):
    code = resolve_country(pais_token)
    if not code:
        # tenta country name na API
        code = None
        country_name = pais_token
    else:
        country_name = None

    params = {
        "order": "votes",
        "reverse": "true",
        "hidebroken": "true",
        "limit": "100",
    }
    if code:
        params["countrycode"] = code
    else:
        params["country"] = country_name

    if filtro:
        params["tag"] = filtro

    qs = urllib.parse.urlencode(params)
    stations = api_get(f"/json/stations/search?{qs}")

    # se tag nao achou nada, tenta name dentro do pais
    if filtro and not stations:
        params.pop("tag", None)
        params["name"] = filtro
        qs = urllib.parse.urlencode(params)
        stations = api_get(f"/json/stations/search?{qs}")

    # dedupe por url
    seen = set()
    clean = []
    for s in stations or []:
        url = (s.get("url_resolved") or s.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        clean.append(s)
    return clean, code or (country_name or pais_token).upper()


def escolher(stations, titulo):
    if not stations:
        logo()
        print(f"❌ Nenhuma rádio encontrada: {titulo}")
        return
    idx = 0
    passo = 10
    total = len(stations)
    while True:
        fim = min(idx + passo, total)
        logo()
        print(f"\n--- 🌍 {titulo} ({idx + 1}-{fim}/{total}) ---")
        for i, st in enumerate(stations[idx:fim], idx + 1):
            tags = (st.get("tags") or "")[:28]
            cc = st.get("countrycode") or "??"
            print(f"[{i}] {st.get('name', '?')[:42]} [{cc}] {tags}")
        print("-" * 45)
        print("[0] Cancelar")
        msg = "\n👉 Número"
        if idx + passo < total:
            msg += " | [m] Mais"
        if idx > 0:
            msg += " | [v] Voltar"
        msg += ": "
        cmd = input(msg).lower().strip()
        if cmd == "m" and idx + passo < total:
            idx += passo
        elif cmd == "v" and idx > 0:
            idx = max(0, idx - passo)
        elif cmd == "0":
            return
        elif cmd.isdigit():
            n = int(cmd)
            if 1 <= n <= total:
                ok, message, item = tune_station(stations[n - 1])
                if not ok:
                    print(message)
                else:
                    print(f"✅ Sintonizando: {item['name']}")
                return


def main(argv):
    if not argv:
        logo()
        print("💡 Uso: play-radio-pais <pais> [filtro]")
        print("   Ex.: play-radio-pais brasil")
        print("        play-radio-pais brasil rock")
        print("        play-radio-pais BR jazz")
        return
    pais = argv[0]
    filtro = " ".join(argv[1:]).strip()
    try:
        stations, label = buscar_pais(pais, filtro)
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return
    titulo = label if not filtro else f"{label} / {filtro}"
    escolher(stations, titulo)


if __name__ == "__main__":
    main(sys.argv[1:])
