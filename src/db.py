from pymongo import MongoClient
from config import Config

client = None
db = None

def get_db():
    """Returns the MongoDB database instance."""
    global client, db
    if db is None:
        try:
            client = MongoClient(Config.MONGO_URI)
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            db = client[Config.MONGO_DB_NAME]
            print("MongoDB connection successful!")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            # Handle connection failure appropriately
            raise e
    return db

def close_db(e=None):
    """Closes the MongoDB connection."""
    global client, db
    if client is not None:
        client.close()
        client = None
        db = None
        print("MongoDB connection closed.")

# Example usage:
# from src.db import get_db
# db = get_db()
# calls_collection = db.calls