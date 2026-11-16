#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--mix"]:
        args = args[1:]
    if not " ".join(args).strip():
        from media_control import main
        sys.argv[1:] = ["play"]
        sys.exit(main())
    sys.exit(subprocess.call([sys.executable, str(Path(__file__).with_name("youtube_queue.py")), "play", *args]))
