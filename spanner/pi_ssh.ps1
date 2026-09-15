# Non-interactive SSH helper for the weather station Pi (rpi4b-weather), using a
# dedicated automation key so no password ever needs to be typed or piped in.
#
# One-time setup (already done on this machine):
#   ssh-keygen -t ed25519 -f $HOME\.ssh\claude_rpi4b_weather -N '""' -C "claude-code-automation"
#   # then append $HOME\.ssh\claude_rpi4b_weather.pub to ~/.ssh/authorized_keys on the Pi
#
# Usage:
#   .\spanner\pi_ssh.ps1 'systemctl status weather_web nginx weather_daq --no-pager'
#   .\spanner\pi_ssh.ps1 'sudo tail -n 50 /var/log/nginx/error.log'
param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$Command
)

$Key = Join-Path $HOME ".ssh\claude_rpi4b_weather"
$KnownHosts = Join-Path $HOME ".ssh\known_hosts_pi"
$RemoteHost = "klm@rpi4b-weather"

if (-not (Test-Path $Key)) {
    Write-Error "Missing automation key at $Key - see setup instructions in this script's header."
    exit 1
}

$remoteCommand = $Command -join ' '

ssh -i $Key `
    -o BatchMode=yes `
    -o UserKnownHostsFile=$KnownHosts `
    -o StrictHostKeyChecking=yes `
    $RemoteHost $remoteCommand
