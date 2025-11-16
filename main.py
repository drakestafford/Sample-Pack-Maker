import os
import shutil
from typing import List

from mutagen.id3 import ID3, TALB, TIT2
from mutagen.wave import WAVE


def find_wav_files(folder_path: str) -> List[str]:
    """Return a sorted list of WAV file paths in the given folder."""
    return sorted(
        [
            os.path.join(folder_path, file)
            for file in os.listdir(folder_path)
            if file.lower().endswith(".wav") and os.path.isfile(os.path.join(folder_path, file))
        ]
    )


def ensure_output_folder(folder_path: str, pack_name: str) -> str:
    """Create (if needed) and return the output folder path."""
    output_folder = os.path.join(folder_path, f"{pack_name}_output")
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


def strip_and_set_metadata(file_path: str, title: str, album: str) -> None:
    """Remove all existing metadata from a WAV file and set clean metadata values."""
    audio = WAVE(file_path)

    # Remove any existing tags to ensure a clean slate
    if audio.tags:
        audio.delete()

    # Write minimal, clean metadata
    tags = ID3()
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TALB(encoding=3, text=album))
    tags.save(file_path, v2_version=3)


def process_wav_files(source_folder: str, pack_name: str) -> None:
    """Process WAV files: copy, strip metadata, rename, and save to output folder."""
    wav_files = find_wav_files(source_folder)
    if not wav_files:
        print("No WAV files found in the provided folder.")
        return

    output_folder = ensure_output_folder(source_folder, pack_name)
    print(f"Output folder: {output_folder}")

    for index, file_path in enumerate(wav_files, start=1):
        new_filename = f"{pack_name}_{index:03d}.wav"
        destination_path = os.path.join(output_folder, new_filename)

        print(f"Processing: {os.path.basename(file_path)} -> {new_filename}")

        shutil.copy2(file_path, destination_path)
        strip_and_set_metadata(destination_path, title=new_filename, album=pack_name)

    print("Processing complete. Original files remain unchanged.")


def prompt_for_folder() -> str:
    """Prompt the user for a folder path containing WAV files."""
    folder = input("Enter the folder containing your WAV files: \n").strip()
    # Handle paths with escaped spaces from terminal drag/drop
    return folder.replace("\\ ", " ")


def prompt_for_pack_name() -> str:
    """Prompt the user for the pack name to use in output filenames."""
    while True:
        pack_name = input("Enter the pack name to use for renaming: \n").strip()
        if pack_name:
            return pack_name
        print("Pack name cannot be empty. Please try again.")


if __name__ == "__main__":
    folder_path = prompt_for_folder()
    pack = prompt_for_pack_name()
    process_wav_files(folder_path, pack)
