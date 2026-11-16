#!/usr/bin/env python3
"""Artist searches use the same immediate, noninteractive YouTube pipeline."""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, str(Path(__file__).with_name("youtube_queue.py")), "play", *sys.argv[1:]]))
