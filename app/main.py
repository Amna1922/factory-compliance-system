"""
FastAPI backend for Factory Compliance & Alert Escalation System
Provides REST API endpoints and WebSocket support for real-time alerts
"""
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Query, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import cv2

from app.config import API_HOST, API_PORT, DEFAULT_ZONE, SEVERITY_LEVELS
from app.models import (
    ComplianceEvent, ComplianceReport, AlertNotification, AnalysisRequest,
    BatchAnalysisRequest, EventFilter, DatasetStats, generate_event_id
)
from app.database import (
    init_db, get_all_events, get_event, get_event_count_by_severity,
    get_recent_events, get_events_by_date_range
)
from app.detection_engine import get_detection_engine
from app.severity_classifier import get_severity_classifier
from app.escalation_pipeline import (
    get_escalation_pipeline, add_websocket_connection, remove_websocket_connection
)
from app.report_generator import get_report_generator
from app.policy_parser import get_policy_parser
from app.utils import get_dataset_loader, validate_dataset

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Factory Compliance & Alert Escalation System",
    description="API for compliance monitoring, violation detection, and alert management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get module instances
detection_engine = get_detection_engine()
severity_classifier = get_severity_classifier()
escalation_pipeline = get_escalation_pipeline()
report_generator = get_report_generator()
policy_parser = get_policy_parser()
dataset_loader = get_dataset_loader()


# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("=" * 50)
    logger.info("Factory Compliance System Starting Up")
    logger.info("=" * 50)
    
    try:
        # Initialize database
        init_db()
        logger.info("✓ Database initialized")
        
        # Validate dataset
        valid, message = validate_dataset()
        logger.info(f"✓ Dataset validation: {message}")
        
        # Validate policy
        policy_parser.validate_policy_rules()
        logger.info("✓ Policy rules validated")
        
        logger.info("=" * 50)
        logger.info("System startup complete - Ready for operations")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("System shutting down...")


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Check system health"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Video Analysis Endpoints ====================

@app.post("/analyze-video", response_model=ComplianceEvent)
async def analyze_video(file: UploadFile = File(...), zone: Optional[str] = Query(None)):
    """
    Analyze a single uploaded video for compliance violations
    Returns the detected compliance event
    """
    try:
        zone = zone or DEFAULT_ZONE
        
        # Save uploaded file
        file_path = f"temp/{file.filename}"
        Path("temp").mkdir(exist_ok=True)
        
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Process video
        detections = detection_engine.process_video(file_path, zone)
        
        if not detections:
            raise HTTPException(status_code=400, detail="No behaviors detected in video")
        
        detection = detections[0]
        
        # Generate event ID
        event_id = generate_event_id()
        timestamp = datetime.utcnow()
        
        # Process through escalation pipeline
        result = escalation_pipeline.process_event(
            event_id=event_id,
            timestamp=timestamp,
            clip_id=detection.clip_id,
            zone=detection.zone,
            behavior_class=detection.behavior_class,
            policy_rule_ref=detection.policy_rule_ref,
            event_description=detection.description,
            confidence=detection.confidence
        )
        
        # Generate reports
        if result["processed"]:
            report_generator.generate_both_reports(
                event_id=event_id,
                timestamp=timestamp,
                clip_id=detection.clip_id,
                zone=detection.zone,
                behavior_class=detection.behavior_class,
                policy_rule_ref=detection.policy_rule_ref,
                event_description=detection.description,
                severity=result["severity"],
                escalation_action=result["escalation_action"]
            )
        
        # Broadcast alert if HIGH/CRITICAL
        if result.get("alert_triggered"):
            alert_data = {
                "event_id": event_id,
                "severity": result["severity"],
                "behavior_class": detection.behavior_class,
                "zone": detection.zone,
                "timestamp": timestamp.isoformat(),
                "description": detection.description,
                "color": severity_classifier.get_alert_color(result["severity"])
            }
            await escalation_pipeline.broadcast_alert(event_id, alert_data)
        
        # Return event
        event = get_event(event_id)
        return ComplianceEvent(**event.to_dict())
        
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if Path(file_path).exists():
            Path(file_path).unlink()


@app.post("/analyze-batch")
async def analyze_batch_videos(request: BatchAnalysisRequest):
    """
    Analyze multiple videos from the dataset
    Returns summary of detections
    """
    try:
        logger.info(f"Starting batch analysis: dataset_type={request.dataset_type}")
        
        results = detection_engine.process_dataset(
            dataset_type=request.dataset_type,
            zone=DEFAULT_ZONE,
            behavior_classes=request.behavior_classes
        )
        
        # Process each detection through escalation pipeline
        total_processed = 0
        total_alerts = 0
        
        for behavior_class, detections in results.items():
            for detection in detections:
                event_id = generate_event_id()
                timestamp = datetime.utcnow()
                
                result = escalation_pipeline.process_event(
                    event_id=event_id,
                    timestamp=timestamp,
                    clip_id=detection.clip_id,
                    zone=detection.zone,
                    behavior_class=detection.behavior_class,
                    policy_rule_ref=detection.policy_rule_ref,
                    event_description=detection.description,
                    confidence=detection.confidence
                )
                
                if result["processed"]:
                    total_processed += 1
                    
                    # Generate reports
                    report_generator.generate_both_reports(
                        event_id=event_id,
                        timestamp=timestamp,
                        clip_id=detection.clip_id,
                        zone=detection.zone,
                        behavior_class=detection.behavior_class,
                        policy_rule_ref=detection.policy_rule_ref,
                        event_description=detection.description,
                        severity=result["severity"],
                        escalation_action=result["escalation_action"]
                    )
                    
                    if result.get("alert_triggered"):
                        total_alerts += 1
                        alert_data = {
                            "event_id": event_id,
                            "severity": result["severity"],
                            "behavior_class": detection.behavior_class,
                            "zone": detection.zone,
                            "timestamp": timestamp.isoformat(),
                            "description": detection.description
                        }
                        await escalation_pipeline.broadcast_alert(event_id, alert_data)
        
        return {
            "status": "completed",
            "dataset_type": request.dataset_type,
            "total_videos_analyzed": sum(len(d) for d in results.values()),
            "events_processed": total_processed,
            "alerts_triggered": total_alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Event Query Endpoints ====================

@app.get("/events", response_model=List[ComplianceEvent])
async def get_events(
    severity: Optional[str] = Query(None),
    behavior_class: Optional[str] = Query(None),
    zone: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """
    Get compliance events with optional filters
    Returns list of compliance events
    """
    try:
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        events = get_all_events(
            severity=severity,
            behavior_class=behavior_class,
            zone=zone,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit
        )
        
        return [ComplianceEvent(**event.to_dict()) for event in events]
        
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}", response_model=ComplianceEvent)
async def get_event_detail(event_id: str):
    """Get a specific compliance event by ID"""
    try:
        event = get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return ComplianceEvent(**event.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{event_id}", response_model=ComplianceReport)
async def get_report(event_id: str):
    """Get compliance report for an event"""
    try:
        event = get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return ComplianceReport(**event.to_dict(), report_generated_at=event.created_at)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Statistics Endpoints ====================

@app.get("/dataset/stats", response_model=DatasetStats)
async def get_dataset_stats():
    """Get dataset statistics"""
    try:
        stats = dataset_loader.get_dataset_statistics()
        return DatasetStats(**stats)
    except Exception as e:
        logger.error(f"Error getting dataset stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/stats/severity")
async def get_severity_stats():
    """Get event statistics by severity"""
    try:
        return get_event_count_by_severity()
    except Exception as e:
        logger.error(f"Error getting severity stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/summary")
async def get_system_summary():
    """Get overall system summary"""
    try:
        dataset_stats = dataset_loader.get_dataset_statistics()
        severity_stats = get_event_count_by_severity()
        recent_events = len(get_recent_events(hours=24))
        
        return {
            "dataset": dataset_stats,
            "event_severity_distribution": severity_stats,
            "recent_events_24h": recent_events,
            "behaviors": dataset_loader.get_all_behavior_classes(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Export Endpoints ====================

@app.get("/export/csv")
async def export_events_csv(
    severity: Optional[str] = Query(None),
    behavior_class: Optional[str] = Query(None)
):
    """Export events to CSV file"""
    try:
        filename = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = report_generator.export_events_to_csv(
            filename=filename,
            severity=severity,
            behavior_class=behavior_class
        )
        
        if not filepath:
            raise HTTPException(status_code=404, detail="No events to export")
        
        return FileResponse(
            path=filepath,
            media_type="text/csv",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket Endpoint ====================

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alert streaming"""
    try:
        await websocket.accept()
        add_websocket_connection(websocket)
        logger.info("WebSocket client connected")
        
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        remove_websocket_connection(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        remove_websocket_connection(websocket)


# ==================== API Documentation ====================

@app.get("/")
async def root():
    """API root endpoint with documentation"""
    return {
        "name": "Factory Compliance & Alert Escalation System",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "video_analysis": {
                "POST /analyze-video": "Analyze single uploaded video",
                "POST /analyze-batch": "Analyze multiple dataset videos"
            },
            "events": {
                "GET /events": "Query compliance events",
                "GET /events/{event_id}": "Get specific event",
                "GET /reports/{event_id}": "Get event report"
            },
            "statistics": {
                "GET /dataset/stats": "Dataset statistics",
                "GET /events/stats/severity": "Event distribution by severity",
                "GET /system/summary": "Overall system summary"
            },
            "export": {
                "GET /export/csv": "Export events to CSV"
            },
            "realtime": {
                "WebSocket /ws/alerts": "Real-time alert stream"
            }
        }
    }


def run_server(host: str = API_HOST, port: int = API_PORT):
    """Run the FastAPI server"""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
