"""Audio processing utilities for Sample Pack Maker."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from mutagen.id3 import ID3, TALB, TIT2
from mutagen.wave import WAVE


def filter_wav_files(files: Iterable[str]) -> List[Path]:
    """Return a stable, unique list of WAV file paths from the provided iterable."""
    seen = set()
    wav_paths: List[Path] = []

    for file_str in files:
        path = Path(file_str).expanduser().resolve()
        if path.suffix.lower() != ".wav" or not path.is_file():
            continue
        if path in seen:
            continue
        seen.add(path)
        wav_paths.append(path)

    return wav_paths


def ensure_output_folder(base_folder: Path, pack_name: str) -> Path:
    """Create and return the output folder path for the given pack."""
    output_folder = base_folder / f"{pack_name}_output"
    output_folder.mkdir(parents=True, exist_ok=True)
    return output_folder


def strip_and_set_metadata(file_path: Path, title: str, album: str) -> None:
    """Remove all existing metadata from a WAV file and set clean metadata values."""
    audio = WAVE(file_path)

    if audio.tags:
        audio.delete()

    tags = ID3()
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TALB(encoding=3, text=album))
    tags.save(file_path, v2_version=3)


def process_wav_files(
    wav_files: List[Path], pack_name: str, output_root: Optional[Path] = None
) -> Tuple[Path, int]:
    """Copy, rename, and clean metadata for the provided WAV files.

    Args:
        wav_files: List of WAV file paths to process.
        pack_name: Base name used for renaming and album metadata.
        output_root: Optional folder where the pack output folder is created.

    Returns:
        A tuple of the output folder path and the number of files processed.

    Raises:
        ValueError: If no WAV files are provided.
    """

    if not wav_files:
        raise ValueError("No WAV files to process.")

    base_folder = output_root or wav_files[0].parent
    output_folder = ensure_output_folder(base_folder, pack_name)

    for index, source_path in enumerate(wav_files, start=1):
        new_filename = f"{pack_name}_{index:03d}{source_path.suffix.lower()}"
        destination_path = output_folder / new_filename

        shutil.copy2(source_path, destination_path)
        strip_and_set_metadata(destination_path, title=new_filename, album=pack_name)

    return output_folder, len(wav_files)
