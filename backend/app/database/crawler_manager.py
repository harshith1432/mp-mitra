"""
MP MITRA — Crawler Manager
===========================
Manages the lifecycle (start / stop / status) of the web scraper.
Emits real-time structured log events that WebSocket clients can subscribe to.
"""

import asyncio
import threading
import time
import uuid
from datetime import datetime
from typing import Optional
from collections import deque

# ─── Global crawler state ─────────────────────────────────────────────────────

class CrawlerManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._current_stage = "idle"
        self._thread: Optional[threading.Thread] = None
        self._run_id: Optional[str] = None
        self._started_at: Optional[str] = None
        self._items_added = 0
        self._items_scanned = 0
        
        self._total_schemes = 0
        self._total_news = 0
        self._total_tenders = 0
        self._schemes_added_run = 0
        self._news_added_run = 0
        self._tenders_added_run = 0

        # Ring buffer of last 500 log lines (for late-joining clients)
        self._log_buffer: deque = deque(maxlen=500)

        # Set of asyncio Queues — one per connected WebSocket client
        self._subscribers: set = set()
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    # ── Subscription management ──────────────────────────────────────────────
    def attach_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._event_loop = loop

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        with self._lock:
            self._subscribers.discard(q)

    def _broadcast(self, event: dict):
        """Called from crawler thread — thread-safe push to all subscriber queues."""
        with self._lock:
            self._log_buffer.append(event)
            dead = set()
            for q in self._subscribers:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.add(q)
            self._subscribers -= dead

    def emit(self, level: str, stage: str, message: str, url: str = "", data: dict = None):
        """Emit a structured log event to all live WebSocket subscribers."""
        event = {
            "id": str(uuid.uuid4())[:8],
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,       # INFO | SUCCESS | WARNING | ERROR | DATA | SYSTEM
            "stage": stage,
            "message": message,
            "url": url,
            "data": data or {},
            "stats": {
                "total_schemes": self._total_schemes,
                "total_tenders": self._total_tenders,
                "total_news": self._total_news,
                "items_scanned": self._items_scanned,
                "items_added": self._items_added,
                "schemes_added_run": self._schemes_added_run,
                "news_added_run": self._news_added_run,
                "tenders_added_run": self._tenders_added_run
            }
        }
        self._broadcast(event)

    def increment_scanned(self, amount=1):
        with self._lock:
            self._items_scanned += amount

    def increment_schemes(self, new_stored=True):
        with self._lock:
            if new_stored:
                self._total_schemes += 1
            self._schemes_added_run += 1
            self._items_added += 1

    def increment_news(self, new_stored=True):
        with self._lock:
            if new_stored:
                self._total_news += 1
            self._news_added_run += 1
            self._items_added += 1

    def increment_tenders(self, new_stored=True):
        with self._lock:
            if new_stored:
                self._total_tenders += 1
            self._tenders_added_run += 1
            self._items_added += 1

    def initialize_total_counts(self, db):
        from app.database.models import CrawledScheme, CrawledNews, CrawledTender
        with self._lock:
            self._total_schemes = db.query(CrawledScheme).count()
            self._total_news = db.query(CrawledNews).count()
            self._total_tenders = db.query(CrawledTender).count()

    # ── Status ───────────────────────────────────────────────────────────────
    def status(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "current_stage": self._current_stage,
                "run_id": self._run_id,
                "started_at": self._started_at,
                "items_added": self._items_added,
                "items_scanned": self._items_scanned,
                "schemes_added_run": self._schemes_added_run,
                "news_added_run": self._news_added_run,
                "tenders_added_run": self._tenders_added_run,
                "total_schemes": self._total_schemes,
                "total_news": self._total_news,
                "total_tenders": self._total_tenders,
                "log_buffer_size": len(self._log_buffer),
            }

    def get_log_buffer(self):
        with self._lock:
            return list(self._log_buffer)

    # ── Start ────────────────────────────────────────────────────────────────
    def start(self, db_session_factory) -> dict:
        with self._lock:
            if self._running:
                return {"ok": False, "reason": "Crawler already running"}
            self._running = True
            self._run_id = str(uuid.uuid4())[:12]
            self._started_at = datetime.now().isoformat()
            self._items_added = 0
            self._items_scanned = 0
            self._schemes_added_run = 0
            self._news_added_run = 0
            self._tenders_added_run = 0
            self._current_stage = "starting"

        self._thread = threading.Thread(
            target=self._run_loop,
            args=(db_session_factory,),
            daemon=True,
            name="CrawlerThread"
        )
        self._thread.start()
        return {"ok": True, "run_id": self._run_id}

    # ── Stop ─────────────────────────────────────────────────────────────────
    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"ok": False, "reason": "Crawler not running"}
            self._running = False
            self._current_stage = "stopping"
        self.emit("WARNING", "SYSTEM", "⛔ Admin requested STOP. Crawler will halt after current stage.")
        return {"ok": True}

    # ── Internal crawler loop ────────────────────────────────────────────────
    def _run_loop(self, db_session_factory):
        from app.database.crawler_service import INDIA_STATES_DISTRICTS, NATIONAL_SCHEMES
        from app.database.crawler_rt_stages import (
            load_national_schemes_rt,
            load_all_district_news_rt,
            load_all_district_tenders_rt,
            scrape_pib_feeds_rt,
            scrape_myscheme_portal_rt,
        )
        from app.database.models import CrawlerLog, CrawledScheme, CrawledNews, CrawledTender

        total_districts = sum(len(v["districts"]) for v in INDIA_STATES_DISTRICTS.values())
        total_states = len(INDIA_STATES_DISTRICTS)

        self.emit("SYSTEM", "SYSTEM", "=" * 60)
        self.emit("SYSTEM", "SYSTEM", f"🚀 MP MITRA All-India Crawler Agent started (Continuous Loop Mode)")
        self.emit("SYSTEM", "SYSTEM", f"Run ID: {self._run_id}")
        self.emit("SYSTEM", "SYSTEM", f"Geography: {total_states} States/UTs | {total_districts}+ Districts")
        self.emit("SYSTEM", "SYSTEM", f"Coverage: 2010–{datetime.now().year} + Live PIB Feeds")
        self.emit("SYSTEM", "SYSTEM", "=" * 60)

        db = db_session_factory()
        self.initialize_total_counts(db)
        items_count = 0
        start_time = datetime.now()

        try:
            loop_idx = 1
            while self._running:
                self.emit("SYSTEM", "SYSTEM", f"\n🔄 Starting Crawl Loop #{loop_idx}...")

                # ── Stage 1 ──────────────────────────────────────────────────────
                if not self._running: break
                with self._lock: self._current_stage = "stage1"
                self.emit("INFO", "Stage 1", f"📚 Loading national + state scheme registry ({len(NATIONAL_SCHEMES)} schemes)...")
                n = load_national_schemes_rt(db, self)
                items_count += n
                with self._lock: self._items_added = items_count

                # ── Stage 2 ──────────────────────────────────────────────────────
                if not self._running: break
                with self._lock: self._current_stage = "stage2"
                self.emit("INFO", "Stage 2", f"📰 Generating district news for ALL {total_districts} districts...")
                n = load_all_district_news_rt(db, self)
                items_count += n
                with self._lock: self._items_added = items_count

                # ── Stage 3 ──────────────────────────────────────────────────────
                if not self._running: break
                with self._lock: self._current_stage = "stage3"
                self.emit("INFO", "Stage 3", f"🏗️ Generating infrastructure tenders for ALL {total_districts} districts...")
                n = load_all_district_tenders_rt(db, self)
                items_count += n
                with self._lock: self._items_added = items_count

                # ── Stage 4 ──────────────────────────────────────────────────────
                if not self._running: break
                with self._lock: self._current_stage = "stage4"
                self.emit("INFO", "Stage 4", "📡 Scraping live PIB press release feeds...")
                n = scrape_pib_feeds_rt(db, self)
                items_count += n
                with self._lock: self._items_added = items_count

                # ── Stage 5 ──────────────────────────────────────────────────────
                if not self._running: break
                with self._lock: self._current_stage = "stage5"
                self.emit("INFO", "Stage 5", "🌐 Scanning MyScheme.gov.in for new welfare schemes...")
                n = scrape_myscheme_portal_rt(db, self)
                items_count += n
                with self._lock: self._items_added = items_count

                # Commit after each complete loop iteration
                db.commit()
                self.emit("SUCCESS", "SYSTEM", f"✨ Crawl Loop #{loop_idx} finished successfully. Ingested data committed to DB.")
                loop_idx += 1

                # Rest/wait between loops to avoid CPU spinning
                if self._running:
                    self.emit("SYSTEM", "SYSTEM", "⏳ Sleeping for 15 seconds before starting next loop...")
                    for _ in range(15):
                        if not self._running: break
                        time.sleep(1)

        except Exception as exc:
            self.emit("ERROR", "SYSTEM", f"❌ Unhandled crawler error: {exc}")
        finally:
            self._finish(db, items_count, start_time)

    def _finish(self, db, items_count, start_time):
        from app.database.models import CrawlerLog, CrawledScheme, CrawledNews, CrawledTender
        try:
            db.commit()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            total_schemes = db.query(CrawledScheme).count()
            total_news    = db.query(CrawledNews).count()
            total_tenders = db.query(CrawledTender).count()

            self.emit("SYSTEM", "SYSTEM", "=" * 60)
            self.emit("SUCCESS", "SYSTEM", f"✅ All-India crawl complete in {duration:.1f}s")
            self.emit("DATA", "SYSTEM", f"New records this run: {items_count}")
            self.emit("DATA", "SYSTEM", f"DB → Schemes: {total_schemes} | News: {total_news} | Tenders: {total_tenders}")
            self.emit("SYSTEM", "SYSTEM", "=" * 60)

            db.add(CrawlerLog(
                status="Success" if items_count > 0 else "Idle",
                items_crawled=items_count,
                message=f"Run {self._run_id}: {items_count} items in {duration:.1f}s"
            ))
            db.commit()
        except Exception as e:
            self.emit("ERROR", "SYSTEM", f"DB commit error: {e}")
        finally:
            db.close()
            with self._lock:
                self._running = False
                self._current_stage = "idle"
            self.emit("SYSTEM", "SYSTEM", "🔴 Crawler stopped.")


# ─── Singleton ────────────────────────────────────────────────────────────────
crawler_manager = CrawlerManager()
