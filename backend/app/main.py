import os
import sys
import asyncio
import json
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import Base, engine
from app.database.crawler_manager import crawler_manager

app = FastAPI(title="MP Mitra: AI Decision Intelligence Platform", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root route is handled below by the catch-all SPA handler


# ─── WebSocket: Real-time crawler log stream ──────────────────────────────────
@app.websocket("/ws/crawler-logs")
async def crawler_logs_ws(websocket: WebSocket):
    """
    WebSocket endpoint — streams real-time crawler log events to connected clients.
    On connect, replays the last 500 buffered log lines, then streams live events.
    """
    await websocket.accept()

    # Give crawler_manager a reference to the running event loop (once)
    loop = asyncio.get_event_loop()
    crawler_manager.attach_event_loop(loop)

    # Subscribe to live events
    queue = crawler_manager.subscribe()

    try:
        # 1. Replay recent log buffer so late-joining clients see history
        for past_event in crawler_manager.get_log_buffer():
            await websocket.send_text(json.dumps(past_event))

        # 2. Stream live events
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_text(json.dumps(event))
            except asyncio.TimeoutError:
                # Send a heartbeat ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        crawler_manager.unsubscribe(queue)


# ─── WebSocket: Real-time dashboard updates ───────────────────────────────────
class DashboardConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

dashboard_manager = DashboardConnectionManager()

@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await dashboard_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)

@app.post("/api/admin/broadcast-suggestion")
async def broadcast_suggestion(data: dict):
    await dashboard_manager.broadcast(json.dumps(data))
    return {"status": "broadcasted"}


# ─── Register Routers ─────────────────────────────────────────────────────────
from app.routing.constituency import router as constituency_router
from app.routing.citizen import router as citizen_router
from app.routing.prioritize import router as prioritize_router
from app.routing.admin import router as admin_router
from app.routing.copilot import router as copilot_router
from app.routing.whatsapp import router as whatsapp_router
from app.routing.geo import router as geo_router

app.include_router(constituency_router, prefix="/api/constituency", tags=["Constituency"])
app.include_router(citizen_router,      prefix="/api/citizen",       tags=["Citizen Interaction"])
app.include_router(prioritize_router,   prefix="/api/prioritize",    tags=["Prioritization"])
app.include_router(admin_router,        prefix="/api/admin",         tags=["Admin Portal"])
app.include_router(copilot_router,      prefix="/api/copilot",       tags=["MP Copilot"])
app.include_router(whatsapp_router,     prefix="/api/whatsapp",      tags=["WhatsApp Webhook"])
app.include_router(geo_router,          prefix="/api/geo",           tags=["Geospatial Intelligence"])


# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    print("Database tables validated.")
    Base.metadata.create_all(bind=engine)

    # Initialize / index RAG vector store in background thread to keep startup fast
    import threading
    def bg_startup_vector():
        try:
            from app.database.vector_store import rebuild_vector_store
            rebuild_vector_store()
        except Exception as err:
            print(f"[Startup] Vector store rebuild failed to start: {err}")
    threading.Thread(target=bg_startup_vector, daemon=True).start()

    # Start background crawler thread (legacy continuous loop)
    import threading
    import time
    from app.database.connection import SessionLocal
    from app.database.crawler_service import crawl_external_sources

    def run_crawler_loop():
        print("[AI Research Agent] Background web scraping loop started.")
        db = SessionLocal()
        try:
            crawl_external_sources(db)
            # Reindex after successful crawl
            try:
                from app.database.vector_store import rebuild_vector_store
                rebuild_vector_store()
            except Exception:
                pass
        except Exception as err:
            print(f"[AI Research Agent] Error on startup crawl: {err}")
        finally:
            db.close()

        while True:
            time.sleep(3600)
            db = SessionLocal()
            try:
                print("[AI Research Agent] Starting hourly scheduled crawl...")
                crawl_external_sources(db)
                try:
                    from app.database.vector_store import rebuild_vector_store
                    rebuild_vector_store()
                except Exception:
                    pass
            except Exception as err:
                print(f"[AI Research Agent] Error on scheduled crawl: {err}")
            finally:
                db.close()

    crawler_thread = threading.Thread(target=run_crawler_loop, daemon=True)
    crawler_thread.start()

# Serve built frontend static assets with SPA routing fallback
import sys
import subprocess
from fastapi.responses import FileResponse, HTMLResponse
from starlette.responses import Response

if getattr(sys, 'frozen', False):
    # PyInstaller bundle path
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    dist_path = os.path.join(bundle_dir, "frontend", "dist")
else:
    # Standard local environment path
    dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

    # Auto-rebuild frontend if missing and running in development mode
    if not os.path.exists(dist_path) or not os.path.exists(os.path.join(dist_path, "index.html")):
        print("[Startup] Frontend build not found at: " + dist_path)
        print("[Startup] Attempting to rebuild frontend...")
        try:
            subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=True)
            print("[Startup] Node.js/npm detected. Running 'npm install'...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)
            print("[Startup] Running 'npm run build'...")
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
            print("[Startup] Frontend rebuild completed successfully.")
        except Exception as e:
            print("[Startup ERROR] Failed to automatically build the frontend.")
            print("[Startup DIAGNOSTIC] Please ensure Node.js is installed and run:")
            print("    cd frontend")
            print("    npm install")
            print("    npm run build")
            print(f"    Error detail: {e}")
            raise RuntimeError("Frontend build missing and rebuild failed.") from e

if os.path.exists(dist_path):
    # Mount assets folder explicitly
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    # Explicit route for favicon.ico
    @app.get("/favicon.ico", include_in_schema=False)
    def get_favicon():
        favicon_path = os.path.join(dist_path, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        return Response(status_code=404)

    # Catch-all route for SPA router fallback (React Router history mode)
    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        # Exclude API endpoints and WebSocket endpoints
        if catchall.startswith("api/") or catchall.startswith("ws/"):
            return Response(content='{"detail":"Not Found"}', media_type="application/json", status_code=404)

        # Check if the requested file exists in dist_path
        file_path = os.path.join(dist_path, catchall)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise serve React's index.html
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

        return HTMLResponse(
            content="<h1>Frontend build not found!</h1><p>Please compile the frontend dashboard by running <code>npm run build</code> in the frontend folder.</p>",
            status_code=404
        )
else:
    @app.get("/{catchall:path}")
    async def serve_missing_error(catchall: str):
        if catchall.startswith("api/") or catchall.startswith("ws/"):
            return Response(content='{"detail":"Not Found"}', media_type="application/json", status_code=404)
        return HTMLResponse(
            content="<h1>Frontend build not found!</h1><p>Please compile the frontend dashboard by running <code>npm run build</code> in the frontend folder.</p>",
            status_code=404
        )
