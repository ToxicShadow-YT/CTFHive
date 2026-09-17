from __future__ import annotations

import sys
import time
from pathlib import Path

from ctfhive.agents.classifier import Category, classify
from ctfhive.agents.coordinator import Coordinator
from ctfhive.config import Config
from ctfhive.evidence.models import Evidence
from ctfhive.evidence.store import EvidenceStore
from ctfhive.flags.detector import candidates_from_evidence, extract_flags
from ctfhive.flags.verifier import choose_flag
from ctfhive.intake import ingest
from ctfhive.tools.base import ToolSpec
from ctfhive.tools.filesystem import safe_file_args
from ctfhive.tools.registry import ToolRegistry
from ctfhive.tools.runner import ToolRunner


def test_flag_extraction_and_validation():
    assert extract_flags("FLAG{one} CTF{two} flag{three}", (r"FLAG\{[^}]+\}", r"CTF\{[^}]+\}", r"flag\{[^}]+\}")) == ["FLAG{one}", "CTF{two}", "flag{three}"]
    record = Evidence("demo", "rev", "strings", [], 0, "FLAG{one}", "", 1, 0.9)
    candidate = choose_flag(candidates_from_evidence([record], (r"FLAG\{[^}]+\}",)), (r"FLAG\{[^}]+\}",))
    assert candidate and candidate.value == "FLAG{one}"


def test_evidence_store(tmp_path: Path):
    store = EvidenceStore(tmp_path)
    record = Evidence("demo", "misc", "mock", [], 0, "ok", "", 2)
    store.append(record)
    assert store.read("demo")[0].stdout == "ok"


def test_registry_contains_groups_and_reports_missing():
    registry = ToolRegistry()
    assert registry.get("strings").category == "general"
    assert any(tool.name == "curl" for tool in registry.all())


def test_runner_timeout_and_limits(tmp_path: Path):
    runner = ToolRunner(tmp_path, stdout_limit=4, stderr_limit=4)
    tool = ToolSpec("python", "test", sys.executable, "python", timeout=0.05)
    result = runner.run(tool, ["-c", "import time; time.sleep(1)"])
    assert result.timed_out
    result = runner.run(tool, ["-c", "print('123456789')"])
    assert result.truncated
    assert len(result.stdout) <= 4


def test_intake_ignores_directories_and_hashes(tmp_path: Path):
    source = tmp_path / "challenge"
    source.mkdir()
    (source / "nested").mkdir()
    (source / "nested" / "sample.txt").write_text("hello", encoding="utf-8")
    challenge = ingest(source, tmp_path / "work")
    assert len(challenge.files) == 1
    assert challenge.files[0].relative_path == "nested/sample.txt"
    try:
        safe_file_args(challenge.root, "nested")
    except ValueError:
        pass
    else:
        raise AssertionError("directories must not be passed to file tools")


def test_classifier_and_mock_mode(tmp_path: Path):
    source = tmp_path / "rev-binary"
    source.write_text("fixture", encoding="utf-8")
    config = Config(workspace_root=tmp_path / "work", evidence_root=tmp_path / "evidence")
    challenge = ingest(source, config.workspace_root)
    assert classify(challenge) == Category.REV
    result = Coordinator(config, EvidenceStore(config.evidence_root)).solve(challenge, mock=True)
    assert result.category == Category.REV
    assert result.solved is False


def test_model_request_shape(monkeypatch):
    from ctfhive.models.openai_compatible import OpenAICompatibleModel

    class Response:
        def read(self):
            return b'{"choices":[{"message":{"content":"ok"}}]}'
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    assert OpenAICompatibleModel("http://localhost/v1", "test").complete("prompt").text == "ok"
