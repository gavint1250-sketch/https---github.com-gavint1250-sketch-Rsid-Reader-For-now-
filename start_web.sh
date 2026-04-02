#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start_web.sh  —  Linux / macOS production startup script
#
# What this script does:
#   1. Installs Flask and all analysis dependencies into the self-contained
#      libs/ directory (same isolation pattern as the desktop app).
#   2. Starts the server using gunicorn (recommended) or falls back to the
#      Flask development server.
#
# For public internet deployment, place nginx in front of gunicorn to handle
# TLS (HTTPS).  See the nginx configuration template at the bottom of this
# file.
#
# Usage:
#   bash start_web.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing dependencies into libs/ ..."
python3 -m pip install --target libs/ flask --quiet
python3 -m pip install --target libs/ -r requirements_web.txt \
    --index-url https://download.pytorch.org/whl/cpu \
    --quiet || \
python3 -m pip install --target libs/ -r requirements_web.txt \
    --break-system-packages \
    --index-url https://download.pytorch.org/whl/cpu \
    --quiet

echo "==> Starting server ..."

if python3 -c "import gunicorn" 2>/dev/null; then
    # ── Production: gunicorn ─────────────────────────────────────────────────
    # --workers 1   : GPT-2 loads ~500 MB per worker process.  One worker
    #                 prevents multiplying that cost for each worker.
    # --threads 4   : Handles concurrent requests within the single process.
    #                 PyTorch releases the GIL during inference so threads work.
    # --timeout 300 : 5-minute timeout covers worst-case GPT-2 analysis.
    # --bind 127.0.0.1:5000 : Bind to localhost only; nginx handles public
    #                         traffic and TLS.
    echo "    Using gunicorn  (http://127.0.0.1:5000)"
    exec python3 -m gunicorn \
        --workers 1 \
        --threads 4 \
        --bind 127.0.0.1:5000 \
        --timeout 300 \
        "web_app:create_app()"
else
    # ── Fallback: Flask development server ───────────────────────────────────
    echo "    gunicorn not found — using Flask dev server."
    echo "    Install gunicorn for production:  pip install gunicorn"
    echo "    Access at http://0.0.0.0:5000"
    python3 web_app.py
fi

# ═════════════════════════════════════════════════════════════════════════════
# NGINX CONFIGURATION TEMPLATE
# ═════════════════════════════════════════════════════════════════════════════
# Save this block as /etc/nginx/sites-available/integrity-analyzer and
# symlink it to /etc/nginx/sites-enabled/.
#
# Replace "your-domain.edu" with your actual domain name.
# Use Certbot (https://certbot.eff.org) to obtain a free Let's Encrypt cert:
#   sudo certbot --nginx -d your-domain.edu
#
# server {
#     listen 443 ssl;
#     server_name your-domain.edu;
#
#     ssl_certificate     /etc/letsencrypt/live/your-domain.edu/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.edu/privkey.pem;
#
#     # Must match MAX_CONTENT_LENGTH in web/app.py (200 MB)
#     client_max_body_size 200m;
#
#     location / {
#         proxy_pass         http://127.0.0.1:5000;
#         proxy_read_timeout 360s;   # must exceed the longest GPT-2 analysis
#         proxy_set_header   Host $host;
#         proxy_set_header   X-Real-IP $remote_addr;
#     }
# }
#
# # Redirect plain HTTP to HTTPS (required for FERPA compliance)
# server {
#     listen 80;
#     server_name your-domain.edu;
#     return 301 https://$host$request_uri;
# }
