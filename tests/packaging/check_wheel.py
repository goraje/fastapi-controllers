"""Install exactly one built wheel in an isolated environment, then test it."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from email.parser import Parser
from pathlib import Path


class WheelArguments(argparse.Namespace):
    wheel_dir: Path = Path()
    dependencies: str = "base"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--dependencies", choices=("base", "minimum"), required=True)
    args = parser.parse_args(namespace=WheelArguments())
    wheels = list(Path(args.wheel_dir).resolve().glob("fastapi_controllers-*.whl"))
    if len(wheels) != 1:
        parser.error(
            f"expected exactly one fastapi_controllers wheel, found {len(wheels)}"
        )
    smoke = Path(__file__).with_name("test_installed.py").resolve()
    with tempfile.TemporaryDirectory(prefix="fastapi-controllers-wheel-") as directory:
        root = Path(directory)
        environment = root / "environment"
        python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(environment)], check=True
        )
        requirements = [str(wheels[0])]
        resolution = "highest"
        if args.dependencies == "minimum":
            # Pin each declared dependency to its floor. Unlike zipctl, not the whole
            # graph: FastAPI's own floors (pydantic, annotated-types) are broken
            # under --resolution lowest and old pydantic-core has no 3.14 wheels.
            requirements += _requires_dist(wheels[0])
            resolution = "lowest-direct"
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--resolution",
                resolution,
                *requirements,
            ],
            check=True,
        )
        subprocess.run(["uv", "pip", "check", "--python", str(python)], check=True)
        subprocess.run(
            [str(python), "-I", str(smoke)], cwd=root, check=True, timeout=120
        )


def _requires_dist(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(archive.read(name).decode())
    return metadata.get_all("Requires-Dist") or []


if __name__ == "__main__":
    main()
