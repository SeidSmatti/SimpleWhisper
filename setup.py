from setuptools import setup, find_packages

setup(
    name="SimpleWhisper",
    version="0.1",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        "customtkinter",
        "faster-whisper",
    ],
    entry_points={
        'console_scripts': [
            'simplewhisper=src.main:main',
        ],
    },
)
