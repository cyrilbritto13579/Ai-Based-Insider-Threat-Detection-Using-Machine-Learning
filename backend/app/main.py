"""
FastAPI Application Entry Point
===============================
Main application module for Explainable Insider Threat Detection V2.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.db.models import User
from app.simulation.enterprise import seed_synthetic_enterprise
from app.api.routes import api_router
from app.services.pipeline_service import pipeline_service
from app.simulation.manager import simulation_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # 1. Initialize DB tables
    init_db()

    # 2. Seed missing synthetic users and reconcile the initial risk-profile migration.
    db = SessionLocal()
    try:
        seed_synthetic_enterprise(db)
    finally:
        db.close()

    print(f"Backend started: {settings.PROJECT_NAME} v{settings.VERSION}")
    yield
    # Shutdown
    await simulation_manager.stop()
    print("Backend shutdown cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Explainable AI-Based Insider Threat Detection with Dynamic Risk Scoring Using Machine Learning",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router)  # Also include at root for convenient client access


# WebSocket live stream at root /ws/live
@app.websocket("/ws/live")
async def websocket_root_endpoint(websocket: WebSocket):
    await websocket.accept()
    pipeline_service.register_websocket(websocket)
    try:
        from datetime import datetime
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "simulation": simulation_manager.get_status(),
            "timestamp": datetime.utcnow().isoformat(),
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pipeline_service.unregister_websocket(websocket)
    except Exception:
        pipeline_service.unregister_websocket(websocket)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "simulation_disclaimer": "SIMULATION DATA — NOT REAL COMPANY DATA",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
