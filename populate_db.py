import json
import sqlite3
import urllib.request
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
import time
from datetime import datetime

# Configurations
CANDIDATES_JSONL = os.environ.get("CANDIDATES_JSONL", r"c:\Users\bhave\Desktop\The Data & AI Challenge\dataset\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl")
SQLITE_DB = os.environ.get("SQLITE_DB", r"c:\Users\bhave\Desktop\The Data & AI Challenge\embeddings.db")
FLASK_EMBED_URL = f"http://{os.environ.get('ML_HOST', 'localhost')}:{os.environ.get('ML_PORT', '5000')}/embed-bulk"

# Postgres Configurations
PG_PORT = int(os.environ.get("DB_PORT", 5432))
PG_DB = os.environ.get("DB_NAME", "ranking_db")
PG_USER = os.environ.get("DB_USER", "postgres")
PG_PASSWORD = os.environ.get("DB_PASSWORD", "password")

def resolve_pg_host():
    env_host = os.environ.get("DB_HOST")
    if env_host:
        return env_host
        
    import socket
    # Try localhost first
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(("localhost", PG_PORT))
        s.close()
        return "localhost"
    except Exception:
        pass
        
    # Try getting WSL IP address
    try:
        import subprocess
        result = subprocess.run(["wsl", "hostname", "-I"], capture_output=True, text=True)
        ips = result.stdout.strip().split()
        for ip in ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((ip, PG_PORT))
                s.close()
                print(f"Detected PostgreSQL running inside WSL at IP: {ip}")
                return ip
            except Exception:
                pass
    except Exception:
        pass
        
    # Fallback to localhost
    return "localhost"

PG_HOST = resolve_pg_host()

def check_anomaly_flags(c):
    expert_zero_dur = sum(1 for s in c.get('skills', []) if s.get('proficiency') == 'expert' and s.get('duration_months', 0) == 0)
    impossible_skills = 1 if expert_zero_dur >= 5 else 0
    
    timeline_invalid = 0
    company_age_invalid = 0
    for job in c.get('career_history', []):
        company = job.get("company", "")
        start_str = job.get('start_date')
        end_str = job.get('end_date')
        dur = job.get('duration_months', 0)
        if start_str:
            try:
                start_dt = datetime.strptime(start_str, '%Y-%m-%d')
                end_dt = datetime.strptime(end_str, '%Y-%m-%d') if end_str else datetime(2026, 6, 29)
                actual_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                if abs(dur - actual_months) > 24:
                    timeline_invalid = 1
            except ValueError:
                pass
                
        if "Redrob" in company and dur > 36:
            company_age_invalid = 1
            
    profile_exp = c.get('profile', {}).get('years_of_experience', 0.0)
    history_exp = sum(j.get('duration_months', 0) for j in c.get('career_history', [])) / 12.0
    exp_discrepancy = 1 if abs(profile_exp - history_exp) > 5.0 else 0
    
    education_invalid = 0
    grad_years = [edu.get("end_year") for edu in c.get("education", []) if edu.get("end_year")]
    if grad_years:
        min_grad = min(grad_years)
        for job in c.get("career_history", []):
            start_str = job.get("start_date")
            if start_str:
                try:
                    start_year = datetime.strptime(start_str, "%Y-%m-%d").year
                    if min_grad - start_year > 6:
                        education_invalid = 1
                except ValueError:
                    pass
    
    return timeline_invalid, impossible_skills, exp_discrepancy, company_age_invalid, education_invalid

def check_anti_patterns(c):
    history = c.get('career_history', [])
    skills = [s.get('name', '').lower() for s in c.get('skills', [])]
    
    # 1. Consulting-only
    consulting_firms = ["tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant", "capgemini", "tech mahindra", "hcl", "lti", "l&t infotech", "mindtree", "deloitte", "pwc", "ey", "ernst & young", "kpmg"]
    is_consulting_only = 0
    if len(history) > 0:
        all_consulting = True
        for job in history:
            company = job.get('company', '').lower()
            if not any(firm in company for firm in consulting_firms):
                all_consulting = False
                break
        if all_consulting:
            is_consulting_only = 1
            
    # 2. Research-only
    is_research_only = 0
    if len(history) > 0:
        all_research = True
        for job in history:
            title = job.get('title', '').lower()
            is_eng_title = any(t in title for t in ["engineer", "developer", "programmer", "architect", "lead", "analyst", "manager", "data scientist", "ml scientist", "consultant", "specialist"])
            is_res_title = any(t in title for t in ["researcher", "postdoc", "phd", "fellow", "professor", "lecturer", "academic"])
            if not is_res_title or is_eng_title:
                all_research = False
                break
        if all_research:
            is_research_only = 1
            
    # 3. Title chaser
    is_title_chaser = 0
    if len(history) >= 2:
        total_months = sum(job.get('duration_months', 0) for job in history)
        avg_months = total_months / len(history)
        if avg_months < 18:
            is_title_chaser = 1
            
    # 4. LangChain-only
    is_langchain_only = 0
    has_lc_or_openai = any(s in skills for s in ["langchain", "openai", "gpt-4", "gpt", "llamaindex"])
    has_core_ml = any(s in skills for s in ["pytorch", "tensorflow", "scikit-learn", "xgboost", "keras", "pandas", "numpy", "scipy", "machine learning", "deep learning", "nlp"])
    if has_lc_or_openai and not has_core_ml:
        is_langchain_only = 1
        
    return is_consulting_only, is_research_only, is_title_chaser, is_langchain_only

def is_tech_profile(c):
    profile = c.get('profile', {})
    title = profile.get('current_title', '').lower()
    headline = profile.get('headline', '').lower()
    title_headline = f"{title} {headline}"
    
    exclude_keywords = ["hr ", " hr", "recruiter", "talent acquisition", "sales", "marketing", "mechanical", "civil", "electrical", "chemical", "business analyst", "product manager", "project manager", "scrum", "finance", "operations", "writer", "accountant", "designer", "content"]
    if any(k in title_headline for k in exclude_keywords):
        return False
        
    tech_keywords = ["engineer", "developer", "architect", "scientist", "programmer", "lead", "specialist"]
    return any(t in title_headline for t in tech_keywords)

def should_sync_candidate(c, index):
    profile = c.get('profile', {})
    years_exp = float(profile.get('years_of_experience', 0.0))
    
    # Check experience range (allowing up to 15 years as per JD flexibility)
    if not (4.0 <= years_exp <= 15.0):
        return False
        
    # Check anomalies
    timeline_invalid, impossible_skills, exp_discrepancy, company_age_invalid, education_invalid = check_anomaly_flags(c)
    if timeline_invalid or impossible_skills or exp_discrepancy or company_age_invalid or education_invalid:
        return False
        
    if not is_tech_profile(c):
        return False
        
    # Check title/headline/skills/career history keywords
    headline = profile.get('headline', '').lower()
    current_title = profile.get('current_title', '').lower()
    title_headline = f"{current_title} {headline}"
    
    skills = [s.get('name', '').lower() for s in c.get('skills', [])]
    skills_str = " ".join(skills)
    
    history_desc = ' '.join([j.get('description', '').lower() + ' ' + j.get('title', '').lower() for j in c.get('career_history', [])])
    search_str = f"{title_headline} {skills_str} {history_desc}"
    
    tech_keywords = ["engineer", "developer", "architect", "scientist", "programmer", "lead", "specialist"]
    if not any(t in title_headline for t in tech_keywords) and not any(t in skills_str for t in tech_keywords) and not any(t in history_desc for t in tech_keywords):
        return False
        
    ai_keywords = ["ai", "ml", "machine learning", "deep learning", "nlp", "neural", "search", "retrieval", "rag", "pytorch", "tensorflow", "xgboost", "learning to rank", "recommend", "data scientist", "embeddings", "vector"]
    if any(k in search_str for k in ai_keywords):
        return True
        
    return False

# Batch sizes
EMBED_BATCH_SIZE = 128
DB_BATCH_SIZE = 250
MAX_CANDIDATES = 100000  # Process full pool

def init_sqlite():
    print(f"Initializing SQLite cache at {SQLITE_DB}...")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_embeddings (
            candidate_id TEXT PRIMARY KEY,
            embedding BLOB
        )
    """)
    conn.commit()
    return conn

def get_cached_embeddings(sqlite_conn, candidate_ids):
    cursor = sqlite_conn.cursor()
    placeholders = ",".join("?" for _ in candidate_ids)
    cursor.execute(f"SELECT candidate_id, embedding FROM candidate_embeddings WHERE candidate_id IN ({placeholders})", candidate_ids)
    rows = cursor.fetchall()
    
    cached = {}
    for row in rows:
        cid, emb_bytes = row[0], row[1]
        emb = np_from_bytes(emb_bytes)
        cached[cid] = emb
    return cached

def save_embeddings_to_sqlite(sqlite_conn, embeddings_dict):
    cursor = sqlite_conn.cursor()
    batch = []
    for cid, emb in embeddings_dict.items():
        emb_bytes = np_to_bytes(emb)
        batch.append((cid, emb_bytes))
    cursor.executemany("INSERT OR REPLACE INTO candidate_embeddings (candidate_id, embedding) VALUES (?, ?)", batch)
    sqlite_conn.commit()

def np_to_bytes(float_list):
    return import_numpy().array(float_list, dtype=import_numpy().float32).tobytes()

def np_from_bytes(blob_bytes):
    return import_numpy().frombuffer(blob_bytes, dtype=import_numpy().float32).tolist()

_numpy = None
def import_numpy():
    global _numpy
    if _numpy is None:
        import numpy
        _numpy = numpy
    return _numpy

def fetch_embeddings_from_flask(texts):
    try:
        data = json.dumps({"texts": texts}).encode('utf-8')
        req = urllib.request.Request(
            FLASK_EMBED_URL, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['embeddings']
    except Exception as e:
        print(f"Error fetching embeddings from Flask: {e}")
        sys.exit(1)

def construct_profile_text(c):
    profile = c.get('profile', {})
    headline = profile.get('headline', '')
    summary = profile.get('summary', '')
    skills = ", ".join([s['name'] for s in c.get('skills', [])])
    current_title = profile.get('current_title', '')
    current_company = profile.get('current_company', '')
    return f"Title: {current_title} at {current_company}. Headline: {headline}. Summary: {summary}. Skills: {skills}."

def get_postgres_conn():
    print(f"Connecting to PostgreSQL at {PG_HOST}:{PG_PORT}...")
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
        print("Please verify the Docker container is running and port 5432 is exposed.")
        sys.exit(1)

def main():
    if not os.path.exists(CANDIDATES_JSONL):
        print(f"Candidates file not found at: {CANDIDATES_JSONL}")
        sys.exit(1)
        
    sqlite_conn = init_sqlite()
    pg_conn = get_postgres_conn()
    
    # Enable autocommit for standard bulk inserting or manage transactions manually
    pg_conn.autocommit = False
    pg_cursor = pg_conn.cursor()
    
    print("Clearing existing candidates in PostgreSQL table...")
    pg_cursor.execute("TRUNCATE TABLE candidates;")
    pg_conn.commit()
    
    print("Reading and filtering candidates profiles. Preparing sync pipeline...")
    candidates = []
    
    with open(CANDIDATES_JSONL, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= MAX_CANDIDATES:
                break
            c = json.loads(line)
            if should_sync_candidate(c, idx):
                candidates.append(c)
            
    total_candidates = len(candidates)
    print(f"Total profiles matched and loaded: {total_candidates}")
    
    start_time = time.time()
    
    # Process candidates in batches for SQLite cache retrieval and Flask embeddings generation
    for i in range(0, total_candidates, DB_BATCH_SIZE):
        batch = candidates[i:i+DB_BATCH_SIZE]
        batch_ids = [c['candidate_id'] for c in batch]
        
        # 1. Check SQLite Cache
        cached_embs = get_cached_embeddings(sqlite_conn, batch_ids)
        
        # Determine which candidates need embeddings computed
        uncached_batch = [c for c in batch if c['candidate_id'] not in cached_embs]
        
        if uncached_batch:
            # We have uncached candidates. Compute embeddings in sub-batches
            uncached_texts = [construct_profile_text(c) for c in uncached_batch]
            uncached_ids = [c['candidate_id'] for c in uncached_batch]
            
            computed_embs = []
            for j in range(0, len(uncached_texts), EMBED_BATCH_SIZE):
                sub_texts = uncached_texts[j:j+EMBED_BATCH_SIZE]
                print(f"Computing embeddings for {len(sub_texts)} candidates (range {i+j} to {i+j+len(sub_texts)})...")
                sub_embs = fetch_embeddings_from_flask(sub_texts)
                computed_embs.extend(sub_embs)
            
            # Map back to IDs
            new_embs_dict = dict(zip(uncached_ids, computed_embs))
            
            # Save to SQLite Cache
            save_embeddings_to_sqlite(sqlite_conn, new_embs_dict)
            
            # Merge with cached
            cached_embs.update(new_embs_dict)
            
        # 2. Insert Batch into PostgreSQL
        pg_batch = []
        for c in batch:
            cid = c['candidate_id']
            profile = c.get('profile', {})
            name = profile.get('anonymized_name', '')
            years_exp = float(profile.get('years_of_experience', 0.0))
            
            # Engagement velocity signal
            completeness = float(c.get('redrob_signals', {}).get('profile_completeness_score', 0.0))
            
            # Intent signal
            open_to_work = 1.0 if c.get('redrob_signals', {}).get('open_to_work_flag', False) else 0.0
            
            resume_text = construct_profile_text(c)
            
            # Anomaly checks (honeypots)
            timeline_invalid, impossible_skills, exp_discrepancy, company_age_invalid, education_invalid = check_anomaly_flags(c)
            
            # Anti-patterns
            is_consulting_only, is_research_only, is_title_chaser, is_langchain_only = check_anti_patterns(c)
            
            # Notice period & Location
            notice_period = int(c.get('redrob_signals', {}).get('notice_period_days', 0))
            willing_to_relocate = bool(c.get('redrob_signals', {}).get('willing_to_relocate', False))
            location = profile.get('location', '')
            
            # Get embedding vector (list of floats)
            emb = cached_embs[cid]
            emb_str = "[" + ",".join(str(v) for v in emb) + "]"
            
            pg_batch.append((cid, name, years_exp, completeness, open_to_work, resume_text,
                             timeline_invalid, impossible_skills, exp_discrepancy,
                             education_invalid, company_age_invalid,
                             is_consulting_only, is_research_only, is_title_chaser, is_langchain_only,
                             notice_period, willing_to_relocate, location, emb_str))
            
        # Execute batch insert into PostgreSQL
        query = """
            INSERT INTO candidates (
                id, name, years_experience, activity_score, intent_score, resume_text,
                is_timeline_invalid, impossible_skills_ratio, experience_discrepancy,
                is_education_invalid, is_company_age_invalid,
                is_consulting_only, is_research_only, is_title_chaser, is_langchain_only,
                notice_period, willing_to_relocate, location, embedding
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, CAST(%s AS vector)
            )
        """
        pg_cursor.executemany(query, pg_batch)
        pg_conn.commit()
        
        elapsed = time.time() - start_time
        avg_speed = (i + len(batch)) / elapsed
        eta = (total_candidates - (i + len(batch))) / avg_speed if avg_speed > 0 else 0
        print(f"Synced {i + len(batch)}/{total_candidates} candidates to PostgreSQL. Speed: {avg_speed:.1f} candidates/sec. ETA: {eta/60:.1f} mins.")

    sqlite_conn.close()
    pg_conn.close()
    print(f"Database population successfully completed in {time.time() - start_time:.1f} seconds.")

if __name__ == '__main__':
    main()
