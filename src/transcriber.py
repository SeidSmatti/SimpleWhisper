# src/transcriber.py
import os
import time
from faster_whisper import WhisperModel
import subprocess

log_box = None

def set_log_box(log_widget):
    global log_box
    log_box = log_widget

def log(message):
    if log_box:
        log_box.insert("end", message + "\n")
        log_box.see("end")
    else:
        print(message)

def load_model(model_size="base", device="cpu", compute_type="int8"):
    log("Loading the model...")
    return WhisperModel(model_size, device=device, compute_type=compute_type)

def convert_to_audio(input_file, output_file):
    try:
        command = ["ffmpeg", "-i", input_file, "-q:a", "0", "-map", "a", output_file]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        log(f"Error converting video to audio: {e}")
        raise

def transcribe_audio(model, audio_path, output_path, include_timecodes):
    try:
        start_time = time.time()
        log(f"Starting transcription for {audio_path}")

        segments, _ = model.transcribe(audio_path)

        with open(output_path, "w") as file:
            for segment in segments:
                start, end, text = segment.start, segment.end, segment.text
                if include_timecodes:
                    file.write(f"{start:.2f}-{end:.2f}: {text}\n")
                else:
                    file.write(f"{text}\n")

        transcription_time = time.time() - start_time
        log(f"Transcription with timecodes saved to {output_path}")
        log(f"Transcription completed in {transcription_time:.2f} seconds.")
    except Exception as e:
        log(f"An error occurred: {e}")
