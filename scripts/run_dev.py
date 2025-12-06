import subprocess
import sys
import time
import signal
import os

def run_dev():
    print("🚀 Starting Development Environment...")
    
    # List of processes to manage
    procs = []
    
    try:
        # 1. Start Redis (Optional check or Assume running)
        # In a real dev script we might check docker, but here we assume docker-compose up is handling redis 
        # or the user has it running. We won't start it to avoid conflict.
        
        # 2. Start Celery Worker
        print("🔧 Starting Celery Worker...")
        # Use sys.executable to ensure we use the same venv
        celery_cmd = [sys.executable, "-m", "celery", "-A", "app.core.celery_app", "worker", "--loglevel=debug", "--concurrency=1", "--pool=solo"]

        celery_proc = subprocess.Popen(celery_cmd, cwd=os.getcwd())
        procs.append(celery_proc)
        
        # 3. Start FastAPI
        print("🌐 Starting API Server...")
        uvicorn_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        api_proc = subprocess.Popen(uvicorn_cmd, cwd=os.getcwd())
        procs.append(api_proc)
        
        print("\n✨ All systems go! Press Ctrl+C to stop.\n")
        print("📱 UI: http://localhost:8000")
        
        # Wait for processes
        for p in procs:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    run_dev()
