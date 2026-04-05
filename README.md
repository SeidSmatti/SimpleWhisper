# SimpleWhisper

A user-friendly speech-to-text transcription tool built on top of [faster-whisper](https://github.com/SYSTRAN/faster-whisper), an optimised implementation of [OpenAI Whisper](https://github.com/openai/whisper) for CPU and GPU.

SimpleWhisper was developed as part of the [LaCAS Project](https://lacas.inalco.fr/le-projet-lacas) for [INALCO](https://www.inalco.fr/) (Institut National des Langues et Civilisations Orientales).

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [From source](#from-source)
  - [Pre-built binaries](#pre-built-binaries)
- [Usage](#usage)
  - [Launching](#launching)
  - [Workflow](#workflow)
  - [Advanced options](#advanced-options)
  - [Performance tips](#performance-tips)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)
- [Changelog](#changelog)
- [About](#about)

## Features

| Feature | Details |
|---|---|
| **Broad format support** | Any audio (MP3, WAV, OGG, FLAC, M4A, OPUS…) or video (MP4, MKV, AVI, MOV, WebM, WMV…) — passed directly to faster-whisper, no pre-conversion overhead. |
| **Model selection** | `tiny` → `large-v3` — trade speed for accuracy. |
| **Language selection** | 58 languages or automatic detection. Detected language and confidence are shown in the log. |
| **Translation** | Built-in speech-to-English translation via the Whisper `translate` task. |
| **VAD filter** | Optional Voice Activity Detection (Silero) — skips silent regions; ~40–60 % faster on long audio with pauses. |
| **Quality presets** | Fast / Balanced / Accurate — sets beam size and compute precision together. |
| **Output formats** | Plain text, **SRT subtitles**, or **WebVTT subtitles** — file extension auto-updated. |
| **Word-level timestamps** | Optional per-word start/end times. |
| **Initial prompt** | Prime the model with domain vocabulary for better accuracy. |
| **GPU acceleration** | CUDA with one checkbox; precision auto-selected per device. |
| **Model caching** | Already-loaded models reused across consecutive runs. |
| **Auto CPU threads** | Uses all available CPU cores automatically. |
| **Live log** | Every segment streamed to the log panel as it is decoded. |
| **Auto-fill output path** | Output filename pre-filled from the input path. |

## Installation

### Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.8+ | |
| `ffmpeg` | Must be on your `PATH`. See the [installation guide](https://gist.github.com/barbietunnie/47a3de3de3274956617ce092a3bc03a1). |
| `tkinter` | Usually bundled with Python; see table below if missing. |
| CUDA Toolkit | Optional — only needed for GPU mode. See [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit). |

If `tkinter` is missing:

| Platform | Command |
|---|---|
| macOS | `brew install python-tk` |
| Linux (Debian/Ubuntu) | `sudo apt-get install python3-tk` |
| Windows | Shipped with the standard Python installer; see [tkdocs](https://tkdocs.com/tutorial/install.html) if absent. |

### From source

```sh
git clone https://github.com/SeidSmatti/SimpleWhisper.git
cd SimpleWhisper

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Pre-built binaries

Pre-built (unsigned) binaries for Linux and Windows are available on the [Releases](https://github.com/SeidSmatti/SimpleWhisper/releases) page — no Python installation required.

## Usage

### Launching

Run directly from the source tree:

```sh
python src/main.py
```

Or install as a package and use the console entry point:

```sh
pip install .
simplewhisper
```

### Workflow

1. **Input** — click *Browse* and select any audio or video file.
2. **Output** — the output path is pre-filled automatically; edit if needed.
3. **Model size** — `base` or `small` for everyday use; `large-v3` for maximum accuracy.
4. **Language** — pick a language or leave *Autodetect*. The detected language and confidence appear in the log.
5. **Task** — *Transcribe* (default) keeps the source language; *Translate to English* produces an English transcript from any source language.
6. **Output format** — Text, SRT, or VTT. The file extension updates automatically when you change this.
7. **Start** — click **▶ Start Transcription** and watch live progress in the log.

### Advanced options

Open the collapsible **▸ Advanced** panel for fine-grained control:

- **Quality preset**
  - *Fast* — beam size 1, quantised precision.
  - *Balanced* — beam size 5 (the faster-whisper default).
  - *Accurate* — beam size 10, full `float32` precision.
- **Initial prompt** — optional text hint to bias vocabulary or formatting style (e.g. `"Medical terms: stethoscope, aorta…"`).
- **VAD filter** *(in main options)* — off by default. Enable for long recordings with pauses (lectures, interviews) to skip silent regions. For short files or fast models it can add more overhead than it saves.
- **Word-level timestamps** *(in main options)* — adds per-word timing to each segment.

### Performance tips

| Scenario | Recommended settings |
|---|---|
| Short clip, any language | `base` + Balanced preset, VAD **off** |
| Long lecture / interview with pauses | `small` or `medium` + VAD **on** |
| Best accuracy, known language | `large-v3` + Accurate preset, language pinned |
| Subtitles for a video | Any model + SRT or VTT output format |
| Foreign audio → English transcript | Any model + *Translate to English* task |
| GPU available | Enable *Use GPU* — `float16` is selected automatically |
| Quick draft on CPU | `base` + Fast preset |

> **Note on VAD:** Voice Activity Detection loads the Silero VAD model and scans the entire audio before decoding. On short files or with the `base` model, this pre-processing can outweigh the savings from skipping silence. Leave it off for quick jobs and enable it for long recordings.

## Troubleshooting

### Missing CUDA DLL (Windows)

```
Could not locate cudnn_ops_infer64_8.dll. Please make sure it is in your library path!
```

Try [this fix](https://github.com/Purfview/whisper-standalone-win/releases/tag/libs) — place the DLL files alongside the executable or in a directory on your `PATH`.

### ffmpeg not found

Ensure `ffmpeg` is installed and reachable from the terminal:

```sh
ffmpeg -version
```

See the [installation guide](https://gist.github.com/barbietunnie/47a3de3de3274956617ce092a3bc03a1) for platform-specific steps.

## Resources

- [OpenAI Whisper](https://github.com/openai/whisper)
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)

## Changelog

| Date | Changes |
|---|---|
| 2026-04-05 | **v1.1.0.** Redesigned GUI (header, grouped cards, status bar, progress bar, live log, clear button, auto-fill output path, file-type filter). New features: *Translate to English* task, SRT and VTT subtitle output, quality presets, word-level timestamps, initial prompt, optional VAD filter, language detection info in log. Performance: removed redundant pre-conversion step — files now go directly to faster-whisper; auto CPU-thread detection. Fixes: ffmpeg path on Linux/macOS, `setup.py` console entry point, thread-safe UI updates. |
| 2024-09-17 | Model caching, responsive threading, safe temp-file handling, enhanced error handling, code modularisation. |
| 2024-07-22 | Added manual language selection. |

## About

SimpleWhisper was initially developed as part of the LaCAS Project for INALCO (Institut National des Langues et Civilisations Orientales). The project aims to make advanced transcription technology accessible to a broad, non-technical audience as part of the collaborative efforts within the LaCAS team to advance areal studies through innovative technological solutions.
