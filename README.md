# Factory Compliance & Alert Escalation System

A complete, fully functional system for detecting factory safety violations in video feeds, classifying severity, escalating alerts in real-time, and maintaining an immutable audit trail.

## Overview

This system provides:

- **Video Behavior Detection**: Process video clips to detect unsafe behaviors using folder-based classification
- **Policy-Based Severity Classification**: Assign severity levels (LOW, MEDIUM, HIGH, CRITICAL) based on compliance policy
- **Automated Escalation Pipeline**: Route events to database or trigger real-time alerts based on severity
- **Report Generation**: Generate JSON and CSV reports for all violations
- **Real-time Dashboard**: Streamlit interface for monitoring, analyzing, and exporting compliance data
- **REST API**: FastAPI backend with WebSocket support for real-time alerts
- **Complete Audit Trail**: Immutable records of all compliance events

## Architecture

### Module 1: Detection Engine

- Processes video files and detects behavioral violations
- Uses dataset folder names to identify behavior classes
- Generates detection results with: clip_id, timestamp, behavior_class, policy_rule_ref, description, zone

### Module 2: Severity Categorization

- Maps behaviors to severity levels based on policy:
  - **LOW**: Opened Panel Cover
  - **MEDIUM**: Safe Walkway Violation
  - **HIGH**: Unauthorized Intervention
  - **CRITICAL**: Carrying Overload with Forklift
  - **NONE**: Safe behaviors (no escalation)

### Module 3: Escalation Pipeline

- Routes events intelligently:
  - **LOW/MEDIUM**: Logged to database only
  - **HIGH/CRITICAL**: Logged to database AND trigger real-time WebSocket alerts
  - **NONE**: Skipped (safe behaviors)

### Module 4: Report Generation

- Generates immutable reports in two formats:
  - **JSON**: Individual report files for each violation
  - **CSV**: Append-only audit log for compliance tracking

### Module 5: Operations Dashboard

Three interactive views:

- **Dashboard Overview**: System statistics, event distribution, recent events
- **Upload Video**: Single video analysis
- **Batch Analysis**: Process multiple dataset videos
- **Alert Timeline**: Real-time event stream with filters
- **Historical Log**: Query and export compliance history

## Project Structure

```
factory-compliance-system/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration and settings
│   ├── models.py                # Pydantic and SQLAlchemy models
│   ├── database.py              # Database operations
│   ├── policy_parser.py         # Policy extraction
│   ├── detection_engine.py      # Video processing
│   ├── severity_classifier.py   # Severity assignment
│   ├── escalation_pipeline.py   # Event routing and alerts
│   ├── report_generator.py      # Report generation
│   ├── utils.py                 # Helper functions
│   └── main.py                  # FastAPI application
├── frontend/
│   ├── app.py                   # Streamlit dashboard
│   └── components.py            # Dashboard components
├── data/                        # Dataset directory (user-provided)
├── reports/                     # Generated reports
│   ├── json/                    # JSON report files
│   └── audit_log.csv            # CSV audit trail
├── logs/                        # Application logs
├── compliance.db                # SQLite database
├── requirements.txt             # Python dependencies
├── run.py                       # Launch script
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Git
- 1GB+ available disk space

### Setup Steps

1. **Clone the repository**

```bash
git clone <repository-url>
cd factory-compliance-system
```

2. **Create virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Prepare dataset**
   Place your video dataset in:

```
data/videos/Video Dataset for Safe and Unsafe Behaviours/Safe and Unsafe Behaviours Dataset/
├── train/
│   ├── 0_safe_walkway_violation/
│   ├── 1_unauthorized_intervention/
│   ├── 2_opened_panel_cover/
│   ├── 3_carrying_overload_with_forklift/
│   ├── 4_safe_walkway/
│   ├── 5_authorized_intervention/
│   └── 6_closed_panel_cover/
└── test/
    └── [same structure as train]
```

## Usage

### Quick Start

```bash
python run.py
```

This launches:

- Backend API: http://localhost:8000
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Running Services Separately

**Backend only** (API at port 8000):

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend only** (Dashboard at port 8501):

```bash
streamlit run frontend/app.py
```

## API Endpoints

### Video Analysis

- `POST /analyze-video` - Analyze single uploaded video
- `POST /analyze-batch` - Analyze multiple dataset videos

### Event Queries

- `GET /events` - Query compliance events with filters
- `GET /events/{event_id}` - Get specific event
- `GET /reports/{event_id}` - Get event report

### Statistics

- `GET /dataset/stats` - Dataset statistics
- `GET /events/stats/severity` - Events by severity
- `GET /system/summary` - Overall system summary

### Export

- `GET /export/csv` - Export events to CSV

### Real-time

- `WebSocket /ws/alerts` - Real-time alert streaming

## Dashboard Features

### 🏠 Dashboard Overview

- System health metrics
- Event distribution by severity
- Dataset statistics
- Recent violations list

### 📹 Upload Video

- Single video upload
- Zone assignment
- Real-time analysis
- Immediate results display

### ⚙️ Batch Analysis

- Select dataset (train/test)
- Filter by behavior classes
- Process multiple videos
- Summary statistics

### 🔴 Alert Timeline

- Real-time event stream
- Filter by severity, behavior, zone, date range
- Timeline visualization
- Alert notifications

### 📋 Historical Log

- Complete event history
- Advanced filtering
- CSV/JSON export
- Audit trail

## Configuration

Edit `app/config.py` to customize:

- Database location
- Dataset paths
- API host/port
- Severity mappings
- Alert thresholds
- Zone names

## Database

SQLite database (`compliance.db`) with tables:

- `compliance_events` - All detected violations
- `compliance_reports` - Report metadata
- `alert_logs` - Alert delivery tracking

## Report Generation

### JSON Reports

- Location: `reports/json/{event_id}.json`
- Contains: All event details with metadata
- Format: Individual files per violation

### CSV Audit Log

- Location: `reports/audit_log.csv`
- Contains: Append-only record of all violations
- Format: Chronological event log

### CSV Export

- Export any filtered set of events
- Date range, severity, behavior class filters
- Download from dashboard

## Logging

Application logs are written to:

- `logs/database.log` - Database operations
- `logs/system.log` - System events

## Behavior Classifications

### Unsafe (Alert-triggering) Behaviors

1. **Safe Walkway Violation** (MEDIUM)
   - Employee outside designated safe walkway
   - Policy Ref: POL-PED-01

2. **Unauthorized Intervention** (HIGH)
   - Unauthorized personnel intervening with equipment
   - Policy Ref: POL-EQP-01

3. **Opened Panel Cover** (LOW)
   - Electrical panel or equipment cover left open
   - Policy Ref: POL-ELE-01

4. **Carrying Overload with Forklift** (CRITICAL)
   - Forklift carrying load exceeding safe capacity
   - Policy Ref: POL-FOR-01

### Safe Behaviors (No Alerts)

1. **Safe Walkway** - Employee in designated walkway
2. **Authorized Intervention** - Authorized personnel intervention
3. **Closed Panel Cover** - Equipment panels properly closed

## API Examples

### Upload and Analyze Video

```bash
curl -X POST "http://localhost:8000/analyze-video" \
  -F "file=@video.mp4" \
  -F "zone=Factory Floor A"
```

### Get Recent Events

```bash
curl "http://localhost:8000/events?severity=HIGH&limit=10"
```

### Export CSV

```bash
curl "http://localhost:8000/export/csv?severity=CRITICAL" > events.csv
```

## Troubleshooting

### Backend won't start

- Check if port 8000 is available: `netstat -an | grep 8000`
- Verify dependencies: `pip install -r requirements.txt`

### Dashboard won't connect

- Ensure backend is running on http://localhost:8000
- Check firewall settings
- Verify CORS is enabled (it is by default)




## Performance Notes

- Video processing uses OpenCV frame-by-frame analysis
- Batch processing analyzes all videos in dataset
- WebSocket connections support multiple simultaneous clients
- Database queries are indexed by event_id, timestamp, severity
- CSV exports limited to 10,000 events for performance



## Testing

Run the system with sample data:

1. Upload a test video via dashboard
2. Monitor real-time alerts
3. Export historical events
4. Verify report generation

## Support

For issues or questions:

1. Check logs in `logs/` directory
2. Review API documentation at `/docs`
3. Check system status at `/health`




