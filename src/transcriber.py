import os
import time
from faster_whisper import WhisperModel
import subprocess
import tempfile
from languages import supported_languages
import sys

log_box = None

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # The application is frozen (PyInstaller executable)
        bundle_dir = sys._MEIPASS
    else:
        # The application is running normally
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_executable = os.path.join(bundle_dir, 'ffmpeg.exe')
    return ffmpeg_executable

def set_log_box(log_widget):
    global log_box
    log_box = log_widget

def log(message):
    if log_box:
        log_box.insert("end", message + "\n")
        log_box.see("end")
    else:
        print(message.encode('utf-8', errors='replace').decode('utf-8'))

class ModelManager:
    def __init__(self):
        self.model = None
        self.model_size = None
        self.device = None
        self.compute_type = None

    def load_model(self, model_size="base", device="cpu", compute_type="int8"):
        if self.model is None or self.model_size != model_size or self.device != device or self.compute_type != compute_type:
            log(f"Loading model: size={model_size}, device={device}, compute_type={compute_type}")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self.model_size = model_size
            self.device = device
            self.compute_type = compute_type
        else:
            log("Using cached model.")
        return self.model

model_manager = ModelManager()

def convert_to_audio(input_file):
    try:
        temp_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio_path = temp_audio_file.name
        temp_audio_file.close()

        # Get the path to the bundled ffmpeg executable
        ffmpeg_path = get_ffmpeg_path()

        # Build the command using the full path to ffmpeg.exe
        command = [ffmpeg_path, "-y", "-i", input_file, "-q:a", "0", "-map", "a", temp_audio_path]
        subprocess.run(command, check=True)
        return temp_audio_path
    except subprocess.CalledProcessError as e:
        log(f"Error converting video to audio: {e}")
        raise

def transcribe_audio(model, audio_path, include_timecodes, language_code):
    try:
        start_time = time.time()
        log(f"Starting transcription for {audio_path}")

        if language_code == "autodetect":
            language_code = None

        segments, _ = model.transcribe(audio_path, language=language_code)
        transcriptions = []
        for segment in segments:
            start, end, text = segment.start, segment.end, segment.text
            if include_timecodes:
                transcriptions.append(f"{start:.2f}-{end:.2f}: {text}")
            else:
                transcriptions.append(text)

        transcription_time = time.time() - start_time
        log(f"Transcription completed in {transcription_time:.2f} seconds.")
        return transcriptions
    except Exception as e:
        log(f"An error occurred: {e}")
        return []

def write_transcriptions_to_file(transcriptions, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        for line in transcriptions:
            file.write(line + '\n')
