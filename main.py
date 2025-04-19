import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from concurrent.futures import ThreadPoolExecutor

# Import directly from modules to avoid circular imports
from video_processor.config import get_config
from video_processor.db import get_mongodb_connection
from video_processor.scene_detect import detect_and_save_scenes
from video_processor.ocr import get_captions
from video_processor.captioning import generate_scene_description
from video_processor.transcription import extract_transcription
from video_processor.matching import match_transcription_to_scenes
from video_processor.summarizer import summarize_scenes

def process_scenes(video_path, images_dir, transcription=None):
    # Get scene timestamps first (still used for description matching if needed)
    scene_timestamps = detect_and_save_scenes(video_path)

    # Note: get_captions no longer looks up the timestamp from scene_timestamps,
    # because the image filename now contains the actual timestamp.
    scenes = get_captions(images_dir, scene_timestamps)
    scenes = generate_scene_description(images_dir, scenes)

    # Match transcriptions to scenes if available
    if transcription:
        scenes = match_transcription_to_scenes(scenes, transcription)

    # Get database connection
    config = get_config()
    db, videos_col = get_mongodb_connection(config)
    
    # Write to MongoDB only once at the end
    print(f"Updating MongoDB with final scenes data: {scenes}")
    videos_col.update_one(
        {"videoId": config.VIDEO_ID},
        {"$set": {"videoId": config.VIDEO_ID, "scenes": scenes}},
        upsert=True,
    )

    return scenes

def main():
    # Load configuration
    config = get_config()
    _, videos_col = get_mongodb_connection(config)
    
    # Create output directory if it doesn't exist
    os.makedirs(config.IMAGE_DIR, exist_ok=True)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Run transcription in parallel
        future2 = executor.submit(extract_transcription, config.VIDEO_PATH)

        # Get transcription result
        transcription_result = future2.result()

        # Process scenes with the transcription
        scenes_result = process_scenes(config.VIDEO_PATH, config.IMAGE_DIR, transcription_result)
        
        # Generate summary after all scene processing is complete
        summary = summarize_scenes(scenes_result)

        # Update the video document with the structured summary
        videos_col.update_one(
            {"videoId": config.VIDEO_ID}, 
            {"$set": {"structured_summary": summary}}, 
            upsert=True
        )

    print("Processing completed successfully")

if __name__ == "__main__":
    main()
