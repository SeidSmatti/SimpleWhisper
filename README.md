# SimpleWhisper

A user-friendly transcription tool using the [faster-whisper](https://github.com/SYSTRAN/faster-whisper) library, optimizing [Whisper](https://github.com/openai/whisper) models performance for CPU and GPU transcribing.

## Motivation

SimpleWhisper was developed as part of the [LaCAS Project](https://lacas.inalco.fr/le-projet-lacas) for [INALCO](https://www.inalco.fr/) (Institut National des Langues et Civilisations Orientales).

 The primary motivation behind this project is to simplify the usage of the Whisper model by creating an accessible GUI, making advanced transcription technology available to a wider audience without requiring extensive technical knowledge.

## Method and Results

### Method

The faster-whisper library, developed by SYSTRAN, offers an optimized and efficient automatic speech recognition (ASR) system. Despite its powerful capabilities, Whisper requires command-line interactions and technical setup, which can be a barrier for many users. SimpleWhisper addresses this by providing a graphical user interface (GUI) that abstracts the complexity of the Whisper model, allowing users to easily transcribe audio or video files.

**Key features:**
- **Model Loading:** Load different sizes of Whisper models based on user requirements.
- **Audio Conversion:** Convert video files to audio format using `ffmpeg`.
- **Transcription:** Transcribe audio files with or without timecodes.
- **GPU Acceleration:** Utilize CUDA for GPU acceleration to speed up transcription (if available).


## Running Instructions

To run SimpleWhisper, follow these steps:

### Prerequisites

- Python 3.7 or higher
- `ffmpeg` installed and available in the system path. 
- For GPU acceleration (optional), ensure you have CUDA installed. Check [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) for installation instructions.


[FFMPEG installation tutorials](https://gist.github.com/barbietunnie/47a3de3de3274956617ce092a3bc03a1) 

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/SeidSmatti/SimpleWhisper.git
    cd SimpleWhisper
    ```

2. Create a virtual environment(optional):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

### Usage

1. Run the application:
    ```sh
    python src/main.py
    ```

2. Alternatively, install the package and use the entry point:
    ```sh
    pip install .
    simplewhisper
    ```

### Features

- Loading video or audio formats (with automatic conversion).
- Basic output formating choice.
- A choice between running the model on CPU or GPU.


### Running Tests

Run the unit tests to ensure everything is working correctly:
```sh
python -m unittest discover -s tests
```

## More Resources

For more information on Whisper, faster-whisper, and CUDA:
- [Open-AI Whisper](https://github.com/openai/whisper)
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)


## About

SimpleWhisper was initially developed as part of the LaCAS Project for INALCO (Institut National des Langues et Civilisations Orientales). The project aims to make advanced transcription technology accessible to a broader audience. 

This project is part of the collaborative efforts within the LaCAS team to advance areal studies through innovative technological solutions.
