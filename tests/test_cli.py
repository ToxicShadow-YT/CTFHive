from __future__ import annotations

from pathlib import Path

from ctfhive.cli import main


def test_mock_cli(tmp_path: Path, monkeypatch, capsys):
    challenge = tmp_path / "fixture.txt"
    challenge.write_text("fixture", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["solve-challenge", str(challenge), "--mock", "--no-submit"]) == 0
    assert '"solved": false' in capsys.readouterr().out


def test_terminal_ui_one_shot(tmp_path: Path, monkeypatch, capsys):
    challenge = tmp_path / "fixture.txt"
    challenge.write_text("fixture", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from ctfhive.tui import main

    assert main(["--solve", str(challenge)]) == 0
    assert "NOT SOLVED" in capsys.readouterr().out


def test_external_agents_command(capsys):
    assert main(["agents"]) == 0
    output = capsys.readouterr().out
    assert "PentestGPT" in output
    assert "Claude Code" in output
    assert "OpenHands" in output
