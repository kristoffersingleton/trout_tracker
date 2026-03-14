"""Tests for update.sh"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
SCRIPT = BASE / "update.sh"


class TestUpdateScript:
    def test_script_exists(self):
        assert SCRIPT.exists(), "update.sh not found"

    def test_script_is_executable(self):
        assert SCRIPT.stat().st_mode & 0o111, "update.sh is not executable"

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line.startswith("#!"), "update.sh missing shebang"

    def test_script_uses_set_e(self):
        content = SCRIPT.read_text()
        assert "set -e" in content, "update.sh should use 'set -e' to fail fast"

    def test_script_references_correct_pdf_url(self):
        content = SCRIPT.read_text()
        assert "portal.ct.gov/-/media/DEEP/fishing/weekly_reports/CurrentStockingReport.pdf" in content

    def test_script_references_required_steps(self):
        content = SCRIPT.read_text()
        assert "parse_pdf.py" in content
        assert "generate_html.py" in content
        assert "git push" in content

    def test_script_handles_no_changes(self):
        """Running the script when nothing has changed should exit 0."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, cwd=BASE
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert "already up to date" in result.stdout or "Pushed" in result.stdout

    def test_script_runs_all_steps(self):
        """All major steps should be reported in output."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, cwd=BASE
        )
        assert "Downloading" in result.stdout
        assert "Parsing" in result.stdout
        assert "Generating" in result.stdout
        assert "Committing" in result.stdout
        assert "kristoffersingleton.github.io/trout_tracker" in result.stdout
