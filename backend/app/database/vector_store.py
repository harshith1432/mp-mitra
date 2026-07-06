"""
MP MITRA — Vector Store Builder
==============================
Initializes the ChromaDB local vector store and indexes all database schemes, news, and tenders.
Runs in a background thread to prevent blocking startup.
"""
import os
import threading
from app.database.connection import SessionLocal
from app.database.models import CrawledScheme, CrawledNews, CrawledTender
from app.agents.rag_agent import index_document


def rebuild_vector_store():
    """Indexes all structured PostgreSQL tables into ChromaDB for semantic search."""
    def _bg_indexing():
        print("[Vector Store] Starting background RAG indexing of all crawled sources...")
        db = SessionLocal()
        count = 0
        try:
            # 1. Index Schemes
            schemes = db.query(CrawledScheme).all()
            for s in schemes:
                doc_id = f"scheme_{s.id}"
                content = f"Scheme Title: {s.title}\nMinistry: {s.ministry}\nCategory: {s.category}\nDescription: {s.description}\nEligibility: Age {s.eligibility_age_min}-{s.eligibility_age_max}, Gender: {s.eligibility_gender}, State: {s.eligibility_state}"
                metadata = {
                    "type": "scheme",
                    "title": s.title,
                    "state": s.eligibility_state,
                    "ministry": s.ministry,
                    "source_url": s.link
                }
                index_document(doc_id, content, metadata)
                count += 1

            # 2. Index Tenders
            tenders = db.query(CrawledTender).all()
            for t in tenders:
                doc_id = f"tender_{t.id}"
                content = f"Tender Title: {t.title}\nAuthority: {t.authority}\nDistrict: {t.district_name}\nCategory: {t.category}\nCost: {t.cost}\nDeadline: {t.deadline}"
                metadata = {
                    "type": "tender",
                    "title": t.title,
                    "district": t.district_name,
                    "state": "KARNATAKA",  # Default state for Mandya tenders
                    "source_url": t.link
                }
                index_document(doc_id, content, metadata)
                count += 1

            # 3. Index News
            news_items = db.query(CrawledNews).all()
            for n in news_items:
                doc_id = f"news_{n.id}"
                content = f"News Title: {n.title}\nSource: {n.source}\nDistrict: {n.district_name}\nSummary: {n.summary}"
                metadata = {
                    "type": "news",
                    "title": n.title,
                    "district": n.district_name,
                    "source_url": n.link
                }
                index_document(doc_id, content, metadata)
                count += 1

            print(f"[Vector Store] Background indexing complete. Indexed {count} documents into ChromaDB.")
        except Exception as e:
            print(f"[Vector Store Indexing Error] {e}")
        finally:
            db.close()

    # Run in background thread to keep startup fast
    threading.Thread(target=_bg_indexing, daemon=True).start()
