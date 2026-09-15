# setup.py
import subprocess
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py


def _git(*args):
    try:
        r = subprocess.run(["git", "-C", str(Path(__file__).parent), *args],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except OSError:
        return None


class BuildPyWithGitInfo(build_py):
    def run(self):
        status = _git("status", "--porcelain")
        info = {
            "head": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(status) if status is not None else None,
            "dirty_files": status.splitlines() if status else [],
        }
        target = Path(__file__).parent / "cmbml" / "_build_info.py"
        target.write_text(
            "# Generated at build time. Do not edit; do not commit.\n"
            f"BUILD_INFO = {info!r}\n"
        )
        super().run()


setup(cmdclass={"build_py": BuildPyWithGitInfo})
