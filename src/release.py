"""Interactively prepare a verified release and push its annotated GitHub tag.

SPDX-License-Identifier: OFL-1.1
"""

import argparse
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

from .versioning import Version, propose_version, read_versions, update_versions

ROOT = Path(__file__).resolve().parent.parent
RELEASE_PATHS = ("src/__init__.py", "README.md", "index.html", "dist", "assets/readme-specimen.png")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


@dataclass(frozen=True)
class Repository:
    head: str
    tags: set[str]


def preflight(root: Path) -> Repository:
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ValueError("Run the release command from the project repository")
    if git(root, "status", "--porcelain"):
        raise ValueError("Working tree is not clean; commit and push your changes first")
    if git(root, "branch", "--show-current") != "main":
        raise ValueError("Releases must be made from main")
    if git(root, "remote", "get-url", "origin") != git(root, "remote", "get-url", "--push", "origin"):
        raise ValueError("The origin fetch and push URLs must match")
    refs = {}
    for line in git(root, "ls-remote", "origin", "refs/heads/main", "refs/tags/v*").splitlines():
        sha, name = line.split()
        refs[name] = sha
    head = git(root, "rev-parse", "HEAD")
    if refs.get("refs/heads/main") != head:
        raise ValueError("Local main and origin/main differ; synchronize and push before releasing")
    tags = set(git(root, "tag", "--list").splitlines())
    tags.update(name.removeprefix("refs/tags/") for name in refs if name.startswith("refs/tags/"))
    return Repository(head, tags)


def check_target(root: Path, repository: Repository, target: Version) -> None:
    current, _ = read_versions(root)
    if target < propose_version(current, repository.tags):
        raise ValueError("Choose a version newer than existing releases and at least the source version")
    if target.tag in repository.tags:
        raise ValueError(f"Tag {target.tag} already exists")


def prepare(root: Path, staging: Path, target: Version) -> None:
    """Build from tracked sources without touching the user's checkout on failure."""
    snapshot = subprocess.run(
        ["git", "-C", str(root), "archive", "--format=tar", "HEAD"], check=True, capture_output=True,
    ).stdout
    with tarfile.open(fileobj=BytesIO(snapshot)) as archive:
        archive.extractall(staging, filter="data")
    python = sys.executable
    subprocess.run([python, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=staging, check=True)
    update_versions(staging, target)
    for arguments in (
        ["-m", "src", "all", "--check-reproducible"],
        ["-m", "src.distribution"],
    ):
        subprocess.run([python, *arguments], cwd=staging, check=True)


def publish(root: Path, repository: Repository, staging: Path, target: Version) -> None:
    fresh = preflight(root)
    if fresh != repository:
        raise ValueError("Repository changed during the build; review it before retrying")
    check_target(root, fresh, target)
    names = git(root, "ls-files", "--", *RELEASE_PATHS).splitlines()
    for name in names:
        content = (staging / name).read_bytes()
        if (root / name).read_bytes() != content:
            (root / name).write_bytes(content)
    git(root, "add", "--", *RELEASE_PATHS)
    if git(root, "diff", "--cached", "--name-only"):
        git(root, "commit", "-m", f"Release {target.tag}")
    git(root, "tag", "-a", target.tag, "-m", f"Release {target.tag}")
    try:
        git(root, "push", "--atomic", "origin", "HEAD:refs/heads/main", f"refs/tags/{target.tag}")
    except subprocess.CalledProcessError:
        print(
            f"The local release commit and tag {target.tag} are retained. After resolving the push error, retry:\n"
            f"  git push --atomic origin HEAD:refs/heads/main refs/tags/{target.tag}", file=sys.stderr,
        )
        raise
    print(f"Pushed {target.tag}. The Release workflow will publish the verified assets on GitHub.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", type=Version.parse, help="Stable SemVer, with an optional v prefix")
    parser.add_argument("--dry-run", action="store_true", help="Read-only preflight and version proposal")
    args = parser.parse_args(argv)
    try:
        repository = preflight(ROOT)
        current, revision = read_versions(ROOT)
        proposed = propose_version(current, repository.tags)
        print(f"Source: {current} (OpenType {revision})\nProposed tag: {proposed.tag}")
        target = args.version
        if target is None:
            target = proposed if args.dry_run else Version.parse(input(f"Version to release [{proposed}]: ").strip() or str(proposed))
        check_target(ROOT, repository, target)
        print(f"Release {target.tag}: verify all styles, update release files, commit, tag and push main to origin.")
        if args.dry_run:
            print("Dry run complete. No files, commits, tags or remote state changed.")
            return
        if input("Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return
        with TemporaryDirectory(prefix=".build-release-", dir=ROOT) as temporary:
            staging = Path(temporary)
            prepare(ROOT, staging, target)
            publish(ROOT, repository, staging, target)
    except (OSError, ValueError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
        parser.exit(1, f"error: {detail or 'Release interrupted'}\n")


if __name__ == "__main__":
    main()
