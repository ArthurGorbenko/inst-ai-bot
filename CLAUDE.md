# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a video processing system that analyzes video content using computer vision and AI. The system processes video files to extract scenes, perform OCR, generate captions, and create structured summaries using multimodal AI.

## Key Commands

### Python Environment
- `source venv/bin/activate` - Activate virtual environment
- `pip install -r requirements.txt` - Install Python dependencies
- `python main.py` - Run the main video processing pipeline (legacy)

### HTTP Server (Primary Interface)
- `python -m fastapi dev server.py` - Start development server on localhost:8000
- `python -m fastapi run server.py` - Start production server
- `python test_server.py` - Run server integration tests

### Node.js (minimal usage)
- `npm install` - Install Node.js dependencies (minimal usage)

## Architecture

### HTTP API Server (`server.py`)
FastAPI-based REST server that provides modular video analysis via HTTP endpoints:
- **POST /analyze** - Upload video and request specific analysis types
- **GET /analyze/{job_id}** - Check analysis status and retrieve results
- **DELETE /analyze/{job_id}** - Cancel analysis and cleanup files
- **GET /health** - Server health check
- **GET /** - API documentation and supported analysis types

### Analysis Types
- `multimodal` - Comprehensive analysis using TwelveLabs API
- `scene_detection` - Extract key frames and timestamps
- `transcription` - Audio-to-text using Whisper
- `ocr` - Text extraction from scenes
- `captioning` - AI-powered scene descriptions
- `matching` - Align transcription with visual scenes
- `structured_summary` - Generate searchable summaries
- `full_pipeline` - Complete processing pipeline

### Core Processing Pipeline (`main.py` - Legacy)
The original pipeline orchestrates video processing through these steps:
1. Scene detection and extraction (`scene_detect.py`)
2. OCR processing on extracted frames (`ocr.py`) 
3. AI-powered scene description generation (`captioning.py`)
4. Audio transcription extraction (`transcription.py`)
5. Matching transcriptions to visual scenes (`matching.py`)
6. Structured summarization (`summarizer.py`)
7. Multimodal AI summary generation (`multimodal.py`)

### Video Processor Module (`video_processor/`)
- `config.py` - Configuration management using dataclasses and environment variables
- `db.py` - MongoDB connection and operations
- `scene_detect.py` - Video scene detection and frame extraction
- `ocr.py` - OCR processing using EasyOCR/PaddleOCR
- `captioning.py` - AI-powered scene description generation
- `transcription.py` - Audio transcription using Whisper
- `matching.py` - Matches transcription timestamps to visual scenes
- `summarizer.py` - Creates structured summaries from processed scenes
- `multimodal.py` - Generates comprehensive summaries using TwelveLabs API

### Data Flow
- Videos stored in `reels/` directory
- Extracted scene images saved to `scenes/` directory  
- Scene data and summaries stored in MongoDB database
- Prompts for AI processing stored in `prompts/` directory

### Configuration
Environment variables are loaded via `.env` file:
- `VIDEO_PATH` - Path to video file to process
- `VIDEO_ID` - Unique identifier for video
- `IMAGE_DIR` - Directory for extracted scene images
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DB` - MongoDB database name
- `OPENAI_API_KEY` - OpenAI API key for AI processing
- `TWELVE_LABS_API_KEY` - TwelveLabs API key for multimodal processing

### Key Dependencies
- **FastAPI** - HTTP server framework with automatic API documentation
- **Uvicorn** - ASGI server for running FastAPI applications
- OpenCV for video processing
- EasyOCR/PaddleOCR for text extraction
- OpenAI for AI-powered descriptions
- TwelveLabs for multimodal video analysis
- MongoDB for data persistence
- PySceneDetect for scene boundary detection

### Development Workflow
1. Start server: `source venv/bin/activate && python -m fastapi dev server.py`
2. Access API docs: `http://localhost:8000/docs` (Swagger UI)
3. Test endpoints: Use `test_server.py` or curl commands
4. Upload videos via POST to `/analyze` with analysis type specification

## Code Style Guidelines

### Core Principles
- **KISS (Keep It Stupid Simple)** - Prioritize simplicity and clarity over clever solutions
- **DRY (Don't Repeat Yourself)** - Extract common functionality into reusable functions/modules
- **Single Responsibility Principle** - Each function/class should have one clear purpose
- **Explicit is better than implicit** - Code should be self-documenting and clear

### Python Style
- Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Prefer descriptive variable names over comments
- Use dataclasses for configuration and data structures
- Handle errors explicitly with try/except blocks

### Architecture Guidelines
- Keep modules focused and cohesive
- Use dependency injection for external services (database, APIs)
- Separate business logic from HTTP/API concerns
- Prefer composition over inheritance
- Write testable code with clear interfaces

### Error Handling
- Use specific exception types rather than generic Exception
- Log errors with sufficient context for debugging
- Fail fast and provide clear error messages
- Implement graceful degradation where appropriate