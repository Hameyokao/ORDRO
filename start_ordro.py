"""Safe launcher for Ordro POS.
Run with: python start_ordro.py
This avoids Windows PATH issues with the `streamlit` command.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"

if not APP.exists():
    raise FileNotFoundError(f"Cannot find app.py in {ROOT}")

cmd = [sys.executable, "-m", "streamlit", "run", str(APP)]
raise SystemExit(subprocess.call(cmd, cwd=str(ROOT)))
