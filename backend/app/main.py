from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.database import init_db
from app.routes.interactions import router as interactions_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="HCP CRM API",
    description="AI-First CRM for Healthcare Professional Interactions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "HCP CRM API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
