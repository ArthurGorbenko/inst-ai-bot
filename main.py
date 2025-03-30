import os
import subprocess
import whisper

from pymongo import MongoClient
from paddleocr import PaddleOCR
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from scenedetect import open_video, detect, AdaptiveDetector, save_images
from concurrent.futures import ThreadPoolExecutor

path = "./reels/3481080082629109504_5599290503.mp4"
videoID = "3481080082629109504_5599290503"
image_dir = "./scenes"
client = MongoClient('mongodb://localhost:27017/')  # Your MongoDB connection

db = client['creator-kb']
videos_col = db['videos']

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
    
    # Write to MongoDB only once at the end
    print(f"Updating MongoDB with final scenes data: {scenes}")
    videos_col.update_one(
        {"videoId": videoID},
        {
            "$set": {
                "videoId": videoID,
                "scenes": scenes
            }
        },
        upsert=True
    )
    
    return scenes

def generate_scene_description(images_dir, existing_scenes=None):
    print(f"\n=== Starting generate_scene_description for directory: {images_dir} ===")
    try:
        print("Loading BLIP processor and model...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        
        files = os.listdir(images_dir)
        print(f"Found {len(files)} files in directory")
        scenes = existing_scenes or {}
        
        for f in files:
            # Extract scene info from filename
            scene_info = f.split('--')
            if len(scene_info) >= 4:
                scene_num = scene_info[1]
                frame_num = scene_info[2]
                # Now the 4th segment contains the actual timestamp
                timestamp = scene_info[3].split('.')[0]
                scene_id = f"{scene_num}_{frame_num}"
                
                image_path = os.path.join(images_dir, f)
                print(f"Processing image: {image_path}")
                
                image = Image.open(image_path)
                inputs = processor(image, return_tensors="pt")
                outputs = model.generate(**inputs)
                description = processor.decode(outputs[0], skip_special_tokens=True)
                
                if scene_id not in scenes:
                    scenes[scene_id] = {
                        'descriptions': [],
                        'captions': [],
                        'images': [],
                        'scene_number': scene_num,
                        'frame_number': frame_num,
                        'timestamp': timestamp
                    }
                
                scenes[scene_id]['descriptions'].append(description)
                scenes[scene_id]['images'].append(f)
                print(f"Generated Description for scene {scene_id}: {description}\n")
        
        return scenes
    except Exception as e:
        print(f"Error in generate_scene_description: {str(e)}")

def get_captions(images_path, scene_timestamps):
    print(f"\n=== Starting get_captions for directory: {images_path} ===")
    try:
        files = os.listdir(images_path)
        print(f"Found {len(files)} files in directory")
        
        ocr = PaddleOCR(use_gpu=False, lang="en", show_log=False)
        scenes = {}
        
        for f in files:
            scene_info = f.split('--')
            if len(scene_info) >= 4:
                scene_num = scene_info[1]
                frame_num = scene_info[2]
                # With the updated template, the 4th segment now holds the actual timestamp
                timestamp = scene_info[3].split('.')[0]
                scene_id = f"{scene_num}_{frame_num}"
                
                image_path = os.path.join(images_path, f)
                print(f"Processing image: {image_path}")
                
                if scene_id not in scenes:
                    scenes[scene_id] = {
                        'descriptions': [],
                        'captions': [],
                        'images': [],
                        'scene_number': scene_num,
                        'frame_number': frame_num,
                        'timestamp': timestamp,
                        'frame': frame_num  # Retain the frame number for reference if needed
                    }
                
                # Run PaddleOCR on the image
                results = ocr.ocr(image_path, cls=True)
                
                if results and results[0]:
                    # filter results with less than 0.9 confidence
                    results[0] = [line for line in results[0] if line is not None and line[1][1] >= 0.9]
                    for line in results[0]:
                        if line is not None:
                            text = line[1][0]
                            confidence = line[1][1]
                            scenes[scene_id]['captions'].append({
                                'text': text,
                                'confidence': confidence
                            })
                            print(f"{text} (Confidence: {confidence:.2f})")
                else:
                    print(f"No text detected in image: {image_path}")
            print()
        
        return scenes
    except Exception as e:
        print(f"Error in get_captions: {str(e)}")
        return {}  # Return empty dict instead of None on error

def detect_and_save_scenes(video_path):
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

def match_transcription_to_scenes(scenes, transcription):
    print("\n=== Matching transcriptions to scenes ===")
    
    # Convert scene timestamps to seconds for easier comparison
    scene_times = {}
    for scene_id, scene_data in scenes.items():
        ts = scene_data['timestamp']
        print(f"Processing timestamp: {ts} for scene {scene_id}")
        
        try:
            # Normalize timestamp format (replace semicolons with colons if present)
            ts = ts.replace(';', ':')
            
            # Split timestamp into components
            if ':' in ts:
                parts = ts.split(':')
                if len(parts) == 3:  # HH:MM:SS format
                    h, m, s = parts
                elif len(parts) == 2:  # MM:SS format
                    h, m, s = '0', parts[0], parts[1]
                else:
                    h, m, s = '0', '0', parts[0]
            else:
                h, m, s = '0', '0', ts
            
            # Handle milliseconds if present
            s, ms = s.split('.') if '.' in s else (s, '0')
            total_seconds = int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000
            scene_times[scene_id] = total_seconds
            print(f"Converted to {total_seconds} seconds")
        except Exception as e:
            print(f"Error parsing timestamp {ts} for scene {scene_id}: {str(e)}")
            scene_num = int(scene_data.get('scene_number', '0'))
            scene_times[scene_id] = scene_num * 5  # Assume 5 seconds per scene as fallback
    
    # Sort scenes by timestamp
    sorted_scenes = sorted(scene_times.items(), key=lambda x: x[1])
    
    # Calculate scene duration estimates
    scene_durations = {}
    for i, (scene_id, start_time) in enumerate(sorted_scenes):
        if i < len(sorted_scenes) - 1:
            end_time = sorted_scenes[i + 1][1]
        else:
            # For the last scene, estimate duration based on last transcription
            end_time = max(t['end'] for t in transcription) if transcription else start_time + 5
        scene_durations[scene_id] = (start_time, end_time)
    
    # Clear existing transcriptions
    for scene_id in scenes:
        scenes[scene_id]['transcription'] = []
    
    # Match transcriptions to scenes based on overlap
    for segment in transcription:
        segment_start = segment['start']
        segment_end = segment['end']
        segment_text = segment['text']
        
        # Find all scenes that overlap with this segment
        for scene_id, (scene_start, scene_end) in scene_durations.items():
            # Check if there's any overlap between segment and scene
            if (segment_start <= scene_end and segment_end >= scene_start):
                overlap_start = max(segment_start, scene_start)
                overlap_end = min(segment_end, scene_end)
                overlap_duration = overlap_end - overlap_start
                
                # Only add if there's significant overlap (more than 0.5 seconds)
                if overlap_duration > 0.5:
                    scenes[scene_id]['transcription'].append({
                        'start': segment_start,
                        'end': segment_end,
                        'text': segment_text,
                        'overlap_duration': overlap_duration
                    })
                    print(f"Matched transcription to scene {scene_id} (overlap: {overlap_duration:.2f}s): {segment_text}")
    
    # For scenes without transcription, find the nearest segment
    for scene_id, scene_data in scenes.items():
        if not scene_data['transcription']:
            # Use the parsed timestamp (converted to seconds) for matching
            scene_start = scene_times[scene_id]
            closest_segment = min(transcription, 
                                key=lambda x: abs(x['start'] - scene_start))
            scenes[scene_id]['transcription'].append({
                'start': closest_segment['start'],
                'end': closest_segment['end'],
                'text': closest_segment['text'],
                'note': 'nearest_match'
            })
            print(f"Assigned nearest transcription to scene {scene_id}: {closest_segment['text']}")
    
    return scenes

def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)  # Convert the remaining seconds to integer
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

with ThreadPoolExecutor(max_workers=2) as executor:
    # Run both tasks in parallel
    future2 = executor.submit(extract_transcription, path)
    
    # Get transcription result first
    transcription_result = future2.result()
    
    # Then process scenes with the transcription
    scenes_result = process_scenes(path, image_dir, transcription_result)
    
    # Update MongoDB with transcription
    videos_col.update_one(
        {"videoId": videoID},
        {
            "$set": {
                "transcription": transcription_result
            }
        }
    )

print("finished in parallel")
