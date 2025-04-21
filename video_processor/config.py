import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    VIDEO_PATH: str
    VIDEO_ID: str
    IMAGE_DIR: str
    MONGODB_URI: str
    MONGODB_DB: str
    OPENAI_API_KEY: str = None
    TWELVE_LABS_API_KEY: str = None

def get_config():
    """Load configuration from environment variables or defaults"""
    
    load_dotenv(override=True)
    
    # You can expand this to load from a config file or environment variables
    config = Config(
        VIDEO_PATH=os.environ.get("VIDEO_PATH", "./reels/3505607525892794154_5599290503.mp4"),
        VIDEO_ID=os.environ.get("VIDEO_ID", "3505607525892794154_5599290503.mp4"),
        IMAGE_DIR=os.environ.get("IMAGE_DIR", "./scenes"),
        MONGODB_URI=os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
        MONGODB_DB=os.environ.get("MONGODB_DB", "creator-kb"),
        OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY"),
        TWELVE_LABS_API_KEY=os.environ.get("TWELVE_LABS_API_KEY"),
    )
    
    return config 