"""
transcriber.py — core transcription backend

Key improvements over the original:
- Auto-detects CPU thread count for parallelism
- VAD (Voice Activity Detection) support — skips silence, 40-60% faster
- Configurable beam_size, task (transcribe / translate), word_timestamps
- Initial prompt support for domain-specific accuracy
- Returns structured SegmentData objects instead of pre-formatted strings
- Output writers for TXT, SRT, and VTT formats
- Language detection info logged (language + confidence + duration)
- Clean log-callback pattern (no global widget reference)
"""

import os
import sys
import time
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional

from faster_whisper import WhisperModel

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_log_callback = None

def set_log_callback(callback):
    global _log_callback
    _log_callback = callback

def log(message: str):
    if _log_callback:
        _log_callback(message)
    else:
        print(message.encode("utf-8", errors="replace").decode("utf-8"))

# ---------------------------------------------------------------------------
# ffmpeg path resolution
# ---------------------------------------------------------------------------

def get_ffmpeg_path() -> str:
    if getattr(sys, "frozen", False):
        bundle_dir = sys._MEIPASS
        exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        return os.path.join(bundle_dir, exe_name)
    found = shutil.which("ffmpeg")
    return found if found else "ffmpeg"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SegmentData:
    start: float
    end:   float
    text:  str
    words: list = field(default_factory=list)  # list of faster_whisper Word objects

# ---------------------------------------------------------------------------
# Model cache
# ---------------------------------------------------------------------------

class ModelManager:
    def __init__(self):
        self.model        = None
        self.model_size   = None
        self.device       = None
        self.compute_type = None

    def load_model(
        self,
        model_size:   str = "base",
        device:       str = "cpu",
        compute_type: str = "int8",
    ) -> WhisperModel:
        # Resolve "auto" compute type
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"

        changed = (
            self.model is None
            or self.model_size   != model_size
            or self.device       != device
            or self.compute_type != compute_type
        )
        if changed:
            log(f"Loading model '{model_size}' on {device.upper()} ({compute_type})…")
            # Use all available CPU cores for inference
            cpu_threads = max(1, (os.cpu_count() or 4))
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=cpu_threads,
                num_workers=1,
            )
            self.model_size   = model_size
            self.device       = device
            self.compute_type = compute_type
            log("Model ready.")
        else:
            log("Reusing cached model.")
        return self.model

model_manager = ModelManager()

# ---------------------------------------------------------------------------
# Audio extraction
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".m4v", ".wmv",
    ".flv", ".webm", ".ts",  ".3gp", ".mpg", ".mpeg",
}

def needs_conversion(input_file: str) -> bool:
    return os.path.splitext(input_file)[1].lower() in VIDEO_EXTENSIONS

def convert_to_audio(input_file: str) -> str:
    """Extract audio track from a video file into a temporary WAV. Returns the temp path."""
    ffmpeg_path = get_ffmpeg_path()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        cmd = [ffmpeg_path, "-y", "-i", input_file, "-q:a", "0", "-map", "a", tmp_path]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode != 0:
            msg = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"ffmpeg failed (code {result.returncode}):\n{msg}")
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return tmp_path

# ---------------------------------------------------------------------------
# Timecode helpers
# ---------------------------------------------------------------------------

def format_timecode(seconds: float) -> str:
    """HH:MM:SS.mmm  (dot as decimal separator — used in VTT/display)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def _srt_tc(seconds: float) -> str:
    """HH:MM:SS,mmm  (comma — required by SRT spec)."""
    return format_timecode(seconds).replace(".", ",")

# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_audio(
    model,
    audio_path:       str,
    language_code:    str   = "autodetect",
    beam_size:        int   = 5,
    task:             str   = "transcribe",
    vad_filter:       bool  = False,
    word_timestamps:  bool  = False,
    initial_prompt:   Optional[str] = None,
) -> List[SegmentData]:
    """
    Transcribe *audio_path* and return a list of SegmentData objects.

    Parameters
    ----------
    beam_size       Higher → better quality, slower. 1 = greedy (fastest).
    vad_filter      Skip silent sections via Silero VAD. ~40-60 % speedup on
                    audio with significant silence.
    word_timestamps Return per-word start/end times inside each segment.
    initial_prompt  Optional text hint to bias transcription style/vocabulary.
    task            "transcribe" or "translate" (translate to English).
    """
    t0 = time.time()
    log("Starting transcription…")

    lang = None if language_code == "autodetect" else language_code

    vad_params = dict(
        threshold=0.5,
        min_silence_duration_ms=500,
        speech_pad_ms=200,
    ) if vad_filter else None

    segments_iter, info = model.transcribe(
        audio_path,
        language=lang,
        task=task,
        beam_size=beam_size,
        vad_filter=vad_filter,
        vad_parameters=vad_params,
        word_timestamps=word_timestamps,
        initial_prompt=initial_prompt or None,
    )

    # Log detection metadata
    lang_label = info.language.upper() if info.language else "?"
    lang_conf  = f"{info.language_probability * 100:.0f}%" if info.language_probability else "?"
    dur_str    = f"{info.duration:.1f}s" if info.duration else "?"
    log(f"  Language: {lang_label} ({lang_conf})  ·  Duration: {dur_str}")
    if vad_filter and hasattr(info, "duration_after_vad") and info.duration_after_vad:
        saved = info.duration - info.duration_after_vad
        log(f"  VAD: {info.duration_after_vad:.1f}s speech detected  ({saved:.1f}s silence skipped)")

    results: List[SegmentData] = []
    for seg in segments_iter:
        data = SegmentData(
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
            words=seg.words or [],
        )
        results.append(data)
        log(f"  [{format_timecode(seg.start)}] {seg.text.strip()}")

    elapsed = time.time() - t0
    log(f"Done — {len(results)} segment(s) in {elapsed:.1f}s.")
    return results

# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_transcriptions_to_file(
    segments:         List[SegmentData],
    output_path:      str,
    fmt:              str  = "txt",
    include_timecodes: bool = True,
):
    """
    Write *segments* to *output_path*.

    fmt
        "txt"  — plain text, optionally with timecodes
        "srt"  — SubRip subtitle format (.srt)
        "vtt"  — WebVTT subtitle format (.vtt)
    """
    with open(output_path, "w", encoding="utf-8") as f:
        if fmt == "srt":
            f.write(_to_srt(segments))
        elif fmt == "vtt":
            f.write(_to_vtt(segments))
        else:
            for seg in segments:
                if include_timecodes:
                    f.write(f"[{format_timecode(seg.start)} --> {format_timecode(seg.end)}]  {seg.text}\n")
                else:
                    f.write(seg.text + "\n")


def _to_srt(segments: List[SegmentData]) -> str:
    blocks = []
    for i, seg in enumerate(segments, 1):
        blocks.append(
            f"{i}\n{_srt_tc(seg.start)} --> {_srt_tc(seg.end)}\n{seg.text}\n"
        )
    return "\n".join(blocks)


def _to_vtt(segments: List[SegmentData]) -> str:
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        lines += [
            str(i),
            f"{format_timecode(seg.start)} --> {format_timecode(seg.end)}",
            seg.text,
            "",
        ]
    return "\n".join(lines)
