#!/usr/bin/env bash
# One-time OS hardening for the weather Pi. Idempotent - safe to re-run.
# Run ON the Pi:   sudo bash system/harden.sh
#
# What it does:
#   1. Installs ufw, fail2ban, unattended-upgrades.
#   2. SSH: no root login, 3 auth tries, short login grace. Password login stays
#      ON because spanner/release.bat and upload.bat use it - move them to a key,
#      then set "PasswordAuthentication no" in the drop-in below.
#   3. Firewall: default-deny inbound. SSH (22), the web page (80) and mDNS (5353)
#      are allowed from the LAN only. Everything else, including gunicorn's 8000,
#      is closed. Outbound is unrestricted (the Cloudflare Tunnel is outbound).
#   4. fail2ban on sshd.
#   5. Automatic SECURITY updates only (Debian-Security), at 02:30 so they finish
#      before the 03:30 reboot. No automatic reboot from apt - the daily reboot
#      already covers it. Kernel/firmware (Raspberry Pi archive) stay manual.
#
# Lock-out protection: before the firewall is enabled, a one-shot timer is armed
# that disables it again after 5 minutes. After checking that a NEW ssh
# connection works, cancel it:   sudo systemctl stop weather-ufw-rollback.timer
set -euo pipefail

[ "$(id -u)" = 0 ] || { echo "Run as root: sudo bash $0"; exit 1; }

# The LAN the Pi sits on (e.g. 192.168.16.0/24), unless overridden.
LAN="${LAN_CIDR:-$(ip -4 -o route show scope link | awk '!/169.254/ {print $1; exit}')}"
if ! echo "$LAN" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$'; then
    echo "Could not determine the LAN CIDR (got '$LAN'). Re-run with LAN_CIDR=192.168.x.0/24"
    exit 1
fi
echo "LAN allowed through the firewall: $LAN (and IPv6 link-local fe80::/10)"

export DEBIAN_FRONTEND=noninteractive
echo "== 1/5 packages"
apt-get update -qq
apt-get install -y -qq ufw fail2ban unattended-upgrades

echo "== 2/5 sshd hardening"
install -d -m 755 /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/10-weather-hardening.conf <<'EOF'
# Managed by system/harden.sh
PermitRootLogin no
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
# Once release.bat/upload.bat use a key, uncomment:
# PasswordAuthentication no
EOF
if sshd -t; then
    systemctl reload ssh
    echo "sshd config valid, reloaded."
else
    rm -f /etc/ssh/sshd_config.d/10-weather-hardening.conf
    echo "ERROR: sshd rejected the drop-in; removed it. sshd unchanged."
    exit 1
fi

echo "== 3/5 fail2ban"
cat > /etc/fail2ban/jail.d/weather-sshd.local <<'EOF'
# Managed by system/harden.sh
[sshd]
enabled  = true
backend  = systemd
maxretry = 5
findtime = 10m
bantime  = 30m
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban

echo "== 4/5 unattended security upgrades"
cat > /etc/apt/apt.conf.d/52weather-unattended <<'EOF'
// Managed by system/harden.sh - security updates only.
#clear Unattended-Upgrade::Origins-Pattern;
Unattended-Upgrade::Origins-Pattern {
    "origin=Debian,codename=${distro_codename}-security,label=Debian-Security";
    "origin=Debian,codename=${distro_codename},label=Debian-Security";
};
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Dependencies "false";
EOF
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
install -d /etc/systemd/system/apt-daily-upgrade.timer.d
cat > /etc/systemd/system/apt-daily-upgrade.timer.d/weather.conf <<'EOF'
[Timer]
OnCalendar=
OnCalendar=*-*-* 02:30
RandomizedDelaySec=10m
EOF
systemctl daemon-reload
systemctl enable --now apt-daily.timer apt-daily-upgrade.timer
unattended-upgrade --dry-run 2>&1 | tail -3 || true

echo "== 5/5 firewall"
ufw default deny incoming
ufw default allow outgoing
ufw allow from "$LAN" to any port 22 proto tcp comment 'ssh (LAN)'
ufw allow from fe80::/10 to any port 22 proto tcp comment 'ssh (IPv6 link-local)'
ufw allow from "$LAN" to any port 80 proto tcp comment 'web (LAN)'
ufw allow from fe80::/10 to any port 80 proto tcp comment 'web (IPv6 link-local)'
ufw allow from "$LAN" to any port 5353 proto udp comment 'mDNS hostname (LAN)'
ufw allow from fe80::/10 to any port 5353 proto udp comment 'mDNS hostname (IPv6 link-local)'
ufw logging low

# Dead-man switch against lock-out.
systemctl stop weather-ufw-rollback.timer 2>/dev/null || true
systemd-run --unit=weather-ufw-rollback --on-active=300 /usr/sbin/ufw --force disable >/dev/null
ufw --force enable
ufw status verbose

cat <<EOF

Firewall is ON. SAFETY TIMER ARMED: it disables the firewall again in 5 minutes.
1. Open a NEW ssh session from your PC and confirm it works.
2. Then cancel the timer:   sudo systemctl stop weather-ufw-rollback.timer
EOF
