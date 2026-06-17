from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Dict, Any
import json
from datetime import datetime
import uuid

from .config import settings
from .models import ViolationEvent, SeverityLevel
from .database import Database
from .detection_engine import DetectionEngine
from .severity_classifier import SeverityClassifier
from .escalation_pipeline import EscalationPipeline
from .report_generator import ReportGenerator

app = FastAPI(title="Factory Compliance System")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = Database()
detection_engine = DetectionEngine()
severity_classifier = SeverityClassifier()
escalation_pipeline = EscalationPipeline()
report_generator = ReportGenerator()

# WebSocket connections for real-time alerts
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize database and load models"""
    await db.initialize()
    print("Factory Compliance System started successfully")

@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """
    Endpoint to upload and analyze a video clip
    """
    try:
        # Save uploaded video
        video_path = f"data/videos/{file.filename}"
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process video through detection engine
        detections = await detection_engine.process_video(video_path)
        
        # Process each detection
        events = []
        for detection in detections:
            # Classify severity
            severity = severity_classifier.classify(detection)
            
            # Create event
            event = ViolationEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat() + "Z",
                clip_id=file.filename,
                zone=detection.get("zone", "Unknown"),
                behavior_class=detection["behavior_class"],
                policy_rule_ref=detection["policy_rule_ref"],
                event_description=detection["description"],
                severity=severity.value,
                escalation_action=""
            )
            
            # Escalate based on severity
            event.escalation_action = await escalation_pipeline.process_event(event)
            
            # Save to database
            await db.save_event(event)
            
            # Generate report
            await report_generator.generate_report(event)
            
            # Send real-time alert for HIGH/CRITICAL
            if severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                await broadcast_alert(event)
            
            events.append(event.dict())
        
        return JSONResponse({
            "status": "success",
            "events": events,
            "total_violations": len(events)
        })
    
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

async def broadcast_alert(event: ViolationEvent):
    """Broadcast alert to all connected WebSocket clients"""
    for connection in active_connections:
        try:
            await connection.send_json(event.dict())
        except:
            pass

@app.get("/events")
async def get_events(
    severity: str = None,
    behavior_class: str = None,
    start_date: str = None,
    end_date: str = None
):
    """Get events with filters"""
    events = await db.get_events(
        severity=severity,
        behavior_class=behavior_class,
        start_date=start_date,
        end_date=end_date
    )
    return JSONResponse({"events": events})

@app.get("/reports/{event_id}")
async def get_report(event_id: str):
    """Get report for specific event"""
    report = await report_generator.get_report(event_id)
    if report:
        return JSONResponse({"report": report})
    return JSONResponse({"error": "Report not found"}, status_code=404)