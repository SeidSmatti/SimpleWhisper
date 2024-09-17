import customtkinter as ctk
from tkinter import filedialog, messagebox
from transcriber import model_manager, convert_to_audio, transcribe_audio, set_log_box, log, write_transcriptions_to_file
import threading
import os
from languages import supported_languages

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
        start_button.configure(state='disabled')
        threading.Thread(target=start_transcription).start()

    def start_transcription():
        try:
            input_file = file_entry.get()
            output_file = output_entry.get()
            model_size = model_size_var.get()
            device = "cuda" if gpu_var.get() else "cpu"
            include_timecodes = timecodes_var.get()
            selected_language_label = language_var.get()
            language_codes = {label: code for code, label in supported_languages}
            selected_language_code = language_codes.get(selected_language_label, "autodetect")

            if not input_file or not output_file:
                messagebox.showerror("Error", "Please select an input file and an output file.")
                return

            model = model_manager.load_model(model_size, device, "int8" if device == "cpu" else "float16")

            if input_file.endswith(('.mp4', '.mkv', '.avi')):
                log("Converting video to audio...")
                audio_path = convert_to_audio(input_file)
                temp_audio = True
            else:
                audio_path = input_file
                temp_audio = False

            # Transcribe audio and get the transcription results
            transcriptions = transcribe_audio(model, audio_path, include_timecodes, selected_language_code)
            
            # Save transcriptions to file
            write_transcriptions_to_file(transcriptions, output_file)

            if temp_audio and os.path.exists(audio_path):
                os.remove(audio_path)

            log("Transcription completed successfully.")
        except Exception as e:
            log(f"An error occurred during transcription: {e}")
        finally:
            # Re-enable the button
            root.after(0, lambda: start_button.configure(state='normal'))

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
    ctk.CTkComboBox(
        frame,
        variable=model_size_var,
        values=["base", "small", "medium", "large", "large-v2", "large-v3"]
    ).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

    ctk.CTkLabel(frame, text="Language:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    language_var = ctk.StringVar(value="Autodetect")
    language_options = [label for code, label in supported_languages]
    ctk.CTkComboBox(frame, variable=language_var, values=language_options).grid(row=3, column=1, sticky="ew", padx=5, pady=5)

    gpu_var = ctk.BooleanVar()
    ctk.CTkCheckBox(frame, text="Use GPU", variable=gpu_var).grid(row=4, column=0, sticky="w", padx=5, pady=5)

    timecodes_var = ctk.BooleanVar()
    ctk.CTkCheckBox(frame, text="Include Timecodes", variable=timecodes_var).grid(row=4, column=1, sticky="w", padx=5, pady=5)

    start_button = ctk.CTkButton(frame, text="Start Transcription", command=start_transcription_thread)
    start_button.grid(row=5, column=0, columnspan=3, pady=10)

    log_box = ctk.CTkTextbox(frame, height=200, width=600)
    log_box.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

    set_log_box(log_box)  # Set the log box for the transcriber

    root.mainloop()


