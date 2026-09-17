$ErrorActionPreference = "Stop"

$repo = (Resolve-Path $PSScriptRoot).Path
if ($repo.Length -lt 3 -or $repo[1] -ne ':') {
    throw "Run this launcher from a Windows filesystem path."
}

$drive = $repo.Substring(0, 1).ToLowerInvariant()
$relative = $repo.Substring(2).Replace('\', '/')
$wslRepo = "/mnt/$drive$relative"

$command = "export CTFHIVE_WORKSPACE=/tmp/ctfhive/challenges; " +
           "export CTFHIVE_EVIDENCE=/tmp/ctfhive/evidence; " +
           "export CTFHIVE_KNOWLEDGE=/tmp/ctfhive/knowledge.sqlite3; " +
           "cd '$wslRepo'; exec python3 -m ctfhive.tui"

& wsl.exe -d kali-linux -- bash -lc $command
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
