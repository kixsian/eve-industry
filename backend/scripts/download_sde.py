#!/usr/bin/env python3
"""
Download the Fuzzwork EVE SDE dump and extract it.
https://www.fuzzwork.co.uk/dump/latest/
"""
import bz2
import requests
from pathlib import Path

SDE_URL = "https://www.fuzzwork.co.uk/dump/latest/eve.db.bz2"
SDE_DIR = Path(__file__).parent.parent / "sde"
SDE_DB = SDE_DIR / "eve.db"


def download_sde():
    print(f"Downloading SDE from {SDE_URL}...")
    SDE_DIR.mkdir(exist_ok=True)

    response = requests.get(SDE_URL, stream=True)
    response.raise_for_status()

    bz2_path = SDE_DIR / "eve.db.bz2"
    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    with open(bz2_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                print(f"\r  {downloaded / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} MB", end="", flush=True)
    print()

    print("Extracting...")
    with bz2.open(bz2_path, "rb") as src, open(SDE_DB, "wb") as dst:
        while chunk := src.read(65536):
            dst.write(chunk)

    bz2_path.unlink()
    print(f"✓ SDE database at {SDE_DB}")


if __name__ == "__main__":
    download_sde()
