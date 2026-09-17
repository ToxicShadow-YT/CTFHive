# CTFHive

CTFHive is a safety-first autonomous CTF orchestrator for authorized competitions. Its primary interface is a local terminal UI for Kali/WSL. It isolates challenge workspaces, records every tool execution as evidence, uses an OpenAI-compatible Ollama endpoint by default, and supports optional Claude CLI delegation for development workflows.

## Quick start

The primary application is the local terminal UI. Run it inside Kali WSL2, not with `python app.py`.

### Windows and WSL2 setup

Open PowerShell and verify Kali:

```powershell
wsl.exe --status
wsl.exe --list --verbose
```

If Kali is not installed, use Administrator PowerShell:

```powershell
wsl.exe --install --distribution kali-linux
```

Start Kali and enter the repository mounted from Windows:

```powershell
wsl.exe -d kali-linux
```

```bash
cd /mnt/c/Users/ashwi/Documents/project/hive
```

Keep challenge copies, evidence, and the SQLite knowledge database on the Linux filesystem. This avoids permission errors when `/mnt/c` is mounted through Windows DrvFS:

```bash
export CTFHIVE_WORKSPACE=/tmp/ctfhive/challenges
export CTFHIVE_EVIDENCE=/tmp/ctfhive/evidence
export CTFHIVE_KNOWLEDGE=/tmp/ctfhive/knowledge.sqlite3
```

Install the baseline CTF tools inside Kali:

```bash
apt-get update
apt-get install -y file binutils gdb ripgrep xxd python3-pip python3-venv
```

Run CTFHive:

```bash
python3 -m ctfhive.tui
```

Or launch it directly from PowerShell:

```powershell
wsl.exe -d kali-linux -- bash -lc "export CTFHIVE_WORKSPACE=/tmp/ctfhive/challenges; export CTFHIVE_EVIDENCE=/tmp/ctfhive/evidence; export CTFHIVE_KNOWLEDGE=/tmp/ctfhive/knowledge.sqlite3; cd /mnt/c/Users/ashwi/Documents/project/hive; python3 -m ctfhive.tui"
```

The repository also includes a launcher that avoids the Windows `python3` Store alias:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-ctfhive.ps1
```

### First test

From Kali, run diagnostics and the harmless fixture:

```bash
cd /mnt/c/Users/ashwi/Documents/project/hive
export CTFHIVE_WORKSPACE=/tmp/ctfhive/challenges
export CTFHIVE_EVIDENCE=/tmp/ctfhive/evidence
export CTFHIVE_KNOWLEDGE=/tmp/ctfhive/knowledge.sqlite3
python3 -m ctfhive.cli doctor
python3 -m ctfhive.tui --solve ./fixtures/hello.txt --real
```

The interactive menu also supports solving, evidence, tools, knowledge, and external-agent status. Mock mode is available with `python3 -m ctfhive.tui --solve ./fixtures/hello.txt`.

Windows virtual-environment commands also work for tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ctfhive.cli doctor
.\.venv\Scripts\python.exe -m ctfhive.tui
```

For a real local run with installed tools and Ollama, use `ctfhive tui --solve ./challenge --real`. The Streamlit dashboard remains optional and must be started with `streamlit run app.py`; `python app.py` is not a valid Streamlit launch command.

### Ollama placement

Do not install Ollama or a model inside Kali. Keep Ollama on the Windows host and let Kali/WSL2 connect to the Windows Ollama service at `http://127.0.0.1:11434/v1` when WSL localhost forwarding is enabled. Start Ollama on Windows, pull the model on Windows, then test from Kali:

```bash
curl http://127.0.0.1:11434/api/tags
```

If that check is refused, Ollama is not running on Windows yet. CTFHive continues to work in mock and tool-only modes without it.

This setup uses WSL2 rather than modifying disk partitions. A true Windows/Kali dual-boot installation must be performed manually with backups and the official Kali installer; CTFHive does not automate partitioning or bootloader changes.

## Optional Kali tooling

The external agent catalog is visible in `ctfhive doctor` and the terminal UI. Integrations for PentestGPT, CAI, Strix, Shannon, PentAGI, HexStrike AI, Claude Code, OpenHands, Cline, and Roo Code are disabled by default and are never cloned or executed automatically. Review their source and scope before enabling any separately.

For optional Python-based analysis tools in Kali/WSL, review and install:

```bash
python3 -m pip install -r requirements-kali.txt
```

System tools and GitHub projects remain operator-managed. CTFHive records their availability but does not execute downloaded repository code.

### Kali on WSL2

Check the current state with `wsl.exe --status` and `wsl.exe --list --verbose`. On a Windows host with no distribution installed, run this from an Administrator PowerShell, then restart if Windows requests it:

```powershell
wsl.exe --install --distribution kali-linux
```

After Kali starts, install the optional Python tools inside Kali, not the Windows virtual environment. CTFHive can then be run from the Kali checkout with `python3 -m ctfhive.tui --solve ./challenge --real`.

Configuration uses `MODEL`, `OLLAMA_BASE_URL`, `CTFHIVE_WORKSPACE`, `CTFHIVE_EVIDENCE`, `CTFD_URL`, `CTFD_TOKEN`, and `CTFHIVE_ALLOW_SUBMISSION`. Automatic submission is disabled by default.

## Qwen learning and fine-tuning

CTFHive learns continuously through local SQLite knowledge, retrieval, and feedback. It can also create a redacted supervised-training dataset for Qwen:

```bash
python3 -m ctfhive.cli knowledge training-data /tmp/ctfhive/qwen.jsonl
```

The generated JSONL contains generalized strategies only. Flags, credentials, tokens, private keys, and challenge secrets are removed before export. To inspect whether a local training backend is present:

```bash
python3 -m ctfhive.cli knowledge train
```

This command never changes model weights automatically. Actual Qwen fine-tuning requires an explicitly selected local training stack, a reviewed dataset, and suitable GPU/storage resources. After fine-tuning, point `MODEL`/`OLLAMA_BASE_URL` at the reviewed model served by Ollama. Normal solving remains available through RAG even when no training backend is installed.
