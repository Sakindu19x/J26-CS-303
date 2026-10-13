"""Read-only access to CAM-LDS archives. Originals are never modified."""
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_ARCHIVES = [
    "scenario_1_sudo_pam.zip",
    "scenario_2_cron.zip",
    "scenario_3_vnc_apt.zip",
    "scenario_4.zip",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass
class ArchiveStatus:
    name: str
    path: str
    present: bool
    readable: bool = False
    error: str | None = None
    entries: list[dict] = field(default_factory=list)


def check_archive(path: Path) -> ArchiveStatus:
    """Open an archive read-only and list every entry (no structure assumed)."""
    st = ArchiveStatus(name=path.name, path=str(path), present=path.is_file())
    if not st.present:
        return st
    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad = zf.testzip()
            if bad:
                st.error = f"CRC failure in member: {bad}"
            st.entries = [
                {
                    "name": i.filename,
                    "is_dir": i.is_dir(),
                    "size": i.file_size,
                    "compressed_size": i.compress_size,
                    "modified": "%04d-%02d-%02dT%02d:%02d:%02d" % i.date_time,
                }
                for i in zf.infolist()
            ]
            st.readable = True
    except (zipfile.BadZipFile, OSError) as exc:
        st.error = f"{type(exc).__name__}: {exc}"
    return st


def discover(raw_dir: Path | str = RAW_DIR) -> list[ArchiveStatus]:
    """Status of the expected archives plus any other .zip found in raw_dir."""
    raw_dir = Path(raw_dir)
    names = list(EXPECTED_ARCHIVES)
    if raw_dir.is_dir():
        names += sorted(p.name for p in raw_dir.glob("*.zip") if p.name not in names)
    return [check_archive(raw_dir / n) for n in names]


def read_member(archive: Path, member: str, max_bytes: int | None = None) -> bytes:
    """Read one archive member in place."""
    with zipfile.ZipFile(archive, "r") as zf, zf.open(member) as fh:
        return fh.read() if max_bytes is None else fh.read(max_bytes)


def extract_to_interim(archive: Path, interim_dir: Path = INTERIM_DIR) -> Path:
    """Extract to data/interim/<archive stem>; refuses to write inside raw/."""
    dest = interim_dir / archive.stem
    if RAW_DIR in dest.resolve().parents:
        raise ValueError("Refusing to extract into data/raw")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest)
    return dest
