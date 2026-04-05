"""
gui.py — SimpleWhisper graphical user interface

Layout (top → bottom)
  Header        app name + subtitle
  Files         input / output file pickers with auto-fill
  Settings      model, language, task, processing options
  ▸ Advanced    beam size, quality preset, initial prompt  (collapsible)
  Action        Start button
  Status        status label + animated progress bar
  Log           live scrolling log with Clear button
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os

from transcriber import (
    model_manager,
    transcribe_audio,
    set_log_callback,
    write_transcriptions_to_file,
)
from languages import supported_languages

# ── constants ────────────────────────────────────────────────────────────────

MODEL_SIZES = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
MODEL_HINT  = "tiny/base = fastest  ·  large-v3 = most accurate"

QUALITY_PRESETS = {
    # label: (beam_size, compute_type_cpu, compute_type_gpu)
    "Fast":     (1,  "int8",    "int8_float16"),
    "Balanced": (5,  "int8",    "float16"),
    "Accurate": (10, "float32", "float32"),
}

FMT_OPTIONS = ["Text (.txt)", "SRT (.srt)", "VTT (.vtt)"]
FMT_EXT     = {
    "Text (.txt)": ".txt",
    "SRT (.srt)":  ".srt",
    "VTT (.vtt)":  ".vtt",
}

MEDIA_FILETYPES = [
    (
        "Audio / Video",
        " ".join([
            "*.mp3", "*.wav", "*.ogg", "*.flac", "*.m4a", "*.opus", "*.wma",
            "*.mp4", "*.mkv", "*.avi", "*.mov", "*.m4v", "*.wmv",
            "*.flv", "*.webm", "*.ts",  "*.3gp",
        ]),
    ),
    ("All files", "*.*"),
]

FONT_MONO = ("Courier New", 12) if os.name == "nt" else ("monospace", 12)


# ── main GUI entry point ──────────────────────────────────────────────────────

def start_gui():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("SimpleWhisper")
    root.geometry("680x810")
    root.minsize(560, 680)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # ── thread-safe helpers ──────────────────────────────────────────────────

    def gui_log(msg: str):
        root.after(0, _append_log, msg)

    def _append_log(msg: str):
        log_box.configure(state="normal")
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")

    def _clear_log():
        log_box.configure(state="normal")
        log_box.delete("1.0", "end")
        log_box.configure(state="disabled")

    def set_status(text: str, color: str = "#9e9e9e"):
        root.after(0, lambda: status_label.configure(text=text, text_color=color))

    def set_busy(busy: bool):
        root.after(0, _apply_busy, busy)

    def _apply_busy(busy: bool):
        if busy:
            start_btn.configure(state="disabled", text="⏳  Transcribing…")
            prog_bar.configure(mode="indeterminate")
            prog_bar.start()
        else:
            start_btn.configure(state="normal", text="▶  Start Transcription")
            prog_bar.stop()
            prog_bar.set(0)
            prog_bar.configure(mode="determinate")

    # ── file browsing ────────────────────────────────────────────────────────

    def _current_ext() -> str:
        return FMT_EXT.get(fmt_var.get(), ".txt")

    def browse_input():
        path = filedialog.askopenfilename(filetypes=MEDIA_FILETYPES)
        if not path:
            return
        file_entry.delete(0, ctk.END)
        file_entry.insert(0, path)
        if not output_entry.get():
            output_entry.insert(0, os.path.splitext(path)[0] + _current_ext())

    def browse_output():
        ext = _current_ext()
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{ext.upper()[1:]} files", f"*{ext}"), ("All files", "*.*")],
        )
        if path:
            output_entry.delete(0, ctk.END)
            output_entry.insert(0, path)

    def on_format_change(_=None):
        """Swap the output file extension when the format selector changes."""
        current = output_entry.get()
        if not current:
            return
        base = os.path.splitext(current)[0]
        output_entry.delete(0, ctk.END)
        output_entry.insert(0, base + _current_ext())

    # ── advanced section toggle ──────────────────────────────────────────────

    adv_visible = False

    def toggle_advanced():
        nonlocal adv_visible
        adv_visible = not adv_visible
        if adv_visible:
            adv_frame.grid()
            adv_btn.configure(text="▾  Advanced")
        else:
            adv_frame.grid_remove()
            adv_btn.configure(text="▸  Advanced")

    # ── transcription ────────────────────────────────────────────────────────

    def start_transcription_thread():
        input_file  = file_entry.get().strip()
        output_file = output_entry.get().strip()

        if not input_file or not output_file:
            messagebox.showerror(
                "Missing paths",
                "Please select both an input file and an output file.",
            )
            return
        if not os.path.isfile(input_file):
            messagebox.showerror("File not found", f"Input file not found:\n{input_file}")
            return

        set_busy(True)
        set_status("Starting…", "#f0a500")
        threading.Thread(
            target=_run_transcription,
            args=(input_file, output_file),
            daemon=True,
        ).start()

    def _run_transcription(input_file: str, output_file: str):
        try:
            # Collect settings from UI
            model_size    = model_size_var.get()
            use_gpu       = gpu_var.get()
            device        = "cuda" if use_gpu else "cpu"
            lang_label    = lang_var.get()
            lang_code     = {lbl: code for code, lbl in supported_languages}.get(
                                lang_label, "autodetect")
            task          = "translate" if task_var.get() == "Translate to English" else "transcribe"
            vad_filter    = vad_var.get()
            incl_tc       = timecodes_var.get()
            word_ts       = word_ts_var.get()
            fmt_key       = fmt_var.get()
            fmt           = FMT_EXT.get(fmt_key, ".txt").lstrip(".")

            # Quality preset → beam_size + compute_type
            preset_name   = quality_var.get()
            preset        = QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["Balanced"])
            beam_size, ct_cpu, ct_gpu = preset
            compute_type  = ct_gpu if use_gpu else ct_cpu

            prompt        = prompt_entry.get().strip() or None

            # Load / reuse model
            set_status("Loading model…", "#f0a500")
            model = model_manager.load_model(model_size, device, compute_type)

            # Pass the file directly — faster-whisper handles all
            # audio/video formats internally via its own ffmpeg integration.
            # Pre-converting to WAV is redundant and adds overhead.
            audio_path = input_file

            # Transcribe
            set_status("Transcribing…", "#4fc3f7")
            segments = transcribe_audio(
                model,
                audio_path,
                language_code=lang_code,
                beam_size=beam_size,
                task=task,
                vad_filter=vad_filter,
                word_timestamps=word_ts,
                initial_prompt=prompt,
            )

            # Save output
            write_transcriptions_to_file(
                segments, output_file,
                fmt=fmt,
                include_timecodes=incl_tc,
            )

            set_status(f"Done — {len(segments)} segment(s) saved.", "#66bb6a")
            gui_log(f"Saved → {output_file}")

        except Exception as exc:
            gui_log(f"ERROR: {exc}")
            set_status("Error — see log.", "#ef5350")
        finally:
            set_busy(False)

    # ════════════════════════════════════════════════════════════════════════
    #  LAYOUT
    # ════════════════════════════════════════════════════════════════════════

    outer = ctk.CTkFrame(root, fg_color="transparent")
    outer.grid(row=0, column=0, sticky="nsew", padx=22, pady=18)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(6, weight=1)   # log section expands vertically

    # ── Header ──────────────────────────────────────────────────────────────
    hdr = ctk.CTkFrame(outer, fg_color="transparent")
    hdr.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    hdr.columnconfigure(0, weight=1)

    ctk.CTkLabel(
        hdr, text="SimpleWhisper",
        font=ctk.CTkFont(size=26, weight="bold"),
    ).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(
        hdr,
        text="Speech-to-text transcription  ·  powered by faster-whisper",
        font=ctk.CTkFont(size=12), text_color="gray55",
    ).grid(row=1, column=0, sticky="w")

    # ── Files card ──────────────────────────────────────────────────────────
    files_card = ctk.CTkFrame(outer)
    files_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    files_card.columnconfigure(1, weight=1)

    ctk.CTkLabel(
        files_card, text="FILES",
        font=ctk.CTkFont(size=10, weight="bold"), text_color="gray50",
    ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 2))

    ctk.CTkLabel(files_card, text="Input:").grid(
        row=1, column=0, sticky="w", padx=14, pady=(4, 4))
    file_entry = ctk.CTkEntry(
        files_card, placeholder_text="Select an audio or video file…")
    file_entry.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=(4, 4))
    ctk.CTkButton(
        files_card, text="Browse", width=82, command=browse_input,
    ).grid(row=1, column=2, padx=(0, 14), pady=(4, 4))

    ctk.CTkLabel(files_card, text="Output:").grid(
        row=2, column=0, sticky="w", padx=14, pady=(0, 10))
    output_entry = ctk.CTkEntry(
        files_card, placeholder_text="Save transcription as…")
    output_entry.grid(row=2, column=1, sticky="ew", padx=(0, 6), pady=(0, 10))
    ctk.CTkButton(
        files_card, text="Browse", width=82, command=browse_output,
    ).grid(row=2, column=2, padx=(0, 14), pady=(0, 10))

    # ── Settings card ───────────────────────────────────────────────────────
    sett = ctk.CTkFrame(outer)
    sett.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    sett.columnconfigure(1, weight=1)
    sett.columnconfigure(3, weight=2)

    ctk.CTkLabel(
        sett, text="SETTINGS",
        font=ctk.CTkFont(size=10, weight="bold"), text_color="gray50",
    ).grid(row=0, column=0, columnspan=6, sticky="w", padx=14, pady=(10, 2))

    # Row 1 — Model + Language
    ctk.CTkLabel(sett, text="Model:").grid(row=1, column=0, sticky="w", padx=14, pady=4)
    model_size_var = ctk.StringVar(value="base")
    ctk.CTkComboBox(
        sett, variable=model_size_var, values=MODEL_SIZES, width=145,
    ).grid(row=1, column=1, sticky="w", padx=(0, 14), pady=4)

    ctk.CTkLabel(sett, text="Language:").grid(row=1, column=2, sticky="w", padx=(0, 6), pady=4)
    lang_var = ctk.StringVar(value="Autodetect")
    ctk.CTkComboBox(
        sett, variable=lang_var,
        values=[lbl for _, lbl in supported_languages],
    ).grid(row=1, column=3, columnspan=2, sticky="ew", padx=(0, 14), pady=4)

    # Model hint
    ctk.CTkLabel(
        sett, text=MODEL_HINT,
        font=ctk.CTkFont(size=11), text_color="gray50",
    ).grid(row=2, column=0, columnspan=6, sticky="w", padx=14, pady=(0, 6))

    # Row 3 — Task
    ctk.CTkLabel(sett, text="Task:").grid(row=3, column=0, sticky="w", padx=14, pady=(0, 4))
    task_var = ctk.StringVar(value="Transcribe")
    ctk.CTkSegmentedButton(
        sett,
        values=["Transcribe", "Translate to English"],
        variable=task_var,
    ).grid(row=3, column=1, columnspan=4, sticky="w", padx=(0, 14), pady=(0, 4))

    # Row 4 — Checkboxes row 1
    chk_row1 = ctk.CTkFrame(sett, fg_color="transparent")
    chk_row1.grid(row=4, column=0, columnspan=6, sticky="ew", padx=14, pady=(2, 2))

    gpu_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(chk_row1, text="Use GPU (CUDA)", variable=gpu_var).pack(
        side="left", padx=(0, 24))

    vad_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(
        chk_row1,
        text="VAD filter  (skips silence — faster for long files)",
        variable=vad_var,
    ).pack(side="left", padx=(0, 24))

    # Row 5 — Checkboxes row 2
    chk_row2 = ctk.CTkFrame(sett, fg_color="transparent")
    chk_row2.grid(row=5, column=0, columnspan=6, sticky="ew", padx=14, pady=(2, 2))

    timecodes_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(chk_row2, text="Include timecodes", variable=timecodes_var).pack(
        side="left", padx=(0, 24))

    word_ts_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(chk_row2, text="Word-level timestamps", variable=word_ts_var).pack(
        side="left", padx=(0, 24))

    # Row 6 — Output format
    fmt_row = ctk.CTkFrame(sett, fg_color="transparent")
    fmt_row.grid(row=6, column=0, columnspan=6, sticky="ew", padx=14, pady=(4, 4))

    ctk.CTkLabel(fmt_row, text="Output format:").pack(side="left", padx=(0, 10))
    fmt_var = ctk.StringVar(value="Text (.txt)")
    ctk.CTkSegmentedButton(
        fmt_row,
        values=FMT_OPTIONS,
        variable=fmt_var,
        command=on_format_change,
    ).pack(side="left")

    # ── Advanced toggle ──────────────────────────────────────────────────────
    adv_btn = ctk.CTkButton(
        sett,
        text="▸  Advanced",
        fg_color="transparent",
        hover_color=("gray80", "gray30"),
        text_color=("gray40", "gray60"),
        font=ctk.CTkFont(size=12),
        anchor="w",
        command=toggle_advanced,
    )
    adv_btn.grid(row=7, column=0, columnspan=6, sticky="w", padx=10, pady=(2, 4))

    # Advanced frame (hidden by default)
    adv_frame = ctk.CTkFrame(sett, fg_color=("gray85", "gray20"))
    adv_frame.columnconfigure(1, weight=1)
    adv_frame.grid(row=8, column=0, columnspan=6, sticky="ew", padx=14, pady=(0, 8))
    adv_frame.grid_remove()

    ctk.CTkLabel(
        adv_frame, text="Quality preset:",
        font=ctk.CTkFont(size=12),
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))
    quality_var = ctk.StringVar(value="Balanced")
    ctk.CTkSegmentedButton(
        adv_frame,
        values=list(QUALITY_PRESETS.keys()),
        variable=quality_var,
    ).grid(row=0, column=1, columnspan=2, sticky="w", padx=(0, 12), pady=(10, 4))

    ctk.CTkLabel(
        adv_frame,
        text="Fast = beam 1, quantised  ·  Balanced = beam 5  ·  Accurate = beam 10, full precision",
        font=ctk.CTkFont(size=11), text_color="gray50",
    ).grid(row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))

    ctk.CTkLabel(
        adv_frame, text="Initial prompt:",
        font=ctk.CTkFont(size=12),
    ).grid(row=2, column=0, sticky="w", padx=12, pady=(4, 10))
    prompt_entry = ctk.CTkEntry(
        adv_frame,
        placeholder_text='Optional — e.g. "Medical terms: stethoscope, aorta…"',
    )
    prompt_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=(4, 10))

    # ── Start button ─────────────────────────────────────────────────────────
    start_btn = ctk.CTkButton(
        outer,
        text="▶  Start Transcription",
        font=ctk.CTkFont(size=14, weight="bold"),
        height=44,
        command=start_transcription_thread,
    )
    start_btn.grid(row=3, column=0, sticky="ew", pady=(0, 6))

    # ── Status + progress bar ────────────────────────────────────────────────
    stat_row = ctk.CTkFrame(outer, fg_color="transparent")
    stat_row.grid(row=4, column=0, sticky="ew")
    stat_row.columnconfigure(1, weight=1)

    ctk.CTkLabel(stat_row, text="Status:", text_color="gray50").grid(
        row=0, column=0, sticky="w")
    status_label = ctk.CTkLabel(stat_row, text="Idle", text_color="gray50")
    status_label.grid(row=0, column=1, sticky="w", padx=8)

    prog_bar = ctk.CTkProgressBar(outer, mode="determinate")
    prog_bar.set(0)
    prog_bar.grid(row=5, column=0, sticky="ew", pady=(4, 8))

    # ── Log card ─────────────────────────────────────────────────────────────
    log_card = ctk.CTkFrame(outer)
    log_card.grid(row=6, column=0, sticky="nsew", pady=(0, 4))
    log_card.columnconfigure(0, weight=1)
    log_card.rowconfigure(1, weight=1)

    log_hdr = ctk.CTkFrame(log_card, fg_color="transparent")
    log_hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
    log_hdr.columnconfigure(0, weight=1)

    ctk.CTkLabel(
        log_hdr, text="LOG",
        font=ctk.CTkFont(size=10, weight="bold"), text_color="gray50",
    ).grid(row=0, column=0, sticky="w")
    ctk.CTkButton(
        log_hdr, text="Clear", width=56, height=24,
        fg_color="transparent", border_width=1,
        command=_clear_log,
    ).grid(row=0, column=1, sticky="e")

    log_box = ctk.CTkTextbox(
        log_card,
        height=170,
        state="disabled",
        font=ctk.CTkFont(family=FONT_MONO[0], size=FONT_MONO[1]),
    )
    log_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 14))

    # Wire log callback
    set_log_callback(gui_log)

    root.mainloop()
