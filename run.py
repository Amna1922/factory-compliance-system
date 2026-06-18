#!/usr/bin/env python
"""
Run script for Factory Compliance & Alert Escalation System
Launches both backend (FastAPI) and frontend (Streamlit) servers
"""
import subprocess
import sys
import time
import os
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📋 Checking dependencies...")
    try:
        import fastapi
        import streamlit
        import sqlalchemy
        import cv2
        import numpy
        print("✅ All dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {str(e)}")
        print("   Run: pip install -r requirements.txt")
        return False


def run_backend():
    """Run FastAPI backend server"""
    print("\n🚀 Starting FastAPI Backend...")
    print("   📍 http://localhost:8000")
    print("   📖 Docs: http://localhost:8000/docs")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(PROJECT_ROOT)
        )
    except KeyboardInterrupt:
        print("\n⏹️  Backend stopped")
    except Exception as e:
        print(f"❌ Backend error: {str(e)}")


def run_frontend():
    """Run Streamlit frontend dashboard"""
    print("\n🎨 Starting Streamlit Frontend...")
    print("   📍 http://localhost:8501")
    
    time.sleep(3)  # Wait for backend to start
    
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--logger.level=error"],
            cwd=str(PROJECT_ROOT)
        )
    except KeyboardInterrupt:
        print("\n⏹️  Frontend stopped")
    except Exception as e:
        print(f"❌ Frontend error: {str(e)}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("🏭 Factory Compliance & Alert Escalation System")
    print("Version 1.0.0")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create necessary directories
    directories = ["logs", "reports", "reports/json", "temp"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("\n📦 System Initialization")
    print("   ✓ Directories created")
    print("   ✓ Configuration loaded")
    
    # Choose between running both or just one
    print("\n🔧 Starting Services...")
    print("   1. Backend + Frontend (Recommended)")
    print("   2. Backend only")
    print("   3. Frontend only")
    
    mode = input("\nSelect mode (1/2/3) [default=1]: ").strip() or "1"
    
    print("\n" + "=" * 60)
    print("Starting services...")
    print("=" * 60)
    print("\n💡 Press Ctrl+C to stop all services\n")
    
    try:
        if mode == "1":
            # Start backend in subprocess, frontend in main
            backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(PROJECT_ROOT)
            )
            
            print("🚀 Backend started")
            time.sleep(3)
            
            print("🎨 Frontend starting...")
            run_frontend()
            
            backend_process.terminate()
            
        elif mode == "2":
            run_backend()
            
        elif mode == "3":
            run_frontend()
        
        else:
            print("❌ Invalid choice")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("⏹️  System stopped")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
