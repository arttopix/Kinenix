"""Check the built distributions before a release.

Usage: python .github/scripts/check_release.py DIST_DIR [TAG]

- Every Kinenix package (kinenix, kinenix-hub, kinenix-worker) has a wheel and an sdist in DIST_DIR.
- All of them carry the same version, since the packages are released together.
- When TAG is given (for example v0.2.0b1), it must be "v" + that version.
"""
import re
import sys
from pathlib import Path

PACKAGES = ("kinenix", "kinenix_hub", "kinenix_worker")
DIST_NAME = re.compile(r"^(?P<name>kinenix(?:_hub|_worker)?)-(?P<version>[^-]+?)(?:-py3-none-any\.whl|\.tar\.gz)$")


def main() -> int:
    dist = Path(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else ""
    found = {}
    for path in sorted(dist.iterdir()):
        match = DIST_NAME.match(path.name)
        if not match:
            print(f"unexpected file in {dist}: {path.name}")
            return 1
        found.setdefault(match["name"], set()).add((match["version"], path.suffix))

    problems = []
    for package in PACKAGES:
        kinds = {suffix for _, suffix in found.get(package, set())}
        if kinds != {".whl", ".gz"}:
            problems.append(f"{package}: expected a wheel and an sdist, found {sorted(kinds) or 'nothing'}")
    versions = {version for entries in found.values() for version, _ in entries}
    if len(versions) != 1:
        problems.append(f"packages must share one version, found {sorted(versions)}")
    elif tag.startswith("v") and tag != "v" + next(iter(versions)):
        problems.append(f"tag {tag} does not match the package version {next(iter(versions))}")

    for problem in problems:
        print("ERROR:", problem)
    if not problems:
        print(f"OK: {', '.join(PACKAGES)} at version {next(iter(versions))}" + (f", tag {tag}" if tag else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
