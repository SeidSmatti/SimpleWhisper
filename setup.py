from setuptools import setup, find_packages

setup(
    name="SimpleWhisper",
    version="1.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "customtkinter",
        "faster-whisper",
    ],
    entry_points={
        "console_scripts": [
            "simplewhisper=main:main",
        ],
    },
)
