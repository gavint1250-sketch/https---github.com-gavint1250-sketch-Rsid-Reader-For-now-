#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start_web.sh  —  Linux / macOS startup script
#
# ACCESS OPTIONS (choose one):
#
#   A) Local only     — no extra setup, open http://localhost:5000
#
#   B) Same network   — others on your Wi-Fi/LAN use http://<your-IP>:5000
#
#   C) Any network (quick share) — install ngrok (free), then re-run:
#        https://ngrok.com → create account → download → ngrok config add-authtoken <token>
#        This script will detect ngrok automatically and print a public URL.
#
#   D) Any network (permanent/production) — deploy on a VPS with nginx + TLS.
#        See the nginx template at the bottom of this file.
#
# Usage:
#   bash start_web.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Install dependencies ──────────────────────────────────────────────────────
echo "==> Installing / updating dependencies into libs/ ..."
python3 -m pip install --target libs/ flask --quiet

python3 -m pip install --target libs/ -r requirements_web.txt \
    --index-url https://download.pytorch.org/whl/cpu \
    --quiet \
|| python3 -m pip install --target libs/ -r requirements_web.txt \
    --break-system-packages \
    --index-url https://download.pytorch.org/whl/cpu \
    --quiet

# ── Choose server ─────────────────────────────────────────────────────────────
if python3 -c "import gunicorn" 2>/dev/null; then
    SERVER="gunicorn"
else
    SERVER="flask"
fi

# ── Detect ngrok ──────────────────────────────────────────────────────────────
USE_NGROK=0
if command -v ngrok &>/dev/null; then
    USE_NGROK=1
fi

# ── Start ────────────────────────────────────────────────────────────────────
if [ "$USE_NGROK" -eq 1 ]; then
    echo "==> ngrok detected — starting public tunnel..."
    echo "    The public URL will appear below once the tunnel opens."
    echo "    Share that URL with anyone on any network."
    echo "    Press Ctrl+C to stop."
    echo ""

    # Start Flask / gunicorn in the background
    if [ "$SERVER" = "gunicorn" ]; then
        python3 -m gunicorn \
            --workers 1 --threads 4 \
            --bind 127.0.0.1:5000 \
            --timeout 300 \
            --daemon \
            --pid /tmp/integrity-analyzer.pid \
            "web_app:create_app()"
    else
        python3 web_app.py &
        echo $! > /tmp/integrity-analyzer.pid
    fi

    # Give the server a moment to start
    sleep 2

    # Start ngrok in the foreground so the URL is visible
    trap 'kill $(cat /tmp/integrity-analyzer.pid 2>/dev/null) 2>/dev/null; rm -f /tmp/integrity-analyzer.pid' EXIT
    ngrok http 5000

else
    # No ngrok — run server directly
    echo "==> Starting server..."
    echo ""

    if [ "$SERVER" = "gunicorn" ]; then
        echo "    Using gunicorn  (http://0.0.0.0:5000)"
        echo "    Others on your network can use http://$(hostname -I | awk '{print $1}'):5000"
        echo ""
        echo "    To allow access from OTHER networks, install ngrok:"
        echo "      https://ngrok.com  (free, takes 2 minutes)"
        echo "    Then re-run this script."
        echo ""
        echo "    Press Ctrl+C to stop."
        exec python3 -m gunicorn \
            --workers 1 --threads 4 \
            --bind 0.0.0.0:5000 \
            --timeout 300 \
            "web_app:create_app()"
    else
        echo "    Using Flask dev server  (http://0.0.0.0:5000)"
        echo "    Others on your network can use http://$(hostname -I | awk '{print $1}'):5000"
        echo ""
        echo "    TIP: Install gunicorn for production:  pip install gunicorn"
        echo "    TIP: Install ngrok for public access:  https://ngrok.com"
        echo ""
        echo "    Press Ctrl+C to stop."
        python3 web_app.py
    fi
fi

# ═════════════════════════════════════════════════════════════════════════════
# PERMANENT PUBLIC DEPLOYMENT — nginx + TLS (Option D)
# ═════════════════════════════════════════════════════════════════════════════
#
# For a permanent institution URL (e.g. https://integrity.youruniversity.edu):
#
# 1. Point a domain at your server's public IP.
# 2. Install nginx and certbot:
#      sudo apt install nginx certbot python3-certbot-nginx
# 3. Get a free TLS certificate:
#      sudo certbot --nginx -d your-domain.edu
# 4. Save the block below as /etc/nginx/sites-available/integrity-analyzer
#    and symlink it: sudo ln -s /etc/nginx/sites-available/integrity-analyzer \
#                                /etc/nginx/sites-enabled/
# 5. Run this script normally — gunicorn will bind to 127.0.0.1 (not public),
#    nginx handles all public HTTPS traffic.
#
# ── nginx config template ─────────────────────────────────────────────────────
#
# server {
#     listen 443 ssl;
#     server_name your-domain.edu;
#
#     ssl_certificate     /etc/letsencrypt/live/your-domain.edu/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.edu/privkey.pem;
#
#     client_max_body_size 200m;
#
#     location / {
#         proxy_pass         http://127.0.0.1:5000;
#         proxy_read_timeout 360s;
#         proxy_set_header   Host $host;
#         proxy_set_header   X-Real-IP $remote_addr;
#     }
# }
#
# server {
#     listen 80;
#     server_name your-domain.edu;
#     return 301 https://$host$request_uri;
# }
