"""
Main entry point for Cartesia.

Run with: python -m cartesia
"""
import sys
from .engine.game import main

if __name__ == "__main__":
    sys.exit(main())
