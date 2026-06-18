from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Dict, Any
import json
from datetime import datetime
import uuid
import tempfile
import shutil

from .config import settings
from .models import ViolationEvent, SeverityLevel
from .database import Database
from .detection_engine import DetectionEngine
from .severity_classifier import SeverityClassifier
from .escalation_pipeline import EscalationPipeline
from .report_generator import ReportGenerator
from .utils import data_loader

app = FastAPI(title="Factory Compliance System")

# CORS middleware
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

# WebSocket connections
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize database and load models"""
    await db.initialize()
    print("🚀 Factory Compliance System started successfully")
    print(f"📁 Dataset location: {settings.DATASET_DIR}")
    
    # Print dataset statistics
    stats = data_loader.get_statistics()
    print("\n📊 Dataset Statistics:")
    for split in ["train", "test"]:
        print(f"  {split.upper()}:")
        print(f"    Total: {stats[split]['total']} videos")
        print(f"    Unsafe: {stats[split]['unsafe']} videos")
        print(f"    Safe: {stats[split]['safe']} videos")
        if "class_counts" in stats[split]:
            print("    Class distribution:")
            for class_name, count in stats[split]["class_counts"].items():
                print(f"      - {class_name}: {count}")

@app.get("/dataset/stats")
async def get_dataset_stats():
    """Get dataset statistics"""
    stats = data_loader.get_statistics()
    return JSONResponse(stats)

@app.get("/dataset/videos/{split}")
async def get_videos(split: str = "train", unsafe_only: bool = False):
    """Get list of videos"""
    if split not in ["train", "test"]:
        return JSONResponse({"error": "Split must be 'train' or 'test'"}, status_code=400)
    
    if unsafe_only:
        videos = data_loader.get_unsafe_videos(split)
    else:
        videos = data_loader.get_all_videos(split)
    
    return JSONResponse({"count": len(videos), "videos": videos[:10]})  # Return first 10

@app.post("/analyze-batch")
async def analyze_batch(split: str = "test", max_videos: int = 10):
    """Analyze a batch of videos from the dataset"""
    unsafe_videos = data_loader.get_unsafe_videos(split)[:max_videos]
    
    if not unsafe_videos:
        return JSONResponse({"error": "No videos found"}, status_code=404)
    
    events = []
    for video_info in unsafe_videos:
        # Process video
        detection = await detection_engine.process_video_file(video_info["path"])
        
        if detection.get("violation_detected", False):
            # Create event
            event = ViolationEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat() + "Z",
                clip_id=Path(video_info["path"]).name,
                zone=detection.get("zone", "Unknown"),
                behavior_class=detection["behavior_class"],
                policy_rule_ref=detection.get("policy_rule_ref", ""),
                event_description=detection["description"],
                severity=detection.get("severity", "MEDIUM"),
                escalation_action=""
            )
            
            # Classify severity
            severity = severity_classifier.classify(detection)
            event.severity = severity.value
            
            # Escalate
            event.escalation_action = await escalation_pipeline.process_event(event)
            
            # Save to database
            await db.save_event(event)
            
            # Generate report
            await report_generator.generate_report(event)
            
            events.append(event.dict())
    
    return JSONResponse({
        "status": "success",
        "processed": len(unsafe_videos),
        "violations": len(events),
        "events": events
    })

@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """Upload and analyze a single video file"""
    try:
        # Save uploaded video
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir) / file.filename
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process video
        detection = await detection_engine.process_video_file(str(temp_path))
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        if detection.get("violation_detected", False):
            # Create event
            event = ViolationEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat() + "Z",
                clip_id=file.filename,
                zone=detection.get("zone", "Unknown"),
                behavior_class=detection["behavior_class"],
                policy_rule_ref=detection.get("policy_rule_ref", ""),
                event_description=detection["description"],
                severity=detection.get("severity", "MEDIUM"),
                escalation_action=""
            )
            
            # Classify severity
            severity = severity_classifier.classify(detection)
            event.severity = severity.value
            
            # Escalate
            event.escalation_action = await escalation_pipeline.process_event(event)
            
            # Save to database
            await db.save_event(event)
            
            # Generate report
            await report_generator.generate_report(event)
            
            return JSONResponse({
                "status": "success",
                "violation_detected": True,
                "event": event.dict()
            })
        else:
            return JSONResponse({
                "status": "success",
                "violation_detected": False,
                "message": "No violation detected"
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
    """Broadcast alert to all connected clients"""
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