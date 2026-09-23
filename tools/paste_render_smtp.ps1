# Paste Gmail app password from clipboard into Render SMTP_PASSWORD (one-time).
# Requires RENDER_API_KEY in env, or you will be prompted.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$password = (Get-Clipboard -Raw).Trim()
if (-not $password) {
    Write-Error "Clipboard is empty. Copy your Gmail App Password first."
}
if ($password.Length -lt 16) {
    Write-Warning "Expected ~16 characters; got $($password.Length). Continuing anyway."
}
if (-not $env:RENDER_API_KEY) {
    $env:RENDER_API_KEY = Read-Host "Render API key (dashboard.render.com → Account Settings → API Keys)"
}
$env:SMTP_PASSWORD = $password
python "$root\tools\set_render_smtp.py"
Remove-Item Env:SMTP_PASSWORD -ErrorAction SilentlyContinue
