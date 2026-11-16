#!/usr/bin/env python3
import os
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher

BASE_DIR = os.path.expanduser("~/porco-music-bot")
DL_DIR = os.path.join(BASE_DIR, "dl")
COOKIES = os.path.join(BASE_DIR, "youtube-cookies.txt")
MIN_SEC, MAX_SEC, SONGS_N = 35, 480, 10
NOISE = {"topic", "vevo", "official", "oficial", "music", "musica", "channel"}
PRINT = "%(id)s\t%(title)s\t%(duration)s\t%(channel)s\t%(channel_id)s"


def fold(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def name_score(query, name):
    a, b = fold(query), fold(name)
    if not a or not b:
        return 0.0
    r = SequenceMatcher(None, a, b).ratio()
    qa, qb = set(a.split()), set(b.split())
    if qa & qb:
        r += 0.18
    last = a.split()[-1]
    if last in qb:
        r += 0.22
    elif len(a.split()) > 1:
        r -= 0.3
    if "topic" in b:
        r += 0.12
    return r


def same_artist(picked, channel):
    p, c = fold(picked), fold(channel)
    if not p or not c or c == "na":
        return False
    pt = [t for t in p.split() if t not in NOISE]
    ct = {t for t in c.split() if t not in NOISE}
    if pt and all(t in ct for t in pt):
        return True
    if len(p) >= 5 and p in c:
        return True
    return name_score(picked, channel) >= 0.88


def ytdlp_cmd(*extra):
    cmd = ["yt-dlp", "--no-warnings", "--ignore-errors", "--no-check-certificates"]
    if os.path.isfile(COOKIES):
        cmd.extend(["--cookies", COOKIES])
    cmd.extend(extra)
    return cmd


def run_ytdlp(args, timeout=90):
    r = subprocess.run(
        ytdlp_cmd(*args),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]


def similar_artists(query, limit=10):
    lines = run_ytdlp(
        ["--flat-playlist", "--print", "%(channel)s\t%(channel_id)s", f"ytsearch25:{query}"],
        timeout=120,
    )
    lines += run_ytdlp(
        ["--flat-playlist", "--print", "%(channel)s\t%(channel_id)s", f"ytsearch8:{query} Topic"],
        timeout=90,
    )
    ranked, seen = [], set()
    for ln in lines:
        parts = ln.split("\t")
        name = (parts[0] if parts else "").strip()
        cid = parts[1].strip() if len(parts) > 1 and parts[1] != "NA" else ""
        key = cid or fold(name)
        if not key or key in seen or not name or name.upper() == "NA":
            continue
        sc = name_score(query, name)
        if sc < 0.5:
            continue
        seen.add(key)
        ranked.append((sc, name, cid))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [{"name": n, "channel_id": c} for _, n, c in ranked[:limit]]


def _scan(url, end):
    return run_ytdlp(
        [
            "--flat-playlist",
            "--match-filter",
            f"duration>={MIN_SEC} & duration<={MAX_SEC} & !is_live",
            "--playlist-end",
            str(end),
            "--print",
            PRINT,
            url,
        ],
        timeout=120,
    )


def _take(lines, artist, n, seen):
    songs = []
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) < 5:
            continue
        vid, title, dur, ch, cid = parts[:5]
        if not vid or vid in seen or title.upper() == "NA":
            continue
        if not same_artist(artist, ch):
            continue
        if dur.isdigit():
            d = int(dur)
            if d < MIN_SEC or d > MAX_SEC:
                continue
        seen.add(vid)
        songs.append(
            {
                "id": vid,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "channel": ch,
                "channel_id": cid,
            }
        )
        if len(songs) >= n:
            break
    return songs


def list_songs(artist, n=SONGS_N, channel_id=""):
    seen, songs = set(), []
    if channel_id:
        songs = _take(_scan(f"https://www.youtube.com/channel/{channel_id}/videos", n + 20), artist, n, seen)
    if len(songs) < n:
        extra = _take(_scan(f'ytsearch{n + 18}:"{artist}"', n + 18), artist, n - len(songs), seen)
        songs.extend(extra)
    return songs


def download_audio(url, video_id):
    os.makedirs(DL_DIR, exist_ok=True)
    tmpl = os.path.join(DL_DIR, "%(id)s.%(ext)s")
    out = run_ytdlp(
        [
            "-f",
            "bestaudio/best",
            "-o",
            tmpl,
            "--no-playlist",
            "--print",
            "after_move:filepath",
            url,
        ],
        timeout=180,
    )
    for ln in out:
        if os.path.isfile(ln):
            return ln
    for name in os.listdir(DL_DIR):
        if name.startswith(video_id + "."):
            return os.path.join(DL_DIR, name)
    return ""
