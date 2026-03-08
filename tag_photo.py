#!/usr/bin/env python3
"""CLI entry point for photo-tagger (preserved for backward compatibility)."""

import sys
from src.photo_tagger.tagger import overlay_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python photo_tagger.py <image_path> [output_path]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    overlay_text(image_path, output_path)
