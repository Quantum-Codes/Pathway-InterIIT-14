from fastapi import FastAPI
# Load environment variables from .env for local development
from dotenv import load_dotenv
from pathlib import Path

# Attempt to load .env from repository root (one level above `app/`)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base, SessionLocal
from app.routes import (
    user_routes, 
    transaction_routes, 
    dashboard_routes,
    auth_routes,
    compliance_routes,
    # cns_routes,
    export_routes,
    superadmin_routes
)
# from app.services import cns_service

# Import database models to ensure they're registered with Base
from app.models import user, transaction, alert, admin, audit_log, toxicity_history, user_sanction_match, system_metrics, system_health  # , cns_match, settings
# from app.models.case import InvestigationCase, AccountHold

import redis
import os

def create_app() -> FastAPI:
    app = FastAPI(
        title="Intelligent Fraud Detection & KYC API",
        description="Advanced fraud detection and KYC compliance system with CNS integration",
        version="2.0"
    )

    # CORS (adjust origins as needed for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routers
    app.include_router(auth_routes.router)  # Auth routes first
    app.include_router(user_routes.router)
    app.include_router(user_routes.users_router)  # /users endpoint for frontend compatibility
    app.include_router(transaction_routes.router)
    app.include_router(dashboard_routes.router)
    app.include_router(compliance_routes.router)  # Compliance alerts
    # app.include_router(cns_routes.router)
    app.include_router(export_routes.router)
    app.include_router(superadmin_routes.router)  # Superadmin routes

    @app.on_event("startup")
    def on_startup():
        # Create DB tables
        Base.metadata.create_all(bind=engine)
        
        # Seed sample CNS data
        # db = SessionLocal()
        # try:
        #     cns_service.seed_sample_cns_data(db)
        # finally:
        #     db.close()

    return app


app = create_app()
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)

@app.get("/")
def read_root():
    return {"message": "Intelligent Fraud Detection & KYC API", "status": "running", "version": "2.0"}
