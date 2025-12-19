
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
projects_col = db["projects"]
dataset_sentences_col = db["dataset_sentences"] 
datasets_col = db["datasets"] 
annotations_col = db["annotations"]  
workspaces_col = db["workspaces"]  # workspaces per user
feedback_col = db["feedback"]  # user feedback on model predictions
active_learning_corrections_col = db["active_learning_corrections"]  # corrected training data from active learning

# Suggested indexes (idempotent ensure) - safe to call at import time
try:
	workspaces_col.create_index("owner_email")
	datasets_col.create_index([("workspace_id", 1), ("checksum", 1)])
	# Compound index for efficient workspace-specific feedback queries
	feedback_col.create_index([("owner_email", 1), ("workspace_id", 1), ("created_at", -1)])
except Exception:
	# Non-fatal if index creation fails (e.g., limited permissions)
	pass
