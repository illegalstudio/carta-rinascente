"""Release regression tests use disposable local repositories, never GitHub.

SPDX-License-Identifier: OFL-1.1
"""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from src import release
from src.config import ROOT, STYLES, VERSION
from src.distribution import package_family
from src.versioning import Version, next_revision, propose_version, read_versions, update_versions


def run_git(root, *args):
    return release.git(root, *args)


class VersionTests(unittest.TestCase):
    def test_semver_uses_numeric_order_and_rejects_ambiguous_versions(self):
        self.assertGreater(Version.parse("v0.10.0"), Version.parse("0.9.9"))
        for value in ("01.2.3", "1.2", "1.2.3-rc.1", "1.2.3;exit", "1.2.3\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Version.parse(value)
        self.assertEqual(str(propose_version(Version(0, 2, 0), {"v0.9.9", "v0.10.0", "demo"})), "0.10.1")
        self.assertEqual(propose_version(Version(1, 0, 0), {"v0.10.0"}), Version(1, 0, 0))

    def test_font_revision_is_independent_and_rolls_over(self):
        self.assertEqual(next_revision("0.200"), "0.201")
        self.assertEqual(next_revision("0.999"), "1.000")
        with self.assertRaises(ValueError):
            next_revision("32767.999")


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix=".build-release-test-", dir=Path.cwd())
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "work"
        self.remote = self.directory / "origin.git"
        self.root.mkdir()
        self.remote.mkdir()
        run_git(self.remote, "init", "--bare", "-b", "main")
        run_git(self.root, "init", "-b", "main")
        for key, value in (("user.name", "Release Test"), ("user.email", "release@example.invalid"),
                           ("commit.gpgsign", "false"), ("tag.gpgsign", "false"),
                           ("core.hooksPath", str(self.directory / "no-hooks"))):
            run_git(self.root, "config", key, value)
        for name in ("src", "dist", "assets"):
            (self.root / name).mkdir()
        (self.root / "src/__init__.py").write_text('__version__ = "0.2.0"\n__font_revision__ = "0.200"\n')
        (self.root / "README.md").write_text('badge/version-0.2.0-color alt="Version: 0.2.0"\n**Four linked styles**, version 0.2.0:')
        (self.root / "index.html").write_text('Four voices, one family / 0.2.0</span>\nOriginal font family, version 0.2.0.')
        (self.root / "dist/font.ttf").write_bytes(b"old-font")
        (self.root / "assets/readme-specimen.png").write_bytes(b"old-proof")
        (self.root / ".gitignore").write_text(".build-*/\n")
        run_git(self.root, "add", ".")
        run_git(self.root, "commit", "-m", "Initial test family")
        run_git(self.root, "remote", "add", "origin", str(self.remote))
        run_git(self.root, "push", "-u", "origin", "main")
        self.head = run_git(self.root, "rev-parse", "HEAD")

    def prepare_fixture(self, root, staging, target):
        for name in ("src", "dist", "assets"):
            shutil.copytree(root / name, staging / name)
        for name in ("README.md", "index.html"):
            shutil.copy2(root / name, staging / name)
        update_versions(staging, target)
        (staging / "dist/font.ttf").write_bytes(b"new-font")

    def invoke(self, *args, answers=(), builder=None):
        output = StringIO()
        with patch.object(release, "ROOT", self.root), patch("builtins.input", side_effect=answers), \
             patch.object(release, "prepare", side_effect=builder or self.prepare_fixture), \
             redirect_stdout(output), redirect_stderr(output):
            release.main(list(args))
        return output.getvalue()

    def test_dry_run_does_not_change_files_or_refs(self):
        self.assertIn("Proposed tag: v0.2.0", self.invoke("--dry-run"))
        self.assertEqual(run_git(self.root, "rev-parse", "HEAD"), self.head)
        self.assertEqual(run_git(self.root, "status", "--porcelain"), "")
        self.assertEqual(run_git(self.root, "tag", "--list"), "")

    def test_confirmed_release_pushes_matching_commit_and_annotated_tag(self):
        self.invoke(answers=("0.2.1", "yes"))
        head = run_git(self.root, "rev-parse", "HEAD")
        self.assertNotEqual(head, self.head)
        self.assertEqual(run_git(self.remote, "rev-parse", "refs/heads/main"), head)
        self.assertEqual(run_git(self.remote, "rev-parse", "v0.2.1^{}"), head)
        self.assertEqual(run_git(self.root, "cat-file", "-t", "v0.2.1"), "tag")
        self.assertEqual(read_versions(self.root), (Version(0, 2, 1), "0.201"))
        self.assertEqual(run_git(self.root, "status", "--porcelain"), "")

    def test_failed_build_leaves_original_checkout_and_remote_untouched(self):
        with self.assertRaises(SystemExit):
            self.invoke(answers=("0.2.1", "yes"), builder=ValueError("Intentional build failure"))
        self.assertEqual(run_git(self.root, "status", "--porcelain"), "")
        self.assertEqual(read_versions(self.root), (Version(0, 2, 0), "0.200"))
        self.assertEqual(run_git(self.remote, "rev-parse", "main"), self.head)
        self.assertEqual(run_git(self.remote, "tag", "--list"), "")
        self.assertEqual(list(self.root.glob(".build-release-*")), [])

    def test_declining_confirmation_makes_no_release(self):
        self.invoke(answers=("", "no"))
        self.assertEqual(run_git(self.root, "status", "--porcelain"), "")
        self.assertEqual(run_git(self.root, "tag", "--list"), "")

    def test_dirty_checkout_wrong_branch_and_unpushed_commits_are_rejected(self):
        extra = self.root / "untracked.txt"
        extra.write_text("uncommitted")
        with self.assertRaisesRegex(ValueError, "not clean"):
            release.preflight(self.root)
        extra.unlink()
        run_git(self.root, "checkout", "-b", "topic")
        with self.assertRaisesRegex(ValueError, "from main"):
            release.preflight(self.root)
        run_git(self.root, "checkout", "main")
        run_git(self.root, "commit", "--allow-empty", "-m", "Unpushed")
        with self.assertRaisesRegex(ValueError, "differ"):
            release.preflight(self.root)

    def test_remote_tags_and_network_failure_are_not_treated_as_no_releases(self):
        run_git(self.remote, "tag", "v0.2.0", "main")
        repository = release.preflight(self.root)
        self.assertIn("v0.2.0", repository.tags)
        with self.assertRaises(ValueError):
            release.check_target(self.root, repository, Version(0, 2, 0))
        run_git(self.root, "remote", "set-url", "origin", str(self.directory / "missing.git"))
        with self.assertRaises(subprocess.CalledProcessError):
            release.preflight(self.root)

    def test_failed_atomic_push_preserves_local_release_for_recovery(self):
        hooks = self.remote / "hooks"
        hook = hooks / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        with self.assertRaises(SystemExit):
            self.invoke(answers=("0.2.1", "yes"))
        self.assertEqual(run_git(self.remote, "rev-parse", "main"), self.head)
        self.assertEqual(run_git(self.remote, "tag", "--list"), "")
        self.assertEqual(run_git(self.root, "tag", "--list"), "v0.2.1")
        self.assertEqual(run_git(self.root, "status", "--porcelain"), "")

    def test_remote_change_during_build_stops_publication(self):
        repository = release.preflight(self.root)
        staging = self.directory / "prepared"
        staging.mkdir()
        self.prepare_fixture(self.root, staging, Version(0, 2, 1))
        run_git(self.remote, "tag", "v0.2.1", "main")
        with self.assertRaisesRegex(ValueError, "changed during the build"):
            release.publish(self.root, repository, staging, Version(0, 2, 1))
        self.assertEqual(run_git(self.root, "status", "--porcelain"), "")
        self.assertEqual(run_git(self.root, "rev-parse", "HEAD"), self.head)

    def test_version_label_failure_does_not_partially_update_sources(self):
        (self.root / "index.html").write_text("missing labels")
        before = (self.root / "src/__init__.py").read_bytes()
        with self.assertRaisesRegex(ValueError, "version label"):
            update_versions(self.root, Version(0, 3, 0))
        self.assertEqual((self.root / "src/__init__.py").read_bytes(), before)


class PackageTests(unittest.TestCase):
    def test_archives_are_reproducible_and_include_the_full_licensed_family(self):
        with TemporaryDirectory(prefix=".build-package-test-", dir=Path.cwd()) as temporary:
            output = Path(temporary)
            first = package_family(output / "first")
            second = package_family(output / "second")
            self.assertEqual([path.read_bytes() for path in first], [path.read_bytes() for path in second])
            archive = output / "first" / f"CartaRinascente-{VERSION}.zip"
            with ZipFile(archive) as fonts:
                prefix = f"CartaRinascente-{VERSION}/"
                for style in STYLES:
                    for extension in ("ttf", "woff2"):
                        name = f"{style.filename}.{extension}"
                        self.assertEqual(fonts.read(prefix + name), (ROOT / "dist" / name).read_bytes())
                self.assertEqual(fonts.read(prefix + "OFL.txt"), (ROOT / "OFL.txt").read_bytes())
            for line in (output / "first" / "SHA256SUMS").read_text().splitlines():
                digest, name = line.split("  ")
                self.assertEqual(hashlib.sha256((output / "first" / name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
