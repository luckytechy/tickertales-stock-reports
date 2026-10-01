#!/usr/bin/env python3
"""
Turn templates/logo.png into templates/logo.txt (a base64 data URI).

The page builders embed the logo inline so each report is a single
self-contained HTML file with no external image dependency.

Drop any PNG at templates/logo.png and this picks it up. If no PNG is
present, nothing happens and the pages fall back to the yellow
"Ticker Tales" wordmark - which still looks correct, just without the mark.

Runs automatically in the workflow. To run by hand:
    python scripts/prepare_logo.py
"""
import base64
import os

SRC_CANDIDATES = [
    "templates/logo.png",
    "templates/logo-nobg-1024.png",
    "templates/logo.jpg",
]
DEST = "templates/logo.txt"

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def main():
    src = next((p for p in SRC_CANDIDATES if os.path.exists(p)), None)

    if src is None:
        if os.path.exists(DEST):
            print(f"No source image found, but {DEST} already exists - keeping it.")
        else:
            print("No logo image found. Pages will use the text wordmark only.")
            print("To add one: drop a PNG at templates/logo.png and re-run.")
        return

    ext = os.path.splitext(src)[1].lower()
    mime = MIME.get(ext, "image/png")

    raw = open(src, "rb").read()
    size_kb = len(raw) / 1024

    # A very large logo bloats every generated page, since it is inlined.
    if size_kb > 300:
        print(f"WARNING: {src} is {size_kb:.0f} KB. It is embedded into every "
              f"report, so consider resizing it to roughly 240x240 px.")

    uri = f"data:{mime};base64," + base64.b64encode(raw).decode()
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    open(DEST, "w").write(uri)
    print(f"Converted {src} ({size_kb:.0f} KB) -> {DEST} ({len(uri):,} chars)")


if __name__ == "__main__":
    main()
