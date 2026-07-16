#!/usr/bin/env python
"""
One-click launcher for the Config Assessment Tool.

- Creates a .venv if it doesn't exist
- Installs requirements
- Starts the Flask UI (webapp.app)
"""

import argparse
import os
import platform
import shutil
import sys
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent             # compare-plugin/
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
MIN_PYTHON = (3, 8)


def get_venv_python() -> Path:
    if os.name == "nt":  # Windows
        return VENV_DIR / "Scripts" / "python.exe"
    else:                # macOS / Linux
        return VENV_DIR / "bin" / "python"


def _excel_status() -> str:
    system = platform.system()
    if system == "Darwin":
        candidates = [
            Path("/Applications/Microsoft Excel.app"),
            Path.home() / "Applications" / "Microsoft Excel.app",
        ]
        found = next((path for path in candidates if path.exists()), None)
        if found:
            return f"Found at {found}"
        return "Not found in /Applications. Excel is only needed for fallback workbook recalculation."

    if system == "Windows":
        if shutil.which("excel"):
            return "Found on PATH"
        return "Not found on PATH. This is common; Excel may still be installed."

    return "Not checked on this OS. Excel fallback is only expected on macOS/Windows."


def print_compatibility_check() -> bool:
    system = platform.system() or "Unknown"
    machine = platform.machine() or "Unknown"
    python_ok = sys.version_info >= MIN_PYTHON
    python_version = platform.python_version()
    python_bits = platform.architecture()[0]
    requirements_status = "Found" if REQUIREMENTS.exists() else "Missing"
    root_writable = os.access(ROOT, os.W_OK)

    print("Config Assessment Tool compatibility check")
    print("=" * 49)
    print(f"Folder: {ROOT}")
    print(f"Operating system: {system} {platform.release()}")
    if system == "Darwin":
        print(f"macOS version: {platform.mac_ver()[0] or 'Unknown'}")
    print(f"CPU architecture: {machine}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {python_version} ({python_bits})")
    print(f"requirements.txt: {requirements_status}")
    print(f"Writable folder: {'Yes' if root_writable else 'No'}")
    print(f"Virtual environment: {VENV_DIR}")
    print(f"Excel check: {_excel_status()}")

    print("\nAssessment")
    print("-" * 10)
    if python_ok:
        print(f"OK: Python {python_version} meets the minimum {MIN_PYTHON[0]}.{MIN_PYTHON[1]} requirement.")
    else:
        print(f"WARNING: Python {python_version} is older than {MIN_PYTHON[0]}.{MIN_PYTHON[1]}. Install a newer Python 3.")

    if system == "Darwin":
        if machine == "arm64":
            print("OK: Apple Silicon Mac detected. This should run natively with the current Python.")
        elif machine == "x86_64":
            print("INFO: Intel/Rosetta Python detected. It should run, but Apple Silicon users may prefer arm64 Python.")
        else:
            print("INFO: macOS architecture is unusual; test the launcher before sharing with users.")
    elif system == "Windows":
        if machine.upper() in {"AMD64", "X86_64"}:
            print("OK: Standard 64-bit Windows architecture detected.")
        elif machine.upper() == "ARM64":
            print("INFO: Windows ARM64 detected. Python packages may need extra testing.")
        else:
            print("INFO: Windows architecture is unusual; test dependency installation.")

    if not REQUIREMENTS.exists():
        print("WARNING: requirements.txt was not found. Dependency installation will be skipped.")
    if not root_writable:
        print("WARNING: This folder is not writable. The tool needs to create .venv, uploads, tmp, logs, and results.")

    return python_ok and REQUIREMENTS.exists() and root_writable


def ensure_venv():
    venv_python = get_venv_python()
    if not VENV_DIR.exists() or not venv_python.exists():
        if VENV_DIR.exists():
            print("Removing incomplete virtual environment...")
            import shutil
            shutil.rmtree(VENV_DIR)
        print("Creating virtual environment in .venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("Using existing virtual environment .venv")


def ensure_requirements(venv_python: Path):
    if REQUIREMENTS.exists():
        print("Installing dependencies from requirements.txt ...")
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    else:
        print("WARNING: requirements.txt not found; skipping dependency install.")


def main():
    parser = argparse.ArgumentParser(description="Start the Config Assessment Tool web UI.")
    parser.add_argument(
        "--check",
        "--compatibility-check",
        action="store_true",
        help="print system compatibility information and exit",
    )
    args = parser.parse_args()

    os.chdir(ROOT)

    compatible = print_compatibility_check()
    if args.check:
        raise SystemExit(0 if compatible else 1)

    print()
    ensure_venv()
    venv_python = get_venv_python()
    if not venv_python.exists():
        raise SystemExit(f"Could not find venv Python at: {venv_python}")

    ensure_requirements(venv_python)

    # Run the Flask app as a module so `compare_tool` imports work
    print("Starting Config Assessment Tool on http://127.0.0.1:5000 ...")
    subprocess.check_call([str(venv_python), "-m", "webapp.app"])


if __name__ == "__main__":
    main()
