#!/usr/bin/env python3
"""
Quick launcher for the modernized Cartesia.

Usage: python play.py
or:    ./play.py
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from cartesia.engine.game import main

if __name__ == "__main__":
    main()
