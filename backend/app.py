# backend/app.py
"""
AlgoShield AI — FastAPI Application Entry Point
All scan, certificate, and monitoring routes are handled by their respective routers.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    try:
        from database import create_indexes
        await create_indexes()
        print("[App] MongoDB indexes verified.")
    except Exception as e:
        print(f"[App] Warning: Database initialization skipped or failed: {e}")

    try:
        from monitoring.monitoring_manager import manager
        await manager.start_background_task()
        print("[App] Background monitoring started.")
    except Exception as e:
        print(f"[App] Warning: Background monitoring failed to start: {e}")

    print("[App] AlgoShield AI Backend is ready ✓")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    try:
        from monitoring.monitoring_manager import manager
        await manager.stop_background_task()
        print("[App] Background monitoring stopped.")
    except Exception:
        pass


app = FastAPI(
    title="AlgoShield AI",
    description="AI-powered smart contract security and monitoring platform for Algorand blockchain.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router Registration ────────────────────────────────────────────────────────
from routes.scan import router as scan_router
from routes.monitor import router as monitor_router

app.include_router(scan_router, tags=["Scan & Certificates"])
app.include_router(monitor_router, tags=["Monitoring"])


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    return {"status": "AlgoShield AI running", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app:app", host=host, port=port, reload=True)
