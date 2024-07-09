import unittest
import os
from src.transcriber import load_model, convert_to_audio, transcribe_audio

class TestTranscriber(unittest.TestCase):

    def setUp(self):
        self.test_audio_file = "test_audio.wav"
        self.test_video_file = "test_video.mp4"
        self.output_file = "test_transcription.txt"
        # Create a dummy audio file for testing
        with open(self.test_audio_file, 'wb') as f:
            f.write(os.urandom(1024))  # 1KB of random bytes

    def tearDown(self):
        # Clean up files after test
        if os.path.exists(self.test_audio_file):
            os.remove(self.test_audio_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_load_model(self):
        model = load_model()
        self.assertIsNotNone(model)

    def test_convert_to_audio(self):
        # This test requires ffmpeg and a valid test_video_file
        # Ensure to have a small video file named test_video.mp4 in the test directory
        output_audio = "test_output_audio.wav"
        try:
            convert_to_audio(self.test_video_file, output_audio)
            self.assertTrue(os.path.exists(output_audio))
        finally:
            if os.path.exists(output_audio):
                os.remove(output_audio)

    def test_transcribe_audio(self):
        model = load_model()
        transcribe_audio(model, self.test_audio_file, self.output_file, include_timecodes=False)
        self.assertTrue(os.path.exists(self.output_file))

if __name__ == '__main__':
    unittest.main()
