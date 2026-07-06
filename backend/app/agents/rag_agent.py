"""
MP MITRA — RAG Agent & Vector Store Manager
===========================================
Handles semantic search against crawled schemes, news, and tenders.
Uses ChromaDB for zero-config local storage, with graceful SQL fallback.
"""
import os
import requests
from typing import List, Dict, Any, Optional

try:
    import chromadb
    _chroma_available = True
except ImportError:
    _chroma_available = False

try:
    from sentence_transformers import SentenceTransformer
    _transformer_available = True
except ImportError:
    _transformer_available = False


# Cache the embedding model
_embedding_model = None

def _get_embedding(text: str) -> List[float]:
    """Generate vector embedding (384-dim)."""
    global _embedding_model
    if not _transformer_available:
        # Fallback to deterministic pseudo-embedding on missing packages
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        emb = []
        for i in range(384):
            idx = (i * 2) % len(h)
            emb.append(float(h[idx]) / 255.0 - 0.5)
        return emb

    if _embedding_model is None:
        print("[RAG Agent] Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
    return _embedding_model.encode(text).tolist()


# ═══════════════════════════════════════════════════════════════════════════════
# CHROMA INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

_chroma_client = None
_collection = None

def _get_chroma_collection():
    global _chroma_client, _collection
    if not _chroma_available:
        return None
    if _collection is None:
        try:
            # Persistent client in the app data directory or local database folder
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "chroma_db")
            _chroma_client = chromadb.PersistentClient(path=db_path)
            _collection = _chroma_client.get_or_create_collection("mp_mitra_knowledge")
        except Exception as e:
            print(f"[RAG Agent] Chroma init error: {e}")
            return None
    return _collection


# ═══════════════════════════════════════════════════════════════════════════════
# INDEXING HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def index_document(doc_id: str, content: str, metadata: Dict[str, Any]):
    """Index a single document into the vector store."""
    coll = _get_chroma_collection()
    if coll:
        try:
            vector = _get_embedding(content)
            # Ensure metadata has string keys and simple values
            cleaned_meta = {}
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    cleaned_meta[k] = v
                else:
                    cleaned_meta[k] = str(v)
            coll.add(
                ids=[doc_id],
                embeddings=[vector],
                metadatas=[cleaned_meta],
                documents=[content]
            )
        except Exception as e:
            print(f"[RAG Agent] Indexing failed for {doc_id}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE SEARCH (RAG)
# ═══════════════════════════════════════════════════════════════════════════════

def search_knowledge_base(query: str, state: str = "", district: str = "", k: int = 4) -> List[Dict[str, Any]]:
    """
    Search indexed government schemes, news, and tenders for matching documents.
    """
    coll = _get_chroma_collection()
    if not coll:
        # Fallback 1: Database keyword lookup via SQL if Chroma is missing
        print("[RAG Agent] Chroma unavailable. Falling back to SQL database keyword matching...")
        return _search_sql_fallback(query, state, district, k)

    try:
        query_vector = _get_embedding(query)
        
        # Build metadata filters
        where_filter = {}
        if state:
            where_filter["state"] = state.upper()
            
        results = coll.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where_filter if where_filter else None
        )
        
        docs = []
        if results and "documents" in results and results["documents"]:
            for i in range(len(results["documents"][0])):
                docs.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": results["distances"][0][i] if "distances" in results else 1.0,
                    "source_url": results["metadatas"][0][i].get("source_url") or results["metadatas"][0][i].get("link", "")
                })
        return docs
    except Exception as e:
        print(f"[RAG Agent Query Error] {e}. Falling back to SQL...")
        return _search_sql_fallback(query, state, district, k)


def _search_sql_fallback(query: str, state: str = "", district: str = "", k: int = 4) -> List[Dict[str, Any]]:
    """Query crawled data in PostgreSQL using direct text search."""
    from app.database.connection import SessionLocal
    from app.database.models import CrawledScheme, CrawledNews
    
    db = SessionLocal()
    results = []
    
    try:
        # Search schemes
        q_words = [w for w in query.lower().split() if len(w) > 3]
        scheme_query = db.query(CrawledScheme)
        if state:
            scheme_query = scheme_query.filter(
                (CrawledScheme.eligibility_state == "ALL") | 
                (CrawledScheme.eligibility_state == state.upper())
            )
        schemes = scheme_query.limit(20).all()
        
        # Rank by matching keywords
        scored_schemes = []
        for s in schemes:
            score = 0
            desc = (s.description or "").lower()
            title = s.title.lower()
            for w in q_words:
                if w in title: score += 5
                if w in desc: score += 1
            if score > 0 or not q_words:
                scored_schemes.append((score, s))
                
        scored_schemes.sort(key=lambda x: x[0], reverse=True)
        
        for _, s in scored_schemes[:k]:
            results.append({
                "content": f"Scheme Name: {s.title}\nMinistry: {s.ministry}\nCategory: {s.category}\nEligibility: Age {s.eligibility_age_min}-{s.eligibility_age_max}, Gender: {s.eligibility_gender}, State: {s.eligibility_state}\nDescription: {s.description}",
                "metadata": {"type": "scheme", "title": s.title, "source_url": s.link},
                "source_url": s.link
            })
            
    except Exception as e:
        print(f"[SQL Fallback Error] {e}")
    finally:
        db.close()
        
    return results
