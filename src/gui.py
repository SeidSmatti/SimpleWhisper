import customtkinter as ctk
from tkinter import filedialog, messagebox
from transcriber import load_model, convert_to_audio, transcribe_audio, set_log_box, log
import threading
import os

def start_gui():
    def browse_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            file_entry.delete(0, ctk.END)
            file_entry.insert(0, file_path)

    def browse_output():
        output_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if output_path:
            output_entry.delete(0, ctk.END)
            output_entry.insert(0, output_path)

    def start_transcription_thread():
        threading.Thread(target=start_transcription).start()

    def start_transcription():
        input_file = file_entry.get()
        output_file = output_entry.get()
        model_size = model_size_var.get()
        device = "cuda" if gpu_var.get() else "cpu"
        include_timecodes = timecodes_var.get()

        if not input_file or not output_file:
            messagebox.showerror("Error", "Please select an input file and an output file.")
            return

        model = load_model(model_size, device, "int8" if device == "cpu" else "float16")

        audio_path = "temp_audio.wav"
        if input_file.endswith(('.mp4', '.mkv', '.avi')):
            log("Converting video to audio...")
            convert_to_audio(input_file, audio_path)
        else:
            audio_path = input_file

        transcribe_audio(model, audio_path, output_file, include_timecodes)

        if audio_path == "temp_audio.wav" and os.path.exists(audio_path):
            os.remove(audio_path)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("SimpleWhisper Transcription Tool")

    frame = ctk.CTkFrame(root)
    frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    ctk.CTkLabel(frame, text="Input File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    file_entry = ctk.CTkEntry(frame, width=400)
    file_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    ctk.CTkButton(frame, text="Browse", command=browse_file).grid(row=0, column=2, sticky="w", padx=5, pady=5)

    ctk.CTkLabel(frame, text="Output File:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    output_entry = ctk.CTkEntry(frame, width=400)
    output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    ctk.CTkButton(frame, text="Browse", command=browse_output).grid(row=1, column=2, sticky="w", padx=5, pady=5)

    ctk.CTkLabel(frame, text="Model Size:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    model_size_var = ctk.StringVar(value="base")
    ctk.CTkComboBox(frame, variable=model_size_var, values=["base", "small", "medium", "large", "large-v2", "large-v3"]).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

    gpu_var = ctk.BooleanVar()
    ctk.CTkCheckBox(frame, text="Use GPU", variable=gpu_var).grid(row=3, column=0, sticky="w", padx=5, pady=5)

    timecodes_var = ctk.BooleanVar()
    ctk.CTkCheckBox(frame, text="Include Timecodes", variable=timecodes_var).grid(row=3, column=1, sticky="w", padx=5, pady=5)

    ctk.CTkButton(frame, text="Start Transcription", command=start_transcription_thread).grid(row=4, column=0, columnspan=3, pady=10)

    log_box = ctk.CTkTextbox(frame, height=200, width=600)
    log_box.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

    set_log_box(log_box)  # Set the log box for the transcriber

    root.mainloop()
