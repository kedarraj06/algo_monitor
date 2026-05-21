from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from utils.feature_extractor import extract_features_from_teal
from utils.feature_engineer import engineer_features
from models.inference import predict
from models.predictor import Predictor
from models.suggester import generate_suggestions
from routers.monitoring import router as monitoring_router
from utils.background_tasks import monitoring_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

_monitoring_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background monitoring loop on startup, cancel it on shutdown."""
    global _monitoring_task
    logger.info("[Startup] Starting background monitoring loop...")
    _monitoring_task = asyncio.create_task(monitoring_loop())
    yield
    # Shutdown
    logger.info("[Shutdown] Stopping background monitoring loop...")
    if _monitoring_task and not _monitoring_task.done():
        _monitoring_task.cancel()
        try:
            await _monitoring_task
        except asyncio.CancelledError:
            pass
    logger.info("[Shutdown] Monitoring loop stopped.")

app = FastAPI(
    title="AlgoShieldAI Backend",
    description="Machine learning based security analysis for TEAL smart contracts",
    lifespan=lifespan
)

app.include_router(monitoring_router)

# Add CORS Support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_smart_contract(file: UploadFile = File(...)):
    if not file.filename.endswith('.teal'):
        raise HTTPException(status_code=400, detail="Only .teal files are allowed")
        
    try:
        content_bytes = await file.read()
        content = content_bytes.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
    try:
        # Extract base features
        extracted = extract_features_from_teal(content)
        
        # Add engineered features
        engineered = engineer_features(extracted)
        
        # Predict using the ML model
        prediction_num, prediction_label = predict(engineered)
        
        return {
            "prediction": prediction_num,
            "label": prediction_label,
            "features": engineered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/suggest")
async def suggest_smart_contract(file: UploadFile = File(...)):
    if not file.filename.endswith('.teal'):
        raise HTTPException(status_code=400, detail="Only .teal files are allowed")
        
    try:
        content_bytes = await file.read()
        content = content_bytes.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
    try:
        # Extract features
        extracted = extract_features_from_teal(content)
        engineered = engineer_features(extracted)
        
        # Predict using the Predictor wrapper
        prediction_num, prediction_label = Predictor.predict(engineered)
        
        # Generate suggestions asynchronously via threadpool (Rule-based + RAG SLM)
        import asyncio
        suggestions, score = await asyncio.to_thread(
            generate_suggestions, engineered, content, prediction_label
        )
        
        return {
            "prediction": prediction_num,
            "label": prediction_label,
            "confidence": "High", # ML confidence proxy
            "score": score,
            "features": engineered,
            "suggestions": suggestions
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
