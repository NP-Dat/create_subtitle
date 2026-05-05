import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.audio_extractor import extract_audio, check_ffmpeg
from core.transcriber import transcribe_audio, AVAILABLE_MODELS, LANGUAGE_OPTIONS
from core.subtitle_converter import convert_segments
from utils.file_helpers import (
    validate_video_file,
    validate_text_file,
    cleanup_temp_file,
    segments_to_text,
    parse_text_to_segments,
    read_text_file,
    write_text_file,
)


class SubtitleApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Create Subtitle")
        self.root.geometry("750x580")
        self.root.minsize(650, 500)

        self._current_segments: list[dict] = []
        self._generated_text: str = ""
        self._converted_content: str = ""
        self._converted_format: str = ""
        self._is_processing = False

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._tab_video = ttk.Frame(notebook)
        self._tab_text = ttk.Frame(notebook)
        notebook.add(self._tab_video, text="  Video → Subtitle  ")
        notebook.add(self._tab_text, text="  Text → Subtitle File  ")

        self._build_video_tab()
        self._build_text_tab()

    # ──────────────────────────────────────────────
    #  Tab 1: Video → Subtitle Text
    # ──────────────────────────────────────────────

    def _build_video_tab(self):
        frame = self._tab_video

        # --- File selection ---
        file_frame = ttk.LabelFrame(frame, text="Video File", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._video_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self._video_path_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_video).pack(side=tk.RIGHT)

        # --- Options ---
        options_frame = ttk.LabelFrame(frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(options_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self._model_var = tk.StringVar(value="small")
        model_combo = ttk.Combobox(
            options_frame, textvariable=self._model_var,
            values=AVAILABLE_MODELS, state="readonly", width=12
        )
        model_combo.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(options_frame, text="Language:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self._language_var = tk.StringVar(value="Japanese")
        lang_combo = ttk.Combobox(
            options_frame, textvariable=self._language_var,
            values=list(LANGUAGE_OPTIONS.keys()), state="readonly", width=14
        )
        lang_combo.grid(row=0, column=3)

        # --- Action buttons ---
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self._generate_btn = ttk.Button(
            btn_frame, text="Generate Subtitle", command=self._on_generate
        )
        self._generate_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._save_txt_btn = ttk.Button(
            btn_frame, text="Save .txt", command=self._save_txt, state=tk.DISABLED
        )
        self._save_txt_btn.pack(side=tk.LEFT)

        # --- Progress ---
        self._progress_var = tk.StringVar(value="Ready.")
        ttk.Label(frame, textvariable=self._progress_var, foreground="gray").pack(
            fill=tk.X, padx=10, pady=(0, 5), anchor=tk.W
        )

        self._progressbar = ttk.Progressbar(frame, mode="indeterminate")
        self._progressbar.pack(fill=tk.X, padx=10, pady=(0, 5))

        # --- Result preview ---
        preview_frame = ttk.LabelFrame(frame, text="Result Preview", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self._video_result_text = tk.Text(preview_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._video_result_text.yview)
        self._video_result_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._video_result_text.pack(fill=tk.BOTH, expand=True)

    def _browse_video(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._video_path_var.set(path)

    def _on_generate(self):
        video_path = self._video_path_var.get()
        if not video_path:
            messagebox.showwarning("No File", "Please select a video file first.")
            return
        if not validate_video_file(video_path):
            messagebox.showerror("Invalid File", "The selected file is not a supported video format.")
            return
        if not check_ffmpeg():
            messagebox.showerror(
                "ffmpeg Not Found",
                "ffmpeg is not installed or not in PATH.\n"
                "Please install ffmpeg to extract audio from video files.",
            )
            return

        self._set_processing(True)
        thread = threading.Thread(target=self._generate_worker, args=(video_path,), daemon=True)
        thread.start()

    def _generate_worker(self, video_path: str):
        temp_wav = None
        try:
            temp_wav = extract_audio(video_path, progress_callback=self._update_progress)

            language_code = LANGUAGE_OPTIONS.get(self._language_var.get(), "ja")
            model_size = self._model_var.get()

            segments = transcribe_audio(
                temp_wav,
                model_size=model_size,
                language=language_code,
                progress_callback=self._update_progress,
            )

            self._current_segments = segments
            self._generated_text = segments_to_text(segments)

            self.root.after(0, self._show_video_result, self._generated_text)
            self.root.after(0, lambda: self._save_txt_btn.configure(state=tk.NORMAL))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            cleanup_temp_file(temp_wav)
            self.root.after(0, lambda: self._set_processing(False))

    def _update_progress(self, message: str):
        self.root.after(0, lambda: self._progress_var.set(message))

    def _show_video_result(self, text: str):
        self._video_result_text.configure(state=tk.NORMAL)
        self._video_result_text.delete("1.0", tk.END)
        self._video_result_text.insert(tk.END, text)
        self._video_result_text.configure(state=tk.DISABLED)

    def _save_txt(self):
        if not self._generated_text:
            messagebox.showwarning("No Data", "No subtitle text to save. Generate subtitles first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Subtitle Text",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if path:
            try:
                write_text_file(path, self._generated_text)
                messagebox.showinfo("Saved", f"Subtitle text saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def _set_processing(self, is_processing: bool):
        self._is_processing = is_processing
        if is_processing:
            self._generate_btn.configure(state=tk.DISABLED)
            self._progressbar.start(10)
        else:
            self._generate_btn.configure(state=tk.NORMAL)
            self._progressbar.stop()
            if not self._is_processing:
                self._progress_var.set("Done.")

    # ──────────────────────────────────────────────
    #  Tab 2: Text → Subtitle File
    # ──────────────────────────────────────────────

    def _build_text_tab(self):
        frame = self._tab_text

        # --- File selection ---
        file_frame = ttk.LabelFrame(frame, text="Text Subtitle File (.txt)", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._text_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self._text_path_var, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_text).pack(side=tk.RIGHT)

        # --- Preview ---
        preview_frame = ttk.LabelFrame(frame, text="File Preview", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._text_preview = tk.Text(preview_frame, wrap=tk.WORD, height=8, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self._text_preview.yview)
        self._text_preview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text_preview.pack(fill=tk.BOTH, expand=True)

        # --- Output format ---
        format_frame = ttk.LabelFrame(frame, text="Output Format", padding=10)
        format_frame.pack(fill=tk.X, padx=10, pady=5)

        self._format_var = tk.StringVar(value="srt")
        for fmt in ("srt", "ass", "ssa"):
            ttk.Radiobutton(
                format_frame, text=f".{fmt}", variable=self._format_var, value=fmt
            ).pack(side=tk.LEFT, padx=(0, 20))

        # --- Action buttons ---
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self._convert_btn = ttk.Button(btn_frame, text="Convert", command=self._on_convert)
        self._convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._save_sub_btn = ttk.Button(
            btn_frame, text="Save As", command=self._save_subtitle, state=tk.DISABLED
        )
        self._save_sub_btn.pack(side=tk.LEFT)

        self._convert_status_var = tk.StringVar(value="")
        ttk.Label(btn_frame, textvariable=self._convert_status_var, foreground="gray").pack(
            side=tk.LEFT, padx=10
        )

    def _browse_text(self):
        path = filedialog.askopenfilename(
            title="Select Text Subtitle File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self._text_path_var.set(path)
            self._load_text_preview(path)

    def _load_text_preview(self, path: str):
        try:
            content = read_text_file(path)
            lines = content.strip().splitlines()
            preview = "\n".join(lines[:20])
            if len(lines) > 20:
                preview += f"\n\n... ({len(lines)} lines total)"

            self._text_preview.configure(state=tk.NORMAL)
            self._text_preview.delete("1.0", tk.END)
            self._text_preview.insert(tk.END, preview)
            self._text_preview.configure(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read file:\n{e}")

    def _on_convert(self):
        text_path = self._text_path_var.get()
        if not text_path:
            messagebox.showwarning("No File", "Please select a text subtitle file first.")
            return
        if not validate_text_file(text_path):
            messagebox.showerror("Invalid File", "Please select a valid .txt file.")
            return

        try:
            content = read_text_file(text_path)
            segments = parse_text_to_segments(content)
            if not segments:
                messagebox.showwarning(
                    "No Segments",
                    "Could not parse any subtitle segments from the file.\n"
                    "Expected format: [HH:MM:SS.mmm --> HH:MM:SS.mmm] Text",
                )
                return

            fmt = self._format_var.get()
            self._converted_content = convert_segments(segments, fmt)
            self._converted_format = fmt
            self._save_sub_btn.configure(state=tk.NORMAL)
            self._convert_status_var.set(f"Converted {len(segments)} segments to .{fmt}")

        except Exception as e:
            messagebox.showerror("Conversion Error", str(e))

    def _save_subtitle(self):
        if not self._converted_content:
            messagebox.showwarning("No Data", "No converted subtitle to save. Convert first.")
            return

        fmt = self._converted_format
        path = filedialog.asksaveasfilename(
            title="Save Subtitle File",
            defaultextension=f".{fmt}",
            filetypes=[
                (f"{fmt.upper()} files", f"*.{fmt}"),
                ("All files", "*.*"),
            ],
        )
        if path:
            try:
                write_text_file(path, self._converted_content)
                messagebox.showinfo("Saved", f"Subtitle file saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))


def run():
    root = tk.Tk()
    SubtitleApp(root)
    root.mainloop()
