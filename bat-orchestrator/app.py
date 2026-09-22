import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .config import HOST, PORT, STATIC_DIR
from .database import get_db, init_db
from .models import Worker, Execution
from .services.telemetry_service import record_heartbeat, ingest_execution_log
from .services.ai_summarizer import analyze_failure

from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("batautomate.orchestrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized successfully.")
    yield


# Ensure tables exist immediately on import
init_db()

app = FastAPI(
    title="BatAutomate Central Orchestrator & AI Dashboard",
    version="1.0.0",
    description="Central control hub, telemetry receiver, and AI-powered failure summarizer for BatAutomate Edge Workers.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class HeartbeatRequest(BaseModel):
    worker_id: str
    name: str = "Worker"
    ip_address: str = "127.0.0.1"
    os_info: str = "Linux"
    cpu_percent: float = 0.0
    ram_usage: str = "0.0 GB"
    current_task: Optional[str] = None


class TelemetryRequest(BaseModel):
    worker_id: str = "local-worker"
    payload: Dict[str, Any]


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/api/v1/healthz")
def health_check():
    return {"status": "healthy", "service": "BatAutomate Central Orchestrator"}


@app.post("/api/v1/heartbeat")
def heartbeat(req: HeartbeatRequest, db: Session = Depends(get_db)):
    worker = record_heartbeat(
        db=db,
        worker_id=req.worker_id,
        name=req.name,
        ip_address=req.ip_address,
        os_info=req.os_info,
        cpu_percent=req.cpu_percent,
        ram_usage=req.ram_usage,
        current_task=req.current_task
    )
    return {"status": "ok", "worker": worker.to_dict()}


@app.get("/api/v1/workers")
def list_workers(db: Session = Depends(get_db)):
    workers = db.query(Worker).all()
    return {"workers": [w.to_dict() for w in workers]}


@app.post("/api/v1/telemetry")
def receive_telemetry(req: TelemetryRequest, db: Session = Depends(get_db)):
    execution = ingest_execution_log(
        db=db,
        payload=req.payload,
        worker_id=req.worker_id
    )
    return {
        "status": "recorded",
        "execution_id": execution.id,
        "flow_name": execution.flow_name,
        "has_error": execution.has_error,
        "ai_summary": execution.ai_summary
    }


@app.get("/api/v1/executions")
def list_executions(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Execution).order_by(Execution.created_at.desc())
    if status:
        query = query.filter(Execution.status == status)
    items = query.limit(limit).all()
    return {"executions": [e.to_dict() for e in items]}


@app.get("/api/v1/executions/{execution_id}")
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution.to_dict()


@app.post("/api/v1/executions/{execution_id}/reanalyze")
def reanalyze_execution(execution_id: str, db: Session = Depends(get_db)):
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    ai_res = analyze_failure(
        flow_name=execution.flow_name,
        failed_step_name=execution.failed_step_name,
        error_message=execution.error_message,
        exception_class=execution.exception_class
    )
    execution.ai_category = ai_res.get("category")
    execution.ai_confidence = ai_res.get("confidence")
    execution.ai_summary = ai_res.get("summary")
    execution.ai_root_cause = ai_res.get("root_cause")
    execution.ai_suggestion = ai_res.get("suggestion")

    db.commit()
    db.refresh(execution)
    return {"status": "reanalyzed", "execution": execution.to_dict()}


# ---------------------------------------------------------
# Web Dashboard Frontend
# ---------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_dashboard():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "BatAutomate Orchestrator Running. Dashboard UI file not found in static/."}


def start_server():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    start_server()
