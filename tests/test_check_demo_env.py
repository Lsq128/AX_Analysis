from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_demo_env.sh"


def _run(env_file: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(ROOT),
        env={**os.environ, "AX_ENV_FILE": str(env_file)},
        capture_output=True,
        text=True,
    )


def test_missing_env_fails(tmp_path: Path) -> None:
    missing = tmp_path / "nope.env"
    result = _run(missing)
    assert result.returncode == 1
    assert "cp .env.example .env" in result.stderr


def test_empty_keys_fails(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DEEPSEEK_API_KEY=\nJWT_SECRET=x\n", encoding="utf-8")
    result = _run(env)
    assert result.returncode == 1
    assert "LLM" in result.stderr or "API_KEY" in result.stderr


def test_deepseek_key_ok(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DEEPSEEK_API_KEY=sk-test\n", encoding="utf-8")
    result = _run(env)
    assert result.returncode == 0, result.stderr


def test_quoted_key_ok(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text('MOONSHOT_API_KEY="sk-moon"\n', encoding="utf-8")
    result = _run(env)
    assert result.returncode == 0, result.stderr
