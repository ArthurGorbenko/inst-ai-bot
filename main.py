import cv2
import os
import subprocess

import whisper

from scenedetect import detect, AdaptiveDetector
from concurrent.futures import ThreadPoolExecutor

path = "./reels/3481080082629109504_5599290503.mp4"


def detect_and_save_scenes(video_path):
    print("saving")
    output_dir = "./scenes"  # Changed to relative path

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    try:
        scene_list = detect(video_path, AdaptiveDetector())
        print(scene_list)
        video = cv2.VideoCapture(video_path)

        if not video.isOpened():
            raise Exception("Error: Could not open video file")

        # Save first frame from each scene
        for i, scene in enumerate(scene_list):
            # Set frame position to start of scene
            video.set(cv2.CAP_PROP_POS_FRAMES, scene[0].frame_num)
            ret, frame = video.read()
            if ret:
                output_path = os.path.join(output_dir, f"scene_{i:03d}.jpg")
                cv2.imwrite(output_path, frame)

        video.release()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if "video" in locals():
            video.release()


def extract_audio(path):
    try:
        output = "./temp/audio.wav"
        # Create temp directory if it doesn't exist
        os.makedirs("./temp", exist_ok=True)

        print("Starting audio extraction...")
        command = f"ffmpeg -i {path} -ab 160k -ac 2 -ar 44100 -vn ./temp/audio.wav"
        subprocess.call(command, shell=True)

        print("Loading Whisper model...")
        model = whisper.load_model("large")

        print("Transcribing audio...")
        result = model.transcribe(output)

        new_list = list(
            map(
                lambda x: {
                    "start": round(x.get("start"), 1),
                    "end": round(x.get("end"), 1),
                    "text": x.get("text"),
                },
                result.get("segments"),
            )
        )
        print("Transcription result:", new_list)
        return new_list
    except Exception as e:
        print(f"Error in extract_audio: {str(e)}")
        raise


with ThreadPoolExecutor(max_workers=2) as executor:
    future1 = executor.submit(detect_and_save_scenes, path)
    future2 = executor.submit(extract_audio, path)


print("finished in parallel")
