import os
import subprocess
import easyocr
import whisper

from scenedetect import open_video, detect, AdaptiveDetector, save_images
from concurrent.futures import ThreadPoolExecutor

path = "./reels/3481080082629109504_5599290503.mp4"
image_dir = "./scenes"


def process_scenes(video_path, images_dir):
    detect_and_save_scenes(video_path)
    get_captions(images_dir)


def get_captions(images_path):
    for f in os.listdir(images_path):
        reader = easyocr.Reader(["en"])
        results = reader.readtext(f)

        print("Detected Text:")
        for result in results:
            print(f"{result[1]} (Confidence: {result[2]:.2f})")


def detect_and_save_scenes(video_path):
    print("Saving scene images...")
    output_dir = "./scenes"  # Use a relative output folder.
    os.makedirs(output_dir, exist_ok=True)

    # Open the video using PySceneDetect's helper.
    video = open_video(video_path)

    # Run scene detection with an AdaptiveDetector.
    scene_list = detect(
        video_path,
        AdaptiveDetector(),
    )

    # Save images (by default, a few key frames per scene) to output_dir.
    # The save_images function uses the scene_list and video stream to extract frames.
    save_images(
        scene_list=scene_list,
        video=video,
        image_name_template=f"./scenes/$VIDEO_NAME-Scene-$SCENE_NUMBER-$IMAGE_NUMBER",
    )

    # Clean up: release the video resource.
    video.release()


def extract_transcription(path):
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
        print(f"Error in extract_transcription: {str(e)}")
        raise


with ThreadPoolExecutor(max_workers=2) as executor:
    future1 = executor.submit(process_scenes, path, image_dir)
    future2 = executor.submit(extract_transcription, path)


print("finished in parallel")
