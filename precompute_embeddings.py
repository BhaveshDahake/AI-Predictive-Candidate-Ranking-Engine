import json
import sqlite3
import os
import sys
import time
import numpy as np
from sentence_transformers import SentenceTransformer

CANDIDATES_JSONL = r"c:\Users\bhave\Desktop\The Data & AI Challenge\dataset\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
SQLITE_DB = r"c:\Users\bhave\Desktop\The Data & AI Challenge\embeddings.db"
NPZ_OUT = r"c:\Users\bhave\Desktop\The Data & AI Challenge\embeddings.npz"

def construct_profile_text(c):
    profile = c.get('profile', {})
    headline = profile.get('headline', '')
    summary = profile.get('summary', '')
    skills = ", ".join([s['name'] for s in c.get('skills', [])])
    current_title = profile.get('current_title', '')
    current_company = profile.get('current_company', '')
    return f"Title: {current_title} at {current_company}. Headline: {headline}. Summary: {summary}. Skills: {skills}."

def init_sqlite():
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = MEMORY;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_embeddings (
            candidate_id TEXT PRIMARY KEY,
            embedding BLOB
        )
    """)
    conn.commit()
    return conn

def main():
    if not os.path.exists(CANDIDATES_JSONL):
        print(f"Candidates file not found at: {CANDIDATES_JSONL}")
        sys.exit(1)
        
    print("Connecting to SQLite cache...")
    sqlite_conn = init_sqlite()
    cursor = sqlite_conn.cursor()
    
    # 1. Fetch already cached IDs
    print("Fetching cached embedding IDs...")
    cursor.execute("SELECT candidate_id FROM candidate_embeddings")
    cached_ids = set(row[0] for row in cursor.fetchall())
    print(f"Already cached in SQLite: {len(cached_ids)}")
    
    # 2. Read candidates.jsonl and identify uncached ones
    print("Reading candidates JSONL file...")
    uncached_batch = []
    
    start_read = time.time()
    with open(CANDIDATES_JSONL, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c['candidate_id']
            if cid not in cached_ids:
                uncached_batch.append((cid, construct_profile_text(c)))
                
    print(f"Read candidates list in {time.time() - start_read:.2f}s. Found {len(uncached_batch)} uncached candidates.")
    
    # 3. Compute missing embeddings in parallel if any
    if uncached_batch:
        print("Loading SentenceTransformer model all-MiniLM-L6-v2...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Start multi-process pool on 4 CPU workers
        print("Starting multi-process pool (4 workers)...")
        pool = model.start_multi_process_pool(target_devices=['cpu'] * 4)
        
        uncached_texts = [item[1] for item in uncached_batch]
        uncached_ids = [item[0] for item in uncached_batch]
        
        print("Computing embeddings in parallel...")
        start_time = time.time()
        embeddings = model.encode_multi_process(uncached_texts, pool, batch_size=256)
        
        print(f"Computed {len(embeddings)} embeddings in {time.time() - start_time:.2f}s.")
        model.stop_multi_process_pool(pool)
        
        # Write to SQLite in chunks
        print("Saving computed embeddings to SQLite...")
        db_batch = []
        for cid, emb in zip(uncached_ids, embeddings):
            emb_bytes = np.array(emb, dtype=np.float32).tobytes()
            db_batch.append((cid, emb_bytes))
            
        chunk_size = 5000
        for i in range(0, len(db_batch), chunk_size):
            chunk = db_batch[i:i+chunk_size]
            cursor.executemany("INSERT OR REPLACE INTO candidate_embeddings (candidate_id, embedding) VALUES (?, ?)", chunk)
            sqlite_conn.commit()
            print(f"Saved {i + len(chunk)}/{len(db_batch)} embeddings to database.")
            
    # 4. Load all 100,000 embeddings and export to NPZ
    print("Loading all embeddings from SQLite to export to NumPy NPZ...")
    cursor.execute("SELECT candidate_id, embedding FROM candidate_embeddings")
    rows = cursor.fetchall()
    
    candidate_ids_ints = []
    embeddings_list = []
    
    for row in rows:
        cid_str = row[0]
        emb_bytes = row[1]
        
        # Parse candidate_id to integer (e.g. CAND_0000001 -> 1)
        cid_int = int(cid_str.split('_')[1])
        emb = np.frombuffer(emb_bytes, dtype=np.float32).tolist()
        
        candidate_ids_ints.append(cid_int)
        embeddings_list.append(emb)
        
    ids = np.array(candidate_ids_ints, dtype=np.int32)
    embs = np.array(embeddings_list, dtype=np.float16)  # Store as float16 to save space
    
    print(f"Saving {len(ids)} embeddings to {NPZ_OUT}...")
    np.savez_compressed(NPZ_OUT, ids=ids, embs=embs)
    print("Export completed successfully!")
    
    sqlite_conn.close()

if __name__ == '__main__':
    main()
