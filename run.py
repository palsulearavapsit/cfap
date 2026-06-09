import os
import sys
import subprocess
import time
import signal

def run_servers():
    print("🍀 Starting EcoTrack AI Platform...")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # Path to virtualenv python interpreter
    venv_python = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        # Fallback to system python if venv not in default path
        venv_python = "python"
        print("⚠️ Virtual environment python not found at default location. Falling back to system python.")
    
    # Define command processes
    backend_cmd = [venv_python, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
    frontend_cmd = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "dev"]
    
    backend_proc = None
    frontend_proc = None

    try:
        # 1. Start Backend FastAPI
        print("⚡ Starting backend FastAPI server on http://127.0.0.1:8000 ...")
        # Set PYTHONPATH so backend modules resolve correctly
        env = os.environ.copy()
        env["PYTHONPATH"] = root_dir
        
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            env=env
        )
        
        # Give backend a moment to bind to port
        time.sleep(1.5)
        
        # 2. Start Frontend Vite
        print("🎨 Starting frontend Vite React server on http://localhost:5173 ...")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir
        )
        
        print("\n🚀 Both servers are running! Press Ctrl+C to stop both cleanly.\n")
        
        # Monitor processes
        while True:
            # Check if either process terminated
            b_status = backend_proc.poll()
            f_status = frontend_proc.poll()
            
            if b_status is not None:
                print(f"❌ Backend server stopped with exit code: {b_status}")
                break
            if f_status is not None:
                print(f"❌ Frontend server stopped with exit code: {f_status}")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers gracefully...")
    finally:
        # Gracefully terminate child processes
        for proc, name in [(backend_proc, "Backend"), (frontend_proc, "Frontend")]:
            if proc and proc.poll() is None:
                print(f"🔌 Stopping {name} process...")
                try:
                    if sys.platform == "win32":
                        # On Windows, taskkill kills the process tree, preventing orphan Node/Python runners
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                    else:
                        proc.terminate()
                        proc.wait(timeout=3)
                except Exception as e:
                    print(f"⚠️ Error stopping {name} process: {e}")
                    
        print("✅ Shutdown complete. Have a green day! 🌍")

if __name__ == "__main__":
    run_servers()
