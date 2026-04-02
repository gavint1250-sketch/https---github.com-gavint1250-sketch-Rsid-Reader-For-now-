"""
Web entry point for the Document Integrity Analyzer.

Mirrors the bootstrap in Main.py exactly:
  - Adds libs/ to sys.path so all pip packages installed there are importable.
  - Sets NLTK_DATA, HF_HOME, TRANSFORMERS_CACHE before any heavy imports so
    model data stays inside the self-contained libs/ directory.

Does NOT import modules/dependency_checker.py — that module imports tkinter at
the top level and would crash on headless Linux servers.

Usage
-----
Development (any platform):
    python3 web_app.py

Production (Linux, after installing gunicorn):
    bash start_web.sh
"""

import os
import sys

# ── Isolated library directory ─────────────────────────────────────────────
# All pip packages are installed here.  Mirrors Main.py so the same libs/
# directory works for both the desktop app and the web app.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
LIBS_DIR = os.path.join(_APP_DIR, "libs")
os.makedirs(LIBS_DIR, exist_ok=True)
if LIBS_DIR not in sys.path:
    sys.path.insert(0, LIBS_DIR)

# Point NLTK and HuggingFace caches into libs/ — must be set before any
# import of transformers or nltk.
os.environ.setdefault("NLTK_DATA",          os.path.join(LIBS_DIR, "nltk_data"))
os.environ.setdefault("HF_HOME",            os.path.join(LIBS_DIR, "hf_cache"))
os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(LIBS_DIR, "hf_cache"))

# ── Flask app ─────────────────────────────────────────────────────────────
from web.app import create_app  # noqa: E402  (import after path setup)

# Re-export create_app at module level so gunicorn / waitress can call it:
#   gunicorn "web_app:create_app()"
#   waitress-serve --call web_app:create_app


def main():
    app = create_app()
    # host='0.0.0.0' makes the server reachable from any network interface.
    # In production, nginx/IIS sits in front and handles TLS; the WSGI server
    # binds to 127.0.0.1 only (see start_web.sh / start_web.bat).
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
