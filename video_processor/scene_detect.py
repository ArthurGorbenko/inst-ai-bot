import os
from scenedetect import open_video, detect, AdaptiveDetector, save_images

def detect_and_save_scenes(video_path):
    """Detect scenes in a video and save representative images"""
    print("Saving scene images...")
    output_dir = "./scenes"
    os.makedirs(output_dir, exist_ok=True)

    video = open_video(video_path)
    scene_list = detect(
        video_path,
        AdaptiveDetector(),
    )

    # Save scene timestamps before saving images
    scene_timestamps = {}
    for scene in scene_list:
        # Scene is now a tuple of (start_frame, end_frame)
        start_frame, end_frame = scene
        # Get the frame number and convert to timestamp
        frame_number = start_frame.get_frames()
        timestamp_seconds = start_frame.get_seconds()
        timestamp = seconds_to_timestamp(timestamp_seconds)
        scene_timestamps[frame_number] = timestamp

    # Save images with the actual timestamp in the filename
    save_images(
        scene_list=scene_list,
        video=video,
        num_images=1,
        image_name_template="./scenes/$VIDEO_NAME--$SCENE_NUMBER--$IMAGE_NUMBER--$TIMECODE",
    )

    return scene_timestamps

def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)  # Convert the remaining seconds to integer
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" 