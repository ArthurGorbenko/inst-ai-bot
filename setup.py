from setuptools import setup, find_packages

setup(
    name="video_processor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymongo",
        "paddleocr",
        "pillow",
        "transformers",
        "scenedetect",
        "openai",
        "whisper",
    ],
) 