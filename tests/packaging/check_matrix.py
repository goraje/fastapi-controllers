"""Run isolated wheel installations sequentially, reporting every combination."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


class MatrixArguments(argparse.Namespace):
    wheel_dir: Path = Path()
    python_versions: list[str]

    def __init__(self) -> None:
        super().__init__()
        self.python_versions = ["3.11", "3.12", "3.13", "3.14"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--python-versions", nargs="+")
    args = parser.parse_args(namespace=MatrixArguments())
    checker = Path(__file__).with_name("check_wheel.py").resolve()
    results: list[tuple[str, str, bool]] = []
    for version in args.python_versions:
        for mode in ("base", "minimum"):
            print(f"::group::Python {version}: {mode}", flush=True)
            try:
                result = subprocess.run(
                    [
                        "uv",
                        "run",
                        "--no-project",
                        "--python",
                        version,
                        "python",
                        str(checker),
                        "--wheel-dir",
                        str(args.wheel_dir.resolve()),
                        "--dependencies",
                        mode,
                    ],
                    timeout=300,
                )
                passed = result.returncode == 0
            except subprocess.TimeoutExpired:
                print("Installation check exceeded its 300-second deadline", flush=True)
                passed = False
            results.append((version, mode, passed))
            print("::endgroup::", flush=True)
    print("\nPython | Dependencies | Result\n--- | --- | ---")
    for version, mode, passed in results:
        print(f"{version} | {mode} | {'PASS' if passed else 'FAIL'}")
    return int(any(not passed for _, _, passed in results))


if __name__ == "__main__":
    raise SystemExit(main())
