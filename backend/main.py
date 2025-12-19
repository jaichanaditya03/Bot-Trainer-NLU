
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, project_routes, dataset_routes, password_reset_routes, annotation_routes
from routes import nlu_routes, workspace_routes, train_routes, active_learning_routes, admin_routes, feedback_routes
from routes.evaluation_routes import router as evaluation_router

# Initialize FastAPI application
app = FastAPI(title="Bot Trainer Backend")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth_routes.router, tags=["Authentication"])
app.include_router(project_routes.router, tags=["Projects"])
app.include_router(dataset_routes.router, tags=["Datasets"])
app.include_router(password_reset_routes.router, tags=["Password Reset"])
app.include_router(annotation_routes.router, tags=["Annotations"])
app.include_router(nlu_routes.router, tags=["NLU"])
app.include_router(workspace_routes.router, tags=["Workspaces"])
app.include_router(train_routes.router, tags=["Training"])
app.include_router(active_learning_routes.router)
app.include_router(evaluation_router)
app.include_router(admin_routes.router)
app.include_router(feedback_routes.router)


# Health check endpoint
@app.get("/", tags=["Health"])
def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "message": "Bot Trainer Backend API is running",
        "version": "1.0.0"
    }
