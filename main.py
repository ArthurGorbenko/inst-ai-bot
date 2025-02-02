import os
import subprocess
import easyocr
import whisper

from pymongo import MongoClient
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from scenedetect import open_video, detect, AdaptiveDetector, save_images
from concurrent.futures import ThreadPoolExecutor

path = "./reels/3481080082629109504_5599290503.mp4"
image_dir = "./scenes"


def process_scenes(video_path, images_dir):
    detect_and_save_scenes(video_path)
    get_captions(images_dir)
    generate_scene_description(images_dir)


def generate_scene_description(images_dir):
    print(f"\n=== Starting generate_scene_description for directory: {images_dir} ===")
    try:
        print("Loading BLIP processor and model...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        
        files = os.listdir(images_dir)
        print(f"Found {len(files)} files in directory")
        
        for f in files:
            image_path = os.path.join(images_dir, f)
            print(f"Processing image: {image_path}")
            image = Image.open(image_path)
            inputs = processor(image, return_tensors="pt")
            outputs = model.generate(**inputs)
            caption = processor.decode(outputs[0], skip_special_tokens=True)
            print(f"Generated Caption for {f}: {caption}\n")
    except Exception as e:
        print(f"Error in generate_scene_description: {str(e)}")


def get_captions(images_path):
    print(f"\n=== Starting get_captions for directory: {images_path} ===")
    try:
        files = os.listdir(images_path)
        print(f"Found {len(files)} files in directory")
        
        for f in files:
            image_path = os.path.join(images_path, f)
            print(f"Processing image: {image_path}")
            reader = easyocr.Reader(["en"])
            results = reader.readtext(image_path)

            for result in results:
                print(f"{result[1]} (Confidence: {result[2]:.2f})")
            print()  # Empty line between images
    except Exception as e:
        print(f"Error in get_captions: {str(e)}")


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
    save_images(
        scene_list=scene_list,
        video=video,
        image_name_template=f"./scenes/$VIDEO_NAME--$SCENE_NUMBER--$IMAGE_NUMBER--$TIMECODE",
    )


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
    process_scenes(path, image_dir)
    # future2 = executor.submit(extract_transcription, path)


print("finished in parallel")
