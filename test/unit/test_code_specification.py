import subprocess

import pytest


def run_command(command: str):
    """Run a command and assert it exits with 0."""
    try:
        subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        pytest.fail(
            f"Command '{command}' failed with exit code {e.returncode}.\n"
            f"Stdout:\n{e.stdout}\n"
            f"Stderr:\n{e.stderr}",
            pytrace=False,
        )


def test_mypy_checks():
    """Run mypy checks on the codebase."""
    run_command("mypy app")
    run_command("mypy test/example")


def test_ruff_checks():
    """Run ruff checks on the codebase."""
    run_command("ruff check app")
    run_command("ruff check test/example")
