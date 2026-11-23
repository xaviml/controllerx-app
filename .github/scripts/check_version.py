#!/usr/bin/env python3
"""Checks the app version in controllerx/config.yaml.

    check_version.py            Check the version in a pull request or on main
    check_version.py --release  Check a version about to be released

The version must:

- Look like X.Y.Z-N, with N from 1 to 9.
- Have X.Y.Z equal to the ControllerX version the app installs: the
  controllerx.zip of the vX.Y.Z release matches CONTROLLERX_SHA256 in the
  Dockerfile and its cx_version.py says vX.Y.Z.
- Be greater, for AwesomeVersion, than every released app version (the
  v* tags). Without --release, a version that is already released passes,
  since it's not going to be released again.

Home Assistant decides whether there's an update with AwesomeVersion, so a
version that isn't greater than the installed one can't be installed. See
"Versioning" in README.md.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from awesomeversion import AwesomeVersion

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "controllerx" / "config.yaml"
DOCKERFILE = ROOT / "controllerx" / "Dockerfile"
ZIP_URL = "https://github.com/xaviml/controllerx/releases/download/v{version}/controllerx.zip"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+-\d+$")
# AwesomeVersion only compares the "-N" suffix as a number when it's a single
# digit: it says that 5.3.0-10 isn't greater than 5.3.0-9.
MAX_REVISION = 9


def is_newer(new: str, old: str) -> bool:
    """Whether Home Assistant offers `new` as an update to `old`."""
    return bool(AwesomeVersion(new) > AwesomeVersion(old))


def format_errors(version: str) -> list[str]:
    if not VERSION_RE.match(version):
        return [
            f"Version '{version}' doesn't match X.Y.Z-N. A plain X.Y.Z is never "
            "released, Home Assistant would treat a later X.Y.Z-N as a downgrade."
        ]
    revision = int(version.rsplit("-", 1)[1])
    if not 1 <= revision <= MAX_REVISION:
        return [
            f"Version '{version}' has N={revision}, it must be from 1 to "
            f"{MAX_REVISION}: Home Assistant doesn't see X.Y.Z-10 as newer than "
            "X.Y.Z-9. Release a new ControllerX patch version instead."
        ]
    return []


def controllerx_errors(base: str, pinned_sha256: str, zip_bytes: bytes) -> list[str]:
    """Checks that `zip_bytes`, the controllerx.zip of release v`base`, is the
    one pinned in the Dockerfile and contains ControllerX v`base`."""
    errors = []
    sha256 = hashlib.sha256(zip_bytes).hexdigest()
    if sha256 != pinned_sha256:
        errors.append(
            f"CONTROLLERX_SHA256 in the Dockerfile is {pinned_sha256}, but the "
            f"controllerx.zip of ControllerX v{base} has {sha256}."
        )
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            cx_version = archive.read("cx_version.py").decode()
    except (zipfile.BadZipFile, KeyError) as error:
        return [*errors, f"Could not read cx_version.py from controllerx.zip: {error}"]
    match = re.search(r"""__version__\s*=\s*["']([^"']+)["']""", cx_version)
    found = match.group(1) if match else None
    if found != f"v{base}":
        errors.append(
            f"The app version says ControllerX {base}, but the bundled "
            f"controllerx.zip is ControllerX {found}."
        )
    return errors


def order_errors(version: str, tags: list[str], release: bool) -> list[str]:
    """Checks that `version` is greater than every released version (`tags`
    without the "v")."""
    if version in tags:
        return [f"Version {version} is already released (tag v{version})."] if release else []
    not_older = [tag for tag in tags if not is_newer(version, tag)]
    if not_older:
        return [
            f"Version {version} isn't greater than the released "
            f"{', '.join(not_older)} for AwesomeVersion, Home Assistant "
            "wouldn't offer it as an update."
        ]
    return []


def read_version() -> str:
    match = re.search(r"^version:\s*['\"]?([^'\"\s]+)", CONFIG.read_text(), re.MULTILINE)
    if not match:
        sys.exit(f"::error::No version in {CONFIG}")
    return match.group(1)


def read_pinned_sha256() -> str:
    match = re.search(
        r'^ARG CONTROLLERX_SHA256="([0-9a-f]{64})"', DOCKERFILE.read_text(), re.MULTILINE
    )
    if not match:
        sys.exit(f"::error::No CONTROLLERX_SHA256 in {DOCKERFILE}")
    return match.group(1)


def released_versions() -> list[str]:
    tags = subprocess.run(
        ["git", "tag", "--list", "v*"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    return [tag[1:] for tag in tags]


def download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--release",
        action="store_true",
        help="the version is about to be released, so it can't be released already",
    )
    args = parser.parse_args()

    version = read_version()
    errors = format_errors(version)
    if not errors:
        base = version.split("-", 1)[0]
        url = ZIP_URL.format(version=base)
        try:
            zip_bytes = download(url)
        except OSError as error:
            errors.append(f"Could not download {url} (is ControllerX v{base} released?): {error}")
        else:
            errors += controllerx_errors(base, read_pinned_sha256(), zip_bytes)

    tags = released_versions()
    if not tags:
        errors.append("No v* tags found, fetch them (actions/checkout with fetch-depth: 0).")
    else:
        errors += order_errors(version, tags, args.release)

    for error in errors:
        print(f"::error file=controllerx/config.yaml::{error}")
    if errors:
        return 1
    if version in tags:
        print(f"Version {version} is already released, so it isn't compared.")
    print(f"Version {version} is fine.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
