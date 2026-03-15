from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import models
from database import engine, SessionLocal
from api import equipment, maintenance, repairs, notifications, auth, users, stats
import scheduler
import auth_utils

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create the database tables
    models.Base.metadata.create_all(bind=engine)

    # 2. Initialize a default user and seed data if empty
    from seed_data import seed_db
    seed_db()

    # 3. Start background jobs
    scheduler.start_scheduler()
    
    yield
    # Shutdown logic could go here

app = FastAPI(title="Hospital Equipment Maintenance API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(equipment.router, prefix="/api/equipment", tags=["Equipment"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Maintenance"])
app.include_router(repairs.router, prefix="/api/repairs", tags=["Repairs"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])

# Serve static files for the frontend SPA
app.mount("/", StaticFiles(directory="static", html=True), name="static")
