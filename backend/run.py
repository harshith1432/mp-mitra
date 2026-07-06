import uvicorn
import os
import subprocess
import atexit

if __name__ == "__main__":
    # Prevent starting duplicate frontend servers when Uvicorn reloads code
    if not os.environ.get("MP_MITRA_FRONTEND_STARTED"):
        os.environ["MP_MITRA_FRONTEND_STARTED"] = "true"
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.abspath(os.path.join(script_dir, "..", "frontend"))
        
        print("\n*** [MP Mitra] Starting Vite Frontend Server... ***")
        try:
            # Spawn npm run dev in frontend directory (shell=True for Windows shell execution)
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                shell=True
            )
            
            # Ensure the frontend server is terminated when python exit is triggered
            def cleanup_frontend():
                print("\n*** [MP Mitra] Terminating Frontend Server... ***")
                try:
                    frontend_process.terminate()
                except Exception:
                    pass
            atexit.register(cleanup_frontend)
            
        except Exception as e:
            print(f"*** [MP Mitra] Warning: Could not automatically launch frontend server: {e} ***")

    print("*** [MP Mitra] Launching FastAPI Backend Server... ***")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
