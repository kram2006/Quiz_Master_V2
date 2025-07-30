#!/usr/bin/env python3
"""
Development startup script for QuizMaster with Redis and Celery
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        return False

def start_redis():
    """Start Redis server"""
    print("🚀 Starting Redis server...")
    try:
        # Try to start Redis using docker if available
        subprocess.run(["docker", "run", "-d", "--name", "quizmaster-redis-dev", 
                       "-p", "6379:6379", "redis:7-alpine"], 
                      check=True, capture_output=True)
        print("✅ Redis started with Docker")
        time.sleep(2)  # Wait for Redis to start
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Docker not available or Redis already running")
        return False
    except FileNotFoundError:
        print("⚠️  Docker not found. Please start Redis manually:")
        print("   docker run -d --name quizmaster-redis-dev -p 6379:6379 redis:7-alpine")
        return False

def start_celery_worker():
    """Start Celery worker"""
    print("🚀 Starting Celery worker...")
    try:
        worker_process = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "main.celery", 
            "worker", "--loglevel=info"
        ])
        print(f"✅ Celery worker started (PID: {worker_process.pid})")
        return worker_process
    except Exception as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return None

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("🚀 Starting Celery beat scheduler...")
    try:
        beat_process = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "main.celery", 
            "beat", "--loglevel=info"
        ])
        print(f"✅ Celery beat started (PID: {beat_process.pid})")
        return beat_process
    except Exception as e:
        print(f"❌ Failed to start Celery beat: {e}")
        return None

def start_flask_app():
    """Start Flask application"""
    print("🚀 Starting Flask application...")
    try:
        flask_process = subprocess.Popen([
            sys.executable, "main.py"
        ])
        print(f"✅ Flask app started (PID: {flask_process.pid})")
        return flask_process
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return None

def cleanup(processes):
    """Clean up processes on exit"""
    print("\n🛑 Shutting down services...")
    for process in processes:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    print("✅ All services stopped")

def main():
    """Main startup function"""
    print("🎯 QuizMaster Development Environment")
    print("=" * 50)
    
    # Check if Redis is running
    if not check_redis():
        if not start_redis():
            print("❌ Cannot start without Redis. Exiting.")
            sys.exit(1)
    
    processes = []
    
    # Handle cleanup on exit
    def signal_handler(signum, frame):
        cleanup(processes)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start Celery worker
        worker_process = start_celery_worker()
        if worker_process:
            processes.append(worker_process)
        
        # Start Celery beat
        beat_process = start_celery_beat()
        if beat_process:
            processes.append(beat_process)
        
        # Wait a moment for Celery services to start
        time.sleep(3)
        
        # Start Flask app
        flask_process = start_flask_app()
        if flask_process:
            processes.append(flask_process)
        
        print("\n🎉 All services started successfully!")
        print("📱 Flask app: http://localhost:5000")
        print("🌱 Celery Flower: http://localhost:5555")
        print("📊 Redis: localhost:6379")
        print("\nPress Ctrl+C to stop all services")
        
        # Keep the script running
        while True:
            time.sleep(1)
            # Check if any process has died
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    print(f"⚠️  Process {i} has stopped unexpectedly")
    
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    finally:
        cleanup(processes)

if __name__ == "__main__":
    main() 