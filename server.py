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

# Import our modular pipeline
from video_processor.pipeline import run_analysis, get_supported_analysis_types, get_analysis_descriptions

app = FastAPI(title="Video Analysis API", version="1.0.0")

class AnalysisType(str, Enum):
    MULTIMODAL = "multimodal"
    STRUCTURED = "structured"

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
    # Validate file type - check both content type and file extension
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    file_extension = Path(video.filename).suffix.lower() if video.filename else ""
    
    is_video_content_type = video.content_type and video.content_type.startswith("video/")
    is_video_extension = file_extension in video_extensions
    
    if not (is_video_content_type or is_video_extension):
        raise HTTPException(status_code=400, detail=f"File must be a video. Got content_type: {video.content_type}, extension: {file_extension}")
    
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
        video_path = str(job["video_path"])
        analysis_types = [analysis.value for analysis in job["analyses"]]
        
        # Run analysis in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, 
            run_analysis, 
            video_path, 
            analysis_types, 
            None  # twelvelabs_video_id
        )
        
        # Update job with results
        job["status"] = "completed"
        job["results"] = results
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
    
    finally:
        # Cleanup temporary files after some delay
        asyncio.create_task(cleanup_job_files(job_id, delay=3600))  # 1 hour delay


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
        "supported_analyses": get_supported_analysis_types(),
        "analysis_descriptions": get_analysis_descriptions()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)