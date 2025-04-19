from pymongo import MongoClient

def get_mongodb_connection(config):
    """Get MongoDB connection and collection"""
    client = MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB]
    videos_col = db["videos"]
    return db, videos_col 