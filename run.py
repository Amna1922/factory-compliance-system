import uvicorn
import streamlit as st
import subprocess
import sys
import os

def start_backend():
    """Start FastAPI backend"""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def start_frontend():
    """Start Streamlit frontend"""
    subprocess.run(["streamlit", "run", "frontend/app.py", "--server.port", "8501"])

if __name__ == "__main__":
    import multiprocessing as mp
    
    # Start backend
    backend_process = mp.Process(target=start_backend)
    backend_process.start()
    
    # Start frontend
    frontend_process = mp.Process(target=start_frontend)
    frontend_process.start()
    
    print("🚀 System Started")
    print("📡 Backend: http://localhost:8000")
    print("📊 Dashboard: http://localhost:8501")
    print("📋 API Documentation: http://localhost:8000/docs")
    
    try:
        backend_process.join()
        frontend_process.join()
    except KeyboardInterrupt:
        backend_process.terminate()
        frontend_process.terminate()
        print("\nSystem stopped")