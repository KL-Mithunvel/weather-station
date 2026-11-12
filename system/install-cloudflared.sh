#!/usr/bin/env bash
# Install cloudflared from Cloudflare's signed apt repository. Run ON the Pi:
#   sudo bash system/install-cloudflared.sh
#
# This only installs the program. It does NOT create or start a tunnel - that
# needs a tunnel token from your Cloudflare Zero Trust dashboard, see weather.MD
# ("Public access via Cloudflare Tunnel"). The tunnel is OUTBOUND-only: no port
# is opened or forwarded on the router.
set -euo pipefail

[ "$(id -u)" = 0 ] || { echo "Run as root: sudo bash $0"; exit 1; }

install -d -m 755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' \
    > /etc/apt/sources.list.d/cloudflared.list

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cloudflared
cloudflared --version
