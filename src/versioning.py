"""Semantic release versions and the independent OpenType revision counter.

SPDX-License-Identifier: OFL-1.1
"""

from dataclasses import dataclass
from pathlib import Path
import re

SEMVER = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = re.fullmatch(SEMVER, value.removeprefix("v"))
        if match is None:
            raise ValueError(f"Expected a stable MAJOR.MINOR.PATCH version, got {value!r}")
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def tag(self) -> str:
        return f"v{self}"

    def next_patch(self) -> "Version":
        return Version(self.major, self.minor, self.patch + 1)


def read_versions(root: Path) -> tuple[Version, str]:
    source = (root / "src" / "__init__.py").read_text(encoding="utf-8")
    values = {}
    for name in ("__version__", "__font_revision__"):
        matches = re.findall(rf'^{name} = "([^"\n]+)"$', source, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {name} in src/__init__.py")
        values[name] = matches[0]
    revision_number(values["__font_revision__"])
    return Version.parse(values["__version__"]), values["__font_revision__"]


def revision_number(value: str) -> int:
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.[0-9]{3}", value):
        raise ValueError(f"Invalid OpenType revision: {value!r}")
    major, minor = value.split(".")
    if int(major) > 32767:
        raise ValueError("OpenType revision exceeds the signed 16.16 field")
    return int(major) * 1000 + int(minor)


def next_revision(value: str) -> str:
    number = revision_number(value) + 1
    revision = f"{number // 1000}.{number % 1000:03d}"
    revision_number(revision)
    return revision


def propose_version(current: Version, tags: set[str]) -> Version:
    versions = []
    for tag in tags:
        if re.fullmatch(f"v{SEMVER}", tag):
            versions.append(Version.parse(tag))
    return max(current, max(versions).next_patch()) if versions else current


def update_versions(root: Path, target: Version) -> str:
    """Prepare all substitutions before writing, so stale labels fail together."""
    current, revision = read_versions(root)
    if target < current:
        raise ValueError("The release version cannot move backwards")
    updated_revision = next_revision(revision) if target != current else revision
    specifications = {
        "src/__init__.py": [
            (rf'(__version__ = "){re.escape(str(current))}("\n)', str(target)),
            (rf'(__font_revision__ = "){re.escape(revision)}("\n)', updated_revision),
        ],
        "README.md": [
            (rf'(badge/version-){re.escape(str(current))}(-)', str(target)),
            (rf'(alt="Version: ){re.escape(str(current))}(")', str(target)),
            (rf'(\*\*Four linked styles\*\*, version ){re.escape(str(current))}(:)', str(target)),
        ],
        "index.html": [
            (rf'(Four voices, one family / ){re.escape(str(current))}(</span>)', str(target)),
            (rf'(Original font family, version ){re.escape(str(current))}(\.)', str(target)),
        ],
    }
    updated = {}
    for name, substitutions in specifications.items():
        content = (root / name).read_text(encoding="utf-8")
        for pattern, replacement in substitutions:
            content, count = re.subn(pattern, lambda m: m[1] + replacement + m[2], content)
            if count != 1:
                raise ValueError(f"Missing or duplicated version label in {name}")
        updated[name] = content
    for name, content in updated.items():
        (root / name).write_text(content, encoding="utf-8")
    return updated_revision
