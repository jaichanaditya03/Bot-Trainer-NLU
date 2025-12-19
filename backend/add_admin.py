from pymongo import MongoClient
from datetime import datetime
import bcrypt

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["bot_trainer"]
users = db["users"]

# Admin credentials
username = "front man"
email = "admin@example.com"
password = "admin@123"  

# Hash password
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Insert admin user
users.insert_one({
    "username": username,
    "email": email,
    "password": hashed,
    "is_admin": True,
    "created_at": datetime.utcnow()
})

print(f"✅ Admin user '{username}' created successfully!")
print(f"   Email: {email}")
print(f"   Password: {password}")
print(f"   Admin: True")