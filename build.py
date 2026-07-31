"""
Release build script for Navidrome Mix Studio.

Cleans generated files and creates a release build
using PyInstaller.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent


# Completely remove build output directories
REMOVE_DIRECTORIES = [
    "build",
    "dist",
]


# Runtime generated data directories
# Keep directory, remove contents only.
CLEAN_CONTENT_DIRECTORIES = [
    "data",
    "logs",
    "reports",
]


KEEP_TRANSLATIONS = {
    "ja.json",
    "en.json",
}


def remove_directory(path: Path) -> None:
    """Remove directory completely."""

    if path.exists():
        print(f"Removing: {path}")
        shutil.rmtree(path)


def clean_directory_contents(path: Path) -> None:
    """Remove contents but keep directory."""

    if not path.exists():
        return

    print(f"Cleaning: {path}")

    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def remove_python_cache(root: Path) -> None:
    """Remove Python cache files."""

    for cache in root.rglob("__pycache__"):
        if cache.is_dir():
            print(f"Removing cache: {cache}")
            shutil.rmtree(cache)

    for pyc in root.rglob("*.pyc"):
        if pyc.is_file():
            print(f"Removing bytecode: {pyc}")
            pyc.unlink()


def clean_translations() -> None:
    """Keep only official translation files."""

    translation_dir = (
        ROOT / "resources" / "translations"
    )

    if not translation_dir.exists():
        return

    print("Cleaning translations...")

    for file in translation_dir.glob("*.json"):
        if file.name not in KEEP_TRANSLATIONS:
            print(f"Removing translation: {file}")
            file.unlink()


def check_version_file() -> None:
    """Check required build files."""

    version_file = ROOT / "version_info.txt"

    if not version_file.exists():
        raise FileNotFoundError(
            "version_info.txt was not found."
        )


def run_pyinstaller() -> None:
    """Execute PyInstaller."""

    spec_file = ROOT / "main.spec"

    if not spec_file.exists():
        raise FileNotFoundError(
            "main.spec was not found."
        )

    print("Building application...")
    print(f"Using spec: {spec_file}")

    subprocess.run(
        [
            "pyinstaller",
            str(spec_file),
            "--noconfirm",
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    """Execute release build."""

    print(
        "=== Navidrome Mix Studio Release Build ==="
    )

    check_version_file()

    for directory in REMOVE_DIRECTORIES:
        remove_directory(ROOT / directory)

    for directory in CLEAN_CONTENT_DIRECTORIES:
        clean_directory_contents(ROOT / directory)

    remove_python_cache(ROOT)

    clean_translations()

    run_pyinstaller()

    print()
    print(
        "=== Build completed successfully ==="
    )
    print(
        f"Output: {ROOT / 'dist'}"
    )


if __name__ == "__main__":
    main()