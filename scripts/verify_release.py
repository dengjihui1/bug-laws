from __future__ import annotations

import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="buglaws-release-") as directory:
        temp = Path(directory)
        wheelhouse = temp / "dist"
        wheelhouse.mkdir()
        # `build` is a release tool; it creates isolated PEP 517 environments.
        # Hatchling remains a build dependency, not a runtime dependency.
        run([sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", str(wheelhouse)], root)
        env = temp / "venv"
        venv.create(env, with_pip=True)
        python = env / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
        wheel = next(wheelhouse.glob("*.whl"))
        source_dist = next(wheelhouse.glob("*.tar.gz"))
        run([str(python), "-m", "pip", "install", "--no-deps", str(wheel)], root)
        run([str(python), "-m", "buglaws", "--version"], root)
        run([str(python), "-c", "import buglaws; print(buglaws.__version__)"], root)
        if source_dist.stat().st_size <= 0:
            raise RuntimeError("empty source distribution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
