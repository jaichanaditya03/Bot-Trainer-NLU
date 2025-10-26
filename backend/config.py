"""
Configuration settings for the backend application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bot_trainer")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "mysecretkey123")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = 12
