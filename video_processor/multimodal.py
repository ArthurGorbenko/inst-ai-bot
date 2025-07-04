from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task
import time
import os
import logging
from typing import Dict, Any, Optional, Tuple
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
import json

logger = logging.getLogger(__name__)

prompt="""
Analyze an Instagram reel from a tech blogger influencer and provide a Comprehensive Description. Include the following details: Describe the reel's purpose, main topics, and target audience, explaining what it communicates and its context in the tech niche. Detail the visual elements, including the setting, objects, gadgets, and notable effects or transitions. Summarize the spoken content or dialogues, highlighting key phrases, quotes, and points emphasized by the influencer. Explain the narrative flow, describing how the content progresses from start to finish, including the opening, main segments, and conclusion. Identify and describe any calls to action, such as encouraging viewers to like, comment, follow, or click links. Analyze the influencer's persona, including tone, style, personality traits, and engagement with their audience. Output the results in the following JSON format: {"content_overview": "Description of the reel's purpose, topics, and target audience.","key_visual_elements": "Details of setting, objects, effects, and transitions.","spoken_content_and_dialogues": "Summary of spoken content with key phrases or quotes.","narrative_flow": "How the reel's content progresses.","calls_to_action": "Details on any calls to action.","influencer_persona": "Analysis of the influencer's tone, style, and engagement."} Ensure the JSON is valid, contains no formatting or new line characters, and includes as much detail as possible for each field.
"""

def generate_summary(api_key, video_id):
    logger.info("Generating summary for video: " + video_id)
    client = TwelveLabs(api_key=api_key)
    res = None
    try:
        res = client.generate.text(video_id=video_id, prompt=prompt, temperature=0.7)
        logger.info(f"Summary generation completed. Result type: {type(res)}")
        if res:
            # Log available attributes for debugging
            logger.info(f"Available attributes: {[attr for attr in dir(res) if not attr.startswith('_')]}")
    except Exception as e:
        logger.error(f"Error happened in generate_summary: {e}")
        
    return res


def extract_summary_text(summary_result) -> str:
    """
    Safely extract summary text from TwelveLabs result object.
    
    Args:
        summary_result: TwelveLabs generate result object
        
    Returns:
        Summary text as string
    """
    if not summary_result:
        return None
    
    # Try different possible attributes
    for attr in ['data', 'text', 'content', 'summary']:
        if hasattr(summary_result, attr):
            value = getattr(summary_result, attr)
            if value:
                return str(value)
    
    # Fallback to string representation
    return str(summary_result)


def create_or_get_index(api_key: str, index_name: str = "default-index", index_id: str = None) -> Tuple[str, bool]:
    """
    Create a new index or get existing index for TwelveLabs.
    
    Args:
        api_key: TwelveLabs API key
        index_name: Name for the index (used when creating new)
        index_id: Existing index ID to use (if provided, skips creation)
        
    Returns:
        Tuple of (index_id, was_created)
    """
    client = TwelveLabs(api_key=api_key)
    
    # If index_id is provided, use it directly
    if index_id:
        try:
            index = client.index.retrieve(index_id)
            logger.info(f"Using existing index: {index_id}")
            return index_id, False
        except Exception as e:
            logger.error(f"Failed to retrieve existing index {index_id}: {e}")
            raise
    
    # Create new index with both models
    try:
        index = client.index.create(
            name=index_name,
            engines=[
                {
                    "name": "marengo2.7",
                    "options": ["visual", "conversation", "text_in_video", "logo"]
                },
                {
                    "name": "pegasus1.2",
                    "options": ["visual", "conversation"]
                }
            ],
            addons=["thumbnail"]
        )
        logger.info(f"Created new index: {index.id}")
        return index.id, True
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        raise


def upload_video_for_indexing(api_key: str, video_path: str, index_id: str, max_retries: int = 3) -> str:
    """
    Upload video to TwelveLabs for indexing with retry logic.
    
    Args:
        api_key: TwelveLabs API key
        video_path: Path to video file
        index_id: TwelveLabs index ID
        max_retries: Maximum number of retry attempts
        
    Returns:
        Task ID for indexing operation
    """
    client = TwelveLabs(api_key=api_key)
    
    # Validate video file exists and size
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    file_size = os.path.getsize(video_path)
    if file_size == 0:
        raise ValueError(f"Video file is empty: {video_path}")
    
    # Size limit check (TwelveLabs has file size limits)
    max_size_mb = 5000  # 5GB limit
    if file_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"Video file too large: {file_size / (1024*1024):.1f}MB > {max_size_mb}MB")
    
    # Retry logic for upload
    for attempt in range(max_retries):
        try:
            logger.info(f"Uploading video (attempt {attempt + 1}/{max_retries}): {video_path}")
            logger.info(f"File size: {file_size / (1024*1024):.1f}MB")
            logger.info(f"Using index ID: {index_id}")
            
            
            task = client.task.create(
                index_id=index_id,
                file=video_path
            )
            
            logger.info(f"Started video upload task: {task.id}")
            return task.id
            
        except (ConnectionError, Timeout, RequestException) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Network error uploading video (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Failed to upload video after {max_retries} attempts: {e}")
                raise
        except ValueError as e:
            # Don't retry for API key validation errors
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            # Handle API-specific errors (rate limits, quota exceeded, etc.)
            error_str = str(e).lower()
            if "rate limit" in error_str:
                if attempt < max_retries - 1:
                    wait_time = 60  # Wait 1 minute for rate limit
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts: {e}")
                    raise
            elif "unauthorized" in error_str or "authentication" in error_str:
                logger.error(f"Authentication error: {e}")
                raise ValueError(f"TwelveLabs API authentication failed: {e}")
            elif "not found" in error_str and "index" in error_str:
                logger.error(f"Index not found: {e}")
                raise ValueError(f"TwelveLabs index not found: {index_id}. Error: {e}")
            else:
                logger.error(f"Failed to upload video {video_path}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise


def wait_for_indexing_completion(api_key: str, task_id: str, job_manager=None, job_id: str = None, timeout: int = 1800, poll_interval: int = 10) -> Tuple[bool, str]:
    """
    Wait for indexing task to complete with exponential backoff.
    
    Args:
        api_key: TwelveLabs API key
        task_id: Task ID from upload
        timeout: Maximum time to wait in seconds (default: 30 minutes)
        poll_interval: Initial polling interval in seconds
        
    Returns:
        Tuple of (success, video_id_or_error)
    """
    client = TwelveLabs(api_key=api_key)
    
    start_time = time.time()
    current_interval = poll_interval
    
    while (time.time() - start_time) < timeout:
        try:
            task = client.task.retrieve(task_id)
            
            if task.status == "ready":
                logger.info(f"Indexing completed successfully: {task.video_id}")
                # Update job status
                if job_manager and job_id:
                    job_manager.update_twelve_labs_metadata(
                        job_id=job_id,
                        video_id=task.video_id,
                        indexing_status="ready"
                    )
                return True, task.video_id
            elif task.status == "failed":
                error_msg = f"Indexing failed: {getattr(task, 'error', 'Unknown error')}"
                logger.error(error_msg)
                # Update job status
                if job_manager and job_id:
                    job_manager.update_twelve_labs_metadata(
                        job_id=job_id,
                        indexing_status="failed"
                    )
                return False, error_msg
            elif task.status in ["pending", "validating", "running"]:
                logger.info(f"Indexing in progress... Status: {task.status}")
                # Update job status with progress
                if job_manager and job_id:
                    job_manager.update_twelve_labs_metadata(
                        job_id=job_id,
                        indexing_status=task.status
                    )
                time.sleep(current_interval)
                # Exponential backoff with max 60 seconds
                current_interval = min(current_interval * 1.5, 60)
            else:
                logger.warning(f"Unknown task status: {task.status}")
                time.sleep(current_interval)
                
        except (ConnectionError, Timeout, RequestException) as e:
            logger.warning(f"Network error checking task status: {e}")
            time.sleep(current_interval)
        except Exception as e:
            if "rate limit" in str(e).lower():
                logger.warning(f"Rate limit checking task status: {e}")
                time.sleep(60)  # Wait 1 minute for rate limit
            else:
                logger.error(f"Error checking task status: {e}")
                time.sleep(current_interval)
    
    error_msg = f"Indexing timeout after {timeout} seconds"
    logger.error(error_msg)
    return False, error_msg


def get_video_analysis(api_key: str, video_path: str, index_id: str = None, index_name: str = "default-index", job_manager=None, job_id: str = None) -> Dict[str, Any]:
    """
    Comprehensive function that handles the complete workflow:
    upload → index → generate summary
    
    Args:
        api_key: TwelveLabs API key
        video_path: Path to video file
        index_id: Existing index ID (if None, creates new index)
        index_name: Name for new index (used if index_id is None)
        
    Returns:
        Dict containing analysis results and metadata
    """
    try:
        # Step 1: Get or create index
        logger.info("Getting or creating index...")
        final_index_id, was_created = create_or_get_index(api_key, index_name, index_id)
        
        # Update job with index info
        if job_manager and job_id:
            job_manager.update_twelve_labs_metadata(
                job_id=job_id,
                index_id=final_index_id,
                indexing_status="uploading"
            )
        
        # Step 2: Upload video for indexing
        logger.info("Uploading video for indexing...")
        task_id = upload_video_for_indexing(api_key, video_path, final_index_id)
        
        # Update job with task info
        if job_manager and job_id:
            job_manager.update_twelve_labs_metadata(
                job_id=job_id,
                task_id=task_id,
                indexing_status="pending"
            )
        
        # Step 3: Wait for indexing completion
        logger.info("Waiting for indexing completion...")
        success, video_id_or_error = wait_for_indexing_completion(api_key, task_id, job_manager, job_id)
        
        if not success:
            return {
                "status": "failed",
                "error": video_id_or_error,
                "index_id": final_index_id,
                "task_id": task_id
            }
        
        video_id = video_id_or_error
        
        # Step 4: Generate summary
        logger.info("Generating summary...")
        summary_result = generate_summary(api_key, video_id)
        
        return {
            "status": "completed",
            "video_id": video_id,
            "index_id": final_index_id,
            "task_id": task_id,
            "index_was_created": was_created,
            "summary": extract_summary_text(summary_result)
        }
        
    except Exception as e:
        logger.error(f"Error in get_video_analysis: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    
    