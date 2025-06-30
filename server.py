import os
import tempfile
import shutil
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import asyncio
from pathlib import Path

# Import our existing pipeline components
from video_processor.multimodal import generate_summary
from video_processor.config import get_config

app = FastAPI(title="Video Analysis API", version="1.0.0")

class AnalysisType(str, Enum):
    MULTIMODAL = "multimodal"
    SCENE_DETECTION = "scene_detection"
    TRANSCRIPTION = "transcription" 
    OCR = "ocr"
    CAPTIONING = "captioning"
    MATCHING = "matching"
    STRUCTURED_SUMMARY = "structured_summary"
    FULL_PIPELINE = "full_pipeline"

class AnalysisRequest(BaseModel):
    analyses: List[AnalysisType] = Field(default=[AnalysisType.MULTIMODAL])
    config: Optional[Dict[str, Any]] = Field(default=None)

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

# Store for tracking analysis jobs
analysis_jobs: Dict[str, Dict] = {}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    video: UploadFile = File(..., description="Video file to analyze"),
    analyses: str = Form(..., description="Comma-separated list of analysis types"),
    config: Optional[str] = Form(None, description="JSON config string")
):
    """
    Analyze uploaded video file with specified analysis types
    """
    # Validate file type
    if not video.content_type or not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Parse analysis types
    try:
        analysis_list = [AnalysisType(a.strip()) for a in analyses.split(",")]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid analysis type: {e}")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create temporary directory for this job
    temp_dir = Path(tempfile.mkdtemp(prefix=f"video_analysis_{job_id}_"))
    video_path = temp_dir / video.filename
    
    try:
        # Save uploaded video
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        # Initialize job tracking
        analysis_jobs[job_id] = {
            "status": "processing",
            "temp_dir": temp_dir,
            "video_path": video_path,
            "analyses": analysis_list,
            "results": {},
            "error": None
        }
        
        # Start async processing
        asyncio.create_task(process_video_analysis(job_id))
        
        return AnalysisResponse(
            job_id=job_id,
            status="processing",
            results=None
        )
        
    except Exception as e:
        # Cleanup on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.get("/analyze/{job_id}", response_model=AnalysisResponse)
async def get_analysis_status(job_id: str):
    """
    Get status and results of analysis job
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    return AnalysisResponse(
        job_id=job_id,
        status=job["status"],
        results=job["results"] if job["status"] == "completed" else None,
        error=job["error"]
    )

async def process_video_analysis(job_id: str):
    """
    Process video analysis in background
    """
    job = analysis_jobs[job_id]
    
    try:
        video_path = job["video_path"]
        analysis_types = job["analyses"]
        results = {}
        
        # Process each requested analysis type
        for analysis_type in analysis_types:
            if analysis_type == AnalysisType.MULTIMODAL:
                # For now, we'll use a mock result since we need TwelveLabs video upload
                results["multimodal"] = await process_multimodal_analysis(str(video_path))
            else:
                # Placeholder for other analysis types
                results[analysis_type.value] = {"status": "not_implemented"}
        
        # Update job with results
        job["status"] = "completed"
        job["results"] = results
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
    
    finally:
        # Cleanup temporary files after some delay
        asyncio.create_task(cleanup_job_files(job_id, delay=3600))  # 1 hour delay

async def process_multimodal_analysis(video_path: str) -> Dict:
    """
    Process multimodal analysis
    Note: This is a placeholder - actual implementation would need to upload video to TwelveLabs first
    """
    try:
        config = get_config()
        
        # TODO: Upload video to TwelveLabs and get video_id
        # For now, return mock data
        return {
            "status": "mock_result",
            "message": "Multimodal analysis requires TwelveLabs video upload integration",
            "video_path": video_path
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

async def cleanup_job_files(job_id: str, delay: int = 3600):
    """
    Clean up temporary files after delay
    """
    await asyncio.sleep(delay)
    
    if job_id in analysis_jobs:
        job = analysis_jobs[job_id]
        temp_dir = job.get("temp_dir")
        
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        # Remove job from tracking
        del analysis_jobs[job_id]

@app.delete("/analyze/{job_id}")
async def cancel_analysis(job_id: str):
    """
    Cancel analysis job and cleanup files
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    temp_dir = job.get("temp_dir")
    
    if temp_dir and temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    del analysis_jobs[job_id]
    
    return {"message": "Job cancelled and files cleaned up"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    """
    Root endpoint with API info
    """
    return {
        "message": "Video Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Upload video and start analysis",
            "GET /analyze/{job_id}": "Get analysis status and results",
            "DELETE /analyze/{job_id}": "Cancel analysis job",
            "GET /health": "Health check"
        },
        "supported_analyses": [analysis.value for analysis in AnalysisType]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)