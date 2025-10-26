"""
MongoDB database connection and collections
"""
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
projects_col = db["projects"]
datasets_col = db["datasets"]
