#!/usr/bin/env python3
"""
Download the Fuzzwork EVE SDE dump and extract it.
https://www.fuzzwork.co.uk/dump/
"""
import requests
import sqlite3
import os
import sys
from pathlib import Path

SDE_URL = "https://www.fuzzwork.co.uk/dump/sqlite-latest.tar.bz2"
SDE_DIR = Path(__file__).parent.parent / "sde"
SDE_DB = SDE_DIR / "eve.db"


def download_sde():
    print(f"Downloading SDE from {SDE_URL}...")
    SDE_DIR.mkdir(exist_ok=True)

    response = requests.get(SDE_URL, stream=True)
    response.raise_for_status()

    tar_path = SDE_DIR / "sde.tar.bz2"
    with open(tar_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded to {tar_path}")

    # Extract
    import tarfile
    print("Extracting...")
    with tarfile.open(tar_path, "r:bz2") as tar:
        tar.extractall(SDE_DIR)

    # Find and move eve.db
    for root, dirs, files in os.walk(SDE_DIR):
        for file in files:
            if file == "eve.db":
                src = os.path.join(root, file)
                if src != str(SDE_DB):
                    os.rename(src, SDE_DB)
                print(f"SDE database at {SDE_DB}")
                break

    # Cleanup
    tar_path.unlink()
    for root, dirs, files in os.walk(SDE_DIR):
        for dir_ in dirs:
            if dir_ not in ["."]:
                import shutil
                try:
                    shutil.rmtree(os.path.join(root, dir_))
                except:
                    pass

    print("✓ SDE setup complete")


if __name__ == "__main__":
    download_sde()
