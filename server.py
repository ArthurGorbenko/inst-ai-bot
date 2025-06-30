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
import logging
from pathlib import Path

# Import our modular pipeline
from video_processor.pipeline import run_analysis, get_supported_analysis_types, get_analysis_descriptions
from video_processor.config import get_config
from video_processor.db import DatabaseConnection, JobManager, ResultsManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Analysis API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global job_manager, results_manager
    
    if not db_connection.connect():
        logger.error("Failed to connect to MongoDB - server cannot start")
        raise RuntimeError("MongoDB connection required for server operation")
    
    job_manager = JobManager(db_connection)
    results_manager = ResultsManager(db_connection)
    logger.info("MongoDB connection established - server ready")
        
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connection on shutdown"""
    if db_connection:
        db_connection.close()

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

# Initialize database connection and managers
config = get_config()
db_connection = DatabaseConnection(config)
job_manager = None
results_manager = None

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
        job_data = {
            "job_id": job_id,
            "video_filename": video.filename,
            "video_size": video.size if hasattr(video, 'size') else 0,
            "video_content_type": video.content_type or "",
            "temp_dir": str(temp_dir),
            "video_path": str(video_path),
            "analyses": [a.value for a in analysis_list]
        }
        
        if not job_manager.create_job(job_data):
            # Cleanup and raise error if job creation fails
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail="Failed to create job - database error")
        
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
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results = None
    if job["status"] == "completed":
        results_list = results_manager.get_results(job_id)
        if results_list:
            results = {}
            for result in results_list:
                results[result["analysis_type"]] = result["results"]
    
    return AnalysisResponse(
        job_id=job_id,
        status=job["status"],
        results=results,
        error=job.get("error")
    )

async def process_video_analysis(job_id: str):
    """
    Process video analysis in background
    """
    job_data = job_manager.get_job(job_id)
    if not job_data:
        logger.error(f"Job {job_id} not found in database")
        return
    
    job = {
        "video_path": job_data["video_path"],
        "analyses": job_data["analyses"]
    }
    
    try:
        video_path = str(job["video_path"])
        # Handle both string arrays and AnalysisType enum arrays
        if isinstance(job["analyses"][0], str):
            analysis_types = job["analyses"]
        else:
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
        job_manager.update_job_status(job_id, "completed")
        # Store results separately for each analysis type
        for analysis_type, result_data in results.items():
            results_manager.store_results(job_id, analysis_type, result_data, 0.0)  # TODO: track actual processing time
        
    except Exception as e:
        error_msg = str(e)
        job_manager.update_job_status(job_id, "failed", error_msg)
    
    finally:
        # Cleanup temporary files after some delay
        asyncio.create_task(cleanup_job_files(job_id, delay=3600))  # 1 hour delay


async def cleanup_job_files(job_id: str, delay: int = 3600):
    """
    Clean up temporary files after delay
    """
    await asyncio.sleep(delay)
    
    job = job_manager.get_job(job_id)
    if job:
        temp_dir = job.get("temp_dir")
        if temp_dir:
            temp_dir_path = Path(temp_dir) if isinstance(temp_dir, str) else temp_dir
            if temp_dir_path.exists():
                shutil.rmtree(temp_dir_path)

@app.delete("/analyze/{job_id}")
async def cancel_analysis(job_id: str):
    """
    Cancel analysis job and cleanup files
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete from MongoDB
    job_manager.delete_job(job_id)
    results_manager.delete_results(job_id)
    
    # Cleanup temp files
    temp_dir = job.get("temp_dir")
    if temp_dir:
        temp_dir_path = Path(temp_dir) if isinstance(temp_dir, str) else temp_dir
        if temp_dir_path.exists():
            shutil.rmtree(temp_dir_path)
    
    return {"message": "Job cancelled and files cleaned up"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "mongodb": "connected",
        "storage": "mongodb"
    }

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