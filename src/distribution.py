"""Package the verified four-style family for GitHub Releases.

SPDX-License-Identifier: OFL-1.1
"""

import argparse
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .config import DEFAULT_OUTPUT, FONT_REVISION, ROOT, STYLES, VERSION
from .validation import validate_family


def package_family(output: Path, fonts: Path = DEFAULT_OUTPUT) -> list[Path]:
    """Validate before writing, use fixed ZIP metadata, then publish complete assets."""
    validate_family(fonts)
    if (fonts / "OFL.txt").read_bytes() != (ROOT / "OFL.txt").read_bytes():
        raise ValueError("The distribution license differs from the project license")
    names = [f"{style.filename}.{extension}" for style in STYLES for extension in ("ttf", "woff2")]
    members = {name: (fonts / name).read_bytes() for name in names + ["OFL.txt", "metadata.json", "validation.json"]}
    members["README.txt"] = (
        f"Carta Rinascente {VERSION}\nOpenType revision: {FONT_REVISION}\n\n"
        "Install the four TTF files for desktop use. Use WOFF2 files for websites.\n"
        "Regular and Italic have weight 400; Bold and Bold Italic have weight 700.\n"
        "Keep OFL.txt with redistributed font files.\n\n"
        "Source, specimens and documentation:\n"
        "https://github.com/illegalstudio/carta-rinascente\n"
        "Created for Ariadne by illegal studio:\n"
        "https://illegal.studio/en/products/ariadne\n"
    ).encode("utf-8")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive_name = f"CartaRinascente-{VERSION}.zip"
    with TemporaryDirectory(prefix=".build-package-", dir=output.parent) as temporary:
        staging = Path(temporary)
        with ZipFile(staging / archive_name, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in sorted(members.items()):
                info = ZipInfo(f"CartaRinascente-{VERSION}/{name}", date_time=(2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, content, compresslevel=9)
        for name in names:
            (staging / name).write_bytes(members[name])
        checksums = "".join(
            f"{hashlib.sha256((staging / name).read_bytes()).hexdigest()}  {name}\n"
            for name in sorted([archive_name, *names])
        )
        (staging / "SHA256SUMS").write_text(checksums, encoding="utf-8")
        artifacts = [archive_name, *names, "SHA256SUMS"]
        for name in artifacts:
            (staging / name).replace(output / name)
    return [output / name for name in artifacts]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "release" / VERSION)
    args = parser.parse_args()
    try:
        for path in package_family(args.output):
            print(path)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
