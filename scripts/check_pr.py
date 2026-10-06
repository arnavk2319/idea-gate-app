"""PR hygiene checks run by CI.

Usage: python scripts/check_pr.py <base-ref>   (e.g. origin/main)

Checks:
  1. pyproject.toml version is higher than on the base branch.
  2. No commit in base..HEAD carries an attribution trailer.
"""

import re
import subprocess
import sys
import tomllib

TRAILER = re.compile(r"co-authored-by|generated with", re.IGNORECASE)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def parse(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split("."))


def main(base: str) -> int:
    errors: list[str] = []

    with open("pyproject.toml", "rb") as f:
        head_version = tomllib.load(f)["project"]["version"]
    base_version = tomllib.loads(git("show", f"{base}:pyproject.toml"))["project"]["version"]
    if parse(head_version) <= parse(base_version):
        errors.append(f"version {head_version} must be higher than {base} ({base_version})")

    for line in git("log", "--format=%h %B", f"{base}..HEAD").splitlines():
        if TRAILER.search(line):
            errors.append(f"attribution trailer in commit message: {line.strip()}")

    for e in errors:
        print(f"FAIL: {e}")
    if not errors:
        print(f"OK: version {head_version} and commit messages look right")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "origin/main"))
