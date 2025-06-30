import os
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .config import get_config
from .db import get_mongodb_connection
from .scene_detect import detect_and_save_scenes
from .ocr import get_captions
from .captioning import generate_scene_description
from .transcription import extract_transcription
from .matching import match_transcription_to_scenes
from .summarizer import summarize_scenes
from .multimodal import generate_summary


def analyze_multimodal(video_path: str, video_id: str) -> Dict[str, Any]:
    """
    Analyze video using TwelveLabs multimodal API.
    
    Args:
        video_path: Path to video file
        video_id: TwelveLabs video ID for the uploaded video
        
    Returns:
        Dict containing multimodal analysis results
    """
    config = get_config()
    
    try:
        # Generate multimodal summary using TwelveLabs
        summary_result = generate_summary(config.TWELVE_LABS_API_KEY, video_id)
        
        return {
            "analysis_type": "multimodal",
            "status": "completed",
            "results": {
                "summary": summary_result.summary if summary_result else None
            }
        }
    except Exception as e:
        return {
            "analysis_type": "multimodal", 
            "status": "error",
            "error": str(e)
        }


def analyze_structured(video_path: str) -> Dict[str, Any]:
    """
    Analyze video using complete structured pipeline.
    Runs: scene detection → OCR → captioning → transcription → matching → summarization
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dict containing structured analysis results
    """
    config = get_config()
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(config.IMAGE_DIR, exist_ok=True)
        
        # Run transcription and scene processing in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Start transcription extraction
            transcription_future = executor.submit(extract_transcription, video_path)
            
            # Start scene detection and processing
            scene_future = executor.submit(_process_scenes_structured, video_path, config.IMAGE_DIR)
            
            # Get results
            transcription_result = transcription_future.result()
            scenes_result = scene_future.result()
        
        # Match transcription to scenes
        if transcription_result:
            scenes_result = match_transcription_to_scenes(scenes_result, transcription_result)
        
        # Generate structured summary
        summary = summarize_scenes(scenes_result)
        
        return {
            "analysis_type": "structured",
            "status": "completed", 
            "results": {
                "scenes": scenes_result,
                "transcription": transcription_result,
                "structured_summary": summary
            }
        }
        
    except Exception as e:
        return {
            "analysis_type": "structured",
            "status": "error", 
            "error": str(e)
        }


def _process_scenes_structured(video_path: str, images_dir: str) -> list:
    """
    Internal function to process scenes for structured analysis.
    """
    # Detect scenes and save frames
    scene_timestamps = detect_and_save_scenes(video_path)
    
    # Extract text from scenes using OCR
    scenes = get_captions(images_dir, scene_timestamps)
    
    # Generate AI descriptions for scenes
    scenes = generate_scene_description(images_dir, scenes)
    
    return scenes