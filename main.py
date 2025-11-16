from __future__ import annotations

import importlib.util
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from audio_engine import filter_wav_files, process_wav_files


def load_tkdnd_module():
    """Load tkinterdnd2 dynamically if installed."""
    spec = importlib.util.find_spec("tkinterdnd2")
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SamplePackMakerApp:
    def __init__(self, root: tk.Misc, tkdnd_module=None) -> None:
        self.root = root
        self.tkdnd_module = tkdnd_module
        self.dnd_enabled = tkdnd_module is not None

        self.root.title("Sample Pack Maker")
        self.root.geometry("720x540")
        self.root.minsize(640, 460)

        self.wav_files: list[Path] = []

        self._build_layout()
        self._configure_drag_and_drop()

    # Layout helpers
    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top_frame = ttk.Frame(self.root, padding="16 12 16 8")
        top_frame.grid(row=0, column=0, sticky="nsew")
        top_frame.columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Pack Name:", font=("SF Pro Display", 11, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.pack_name_var = tk.StringVar()
        self.pack_name_entry = ttk.Entry(top_frame, textvariable=self.pack_name_var)
        self.pack_name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        middle_frame = ttk.Frame(self.root, padding="16 8 16 8")
        middle_frame.grid(row=1, column=0, sticky="nsew")
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(1, weight=1)

        drop_border = ttk.Frame(middle_frame, padding=4, style="DropArea.TFrame")
        drop_border.grid(row=0, column=0, sticky="ew")
        drop_border.columnconfigure(0, weight=1)

        drop_text = "Drag & Drop WAV files here" if self.dnd_enabled else "Drag & Drop requires tkinterdnd2"
        self.drop_area = ttk.Label(
            drop_border,
            text=drop_text,
            anchor="center",
            padding=12,
            relief="solid",
            borderwidth=1,
            style="DropArea.TLabel",
        )
        self.drop_area.grid(row=0, column=0, sticky="ew")

        list_frame = ttk.Frame(middle_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(
            list_frame,
            height=12,
            activestyle="none",
            selectmode=tk.SINGLE,
            font=("SF Mono", 10),
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.root, padding="16 8 16 8")
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.columnconfigure((0, 1, 2), weight=1, uniform="buttons")

        self.add_button = ttk.Button(button_frame, text="Add Files", command=self.add_files_via_dialog)
        self.add_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.clear_button = ttk.Button(button_frame, text="Clear List", command=self.clear_list)
        self.clear_button.grid(row=0, column=1, sticky="ew", padx=4)

        self.process_button = ttk.Button(button_frame, text="Rinse and Export", command=self.process_files)
        self.process_button.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        status_frame = ttk.Frame(self.root, padding="16 0 16 12")
        status_frame.grid(row=3, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")

    def _configure_drag_and_drop(self) -> None:
        if not self.dnd_enabled:
            self.drop_area.state(["disabled"])
            return

        self.drop_area.drop_target_register(self.tkdnd_module.DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.handle_drop)

    # File handling
    def add_files_via_dialog(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="Select WAV files",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if file_paths:
            self._add_files(file_paths)

    def handle_drop(self, event) -> None:
        dropped_items = self.root.tk.splitlist(event.data)
        self._add_files(dropped_items)

    def _add_files(self, files: list[str] | tuple[str, ...]) -> None:
        new_paths = filter_wav_files(files)
        if not new_paths:
            self.update_status("No WAV files detected in selection.")
            return

        existing = {path.resolve() for path in self.wav_files}
        added = 0
        for path in new_paths:
            if path.resolve() in existing:
                continue
            self.wav_files.append(path)
            existing.add(path.resolve())
            added += 1

        if added:
            self.update_status(f"Added {added} file(s).")
        else:
            self.update_status("Files already in list.")

        self._refresh_listbox()

    def _refresh_listbox(self) -> None:
        self.file_listbox.delete(0, tk.END)
        for path in self.wav_files:
            self.file_listbox.insert(tk.END, path.name)

    def clear_list(self) -> None:
        self.wav_files.clear()
        self._refresh_listbox()
        self.update_status("Cleared file list.")

    # Processing
    def process_files(self) -> None:
        pack_name = self.pack_name_var.get().strip()
        if not pack_name:
            messagebox.showerror("Missing Pack Name", "Please enter a pack name before exporting.")
            return
        if not self.wav_files:
            messagebox.showerror("No Files", "Add at least one WAV file to process.")
            return

        self._set_controls_state("disabled")
        self.update_status("Processing…")
        self.root.update_idletasks()

        try:
            output_folder, count = process_wav_files(self.wav_files, pack_name)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Processing Error", str(exc))
            self.update_status("Error during processing.")
            self._set_controls_state("!disabled")
            return

        messagebox.showinfo(
            "Export Complete",
            f"Processed {count} file(s).\nOutput folder:\n{output_folder}",
        )
        self.update_status(f"Done. Exported to {output_folder}")
        self._set_controls_state("!disabled")

    # Utility
    def update_status(self, text: str) -> None:
        self.status_var.set(text)

    def _set_controls_state(self, state: str) -> None:
        for widget in (self.add_button, self.clear_button, self.process_button, self.pack_name_entry, self.drop_area):
            try:
                widget.state([state])
            except tk.TclError:
                # Some widgets may not support state changes (e.g., non-themed widgets)
                pass


def main() -> None:
    tkdnd_module = load_tkdnd_module()
    if tkdnd_module:
        root = tkdnd_module.TkinterDnD.Tk()
    else:
        root = tk.Tk()

    style = ttk.Style(root)
    style.configure("DropArea.TLabel", background="#f8f9fa")
    style.configure("DropArea.TFrame", background="#d1d5db")

    SamplePackMakerApp(root, tkdnd_module=tkdnd_module)
    root.mainloop()


if __name__ == "__main__":
    main()
