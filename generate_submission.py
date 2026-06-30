import json
import csv
import urllib.request
import psycopg2
import os
import sys

# Configurations
JD_FILE = os.environ.get("JD_FILE", r"c:\Users\bhave\Desktop\The Data & AI Challenge\dataset\job_description.txt")
OUTPUT_CSV = os.environ.get("OUTPUT_CSV", r"c:\Users\bhave\Desktop\The Data & AI Challenge\team_antigravity.csv")
FLASK_EMBED_URL = f"http://{os.environ.get('ML_HOST', 'localhost')}:{os.environ.get('ML_PORT', '5000')}/embed"
FLASK_RANK_URL = f"http://{os.environ.get('ML_HOST', 'localhost')}:{os.environ.get('ML_PORT', '5000')}/rank"

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
                return ip
            except Exception:
                pass
    except Exception:
        pass
        
    return "localhost"

PG_HOST = resolve_pg_host()

def get_job_description():
    if not os.path.exists(JD_FILE):
        print(f"Job Description file not found at: {JD_FILE}")
        sys.exit(1)
    with open(JD_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def fetch_jd_embedding(jd_text):
    try:
        data = json.dumps({"text": jd_text}).encode('utf-8')
        req = urllib.request.Request(
            FLASK_EMBED_URL, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['embedding'], res_data['required_experience']
    except Exception as e:
        print(f"Error fetching JD embedding from Flask: {e}")
        sys.exit(1)

def fetch_ltr_rankings(candidates_list):
    try:
        data = json.dumps({"candidates": candidates_list}).encode('utf-8')
        req = urllib.request.Request(
            FLASK_RANK_URL, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['ranked_candidates']
    except Exception as e:
        print(f"Error fetching LTR rankings from Flask: {e}")
        sys.exit(1)

def main():
    print("Reading job description...")
    jd_text = get_job_description()
    
    print("Vectorizing job description and extracting experience requirements...")
    embedding, required_experience = fetch_jd_embedding(jd_text)
    print(f"Extracted experience required midpoint: {required_experience} years")
    
    # Format embedding as vector string
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    
    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL at {PG_HOST}...")
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cursor = conn.cursor()
    
    # Retrieve top candidates by vector similarity
    print("Retrieving candidate matches using pgvector cosine similarity index search...")
    query = """
        SELECT id, name, years_experience, activity_score, intent_score, resume_text,
               is_timeline_invalid, impossible_skills_ratio, experience_discrepancy,
               is_education_invalid, is_company_age_invalid,
               is_consulting_only, is_research_only, is_title_chaser, is_langchain_only,
               notice_period, willing_to_relocate, location,
               1 - (embedding <=> CAST(%s AS vector)) AS semanticScore
        FROM candidates
        ORDER BY embedding <=> CAST(%s AS vector)
        LIMIT 500
    """
    cursor.execute("SET local enable_indexscan = off;")
    cursor.execute(query, (embedding_str, embedding_str))
    rows = cursor.fetchall()
    
    print(f"PostgreSQL returned {len(rows)} potential matches.")
    if len(rows) == 0:
        print("No candidates found in PostgreSQL database.")
        sys.exit(1)
        
    # Map rows to LTR features
    candidates_features = []
    candidates_metadata = {}
    import re
    
    for r in rows:
        (cid, name, years_exp, activity_score, intent_score, resume_text, 
         is_timeline_invalid, impossible_skills_ratio, experience_discrepancy, 
         is_education_invalid, is_company_age_invalid,
         is_consulting_only, is_research_only, is_title_chaser, is_langchain_only,
         notice_period, willing_to_relocate, location, semantic_score) = r
        
        # Calculate experience fit
        exp_fit = years_exp - required_experience
        
        # Calculate location fit
        location_fit = 0.0
        loc_str = location.lower() if location else ""
        if any(city in loc_str for city in ["noida", "pune", "delhi", "ncr", "gurgaon", "hyderabad", "mumbai"]):
            location_fit = 1.0
        elif willing_to_relocate:
            location_fit = 0.5
            
        candidates_metadata[cid] = {
            "name": name,
            "years_experience": years_exp,
            "semantic_score": semantic_score,
            "experience_fit": exp_fit,
            "activity_score": activity_score,
            "intent_score": intent_score,
            "is_timeline_invalid": is_timeline_invalid,
            "impossible_skills_ratio": impossible_skills_ratio,
            "experience_discrepancy": experience_discrepancy,
            "is_education_invalid": is_education_invalid,
            "is_company_age_invalid": is_company_age_invalid,
            "is_consulting_only": is_consulting_only,
            "is_research_only": is_research_only,
            "is_title_chaser": is_title_chaser,
            "is_langchain_only": is_langchain_only,
            "notice_period": notice_period,
            "willing_to_relocate": willing_to_relocate,
            "location": location,
            "resume_text": resume_text
        }
        
        candidates_features.append({
            "candidate_id": cid,
            "semantic_score": semantic_score,
            "experience_fit": exp_fit,
            "activity_score": activity_score,
            "intent_score": intent_score,
            "is_timeline_invalid": is_timeline_invalid,
            "impossible_skills_ratio": impossible_skills_ratio,
            "experience_discrepancy": experience_discrepancy,
            "is_education_invalid": is_education_invalid,
            "is_company_age_invalid": is_company_age_invalid,
            "is_consulting_only": is_consulting_only,
            "is_research_only": is_research_only,
            "is_title_chaser": is_title_chaser,
            "is_langchain_only": is_langchain_only,
            "location_fit": location_fit,
            "notice_period": notice_period
        })
        
    # Get LTR rankings
    print("Scoring candidates features using pre-trained XGBoost LTR model...")
    ranked_results = fetch_ltr_rankings(candidates_features)
    
    # Sort results to be 100% compliant with tie-breaking rules
    # Sort descending by score, and ascending by candidate_id in case of equal scores
    ranked_results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    def generate_reasoning(meta):
        resume_text = meta["resume_text"]
        years_exp = meta["years_experience"]
        
        # Parse title & company
        title_match = re.search(r"Title:\s*(.*?)\s*at\s*(.*?)\.", resume_text)
        current_title = title_match.group(1).strip() if title_match else "Software Engineer"
        
        # Parse skills
        skills_match = re.search(r"Skills:\s*(.*?)\.$", resume_text)
        skills = [s.strip() for s in skills_match.group(1).split(",")] if skills_match else []
        
        # Intersect with target JD keywords
        target_keywords = ["pytorch", "tensorflow", "nlp", "search", "retrieval", "rag", "embeddings", "vector", "xgboost", "learning to rank", "python", "postgresql"]
        matched = [s for s in skills if s.lower() in target_keywords]
        matched_str = ", ".join(matched[:3]) if matched else ""

        loc = meta["location"].lower() if meta["location"] else ""
        is_local = any(city in loc for city in ["noida", "pune", "delhi", "ncr", "gurgaon", "hyderabad", "mumbai"])
        
        # Sentence 1: Profile Fit & Experience
        if meta["is_consulting_only"] == 1:
            s1 = f"Consulting-only background at service companies, but shows {years_exp:.1f} years of relevant tech tenure."
        elif meta["is_research_only"] == 1:
            s1 = f"Background is primarily academic/research-focused. Lacks product deployment experience despite {years_exp:.1f} years experience."
        else:
            s1 = f"{years_exp:.1f} years experience as {current_title} at a product company."
            
        # Sentence 2: Technical Skills Match
        if matched_str:
            s2 = f"Demonstrates hands-on expertise in key search & ML technologies, including {matched_str}."
        else:
            s2 = "Possesses foundational backend capabilities and adjacent technical skills."
            
        # Sentence 3: Relocation / notice period / anomalies
        parts = []
        if is_local:
            parts.append(f"Based in {meta['location']}, ideal for the hybrid cadence.")
        elif meta["willing_to_relocate"]:
            parts.append("Willing to relocate to Noida/Pune.")
        else:
            parts.append("Location is not adjacent and relocation is not indicated.")
            
        if meta["notice_period"] <= 30:
            parts.append(f"Highly available with a {meta['notice_period']}-day notice period.")
        else:
            parts.append(f"Notice period is {meta['notice_period']} days.")
            
        s3 = " ".join(parts)
        
        # Sentence 4: Warnings / Flags
        s4 = ""
        if meta["is_title_chaser"] == 1:
            s4 = "Note: Career history indicates frequent switches (average tenure under 18 months)."
        elif meta["is_langchain_only"] == 1:
            s4 = "AI projects are primarily LangChain-based without custom model design."
            
        reason = f"{s1} {s2} {s3} {s4}".strip()
        return reason

    # Write to CSV
    print(f"Writing top 100 ranked candidates to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank_idx, result in enumerate(ranked_results[:100]):
            rank = rank_idx + 1
            cid = result["candidate_id"]
            score = result["score"]
            
            meta = candidates_metadata[cid]
            reason = generate_reasoning(meta)
            writer.writerow([cid, rank, score, reason])
            
    conn.close()
    print("CSV generation completed successfully.")

if __name__ == '__main__':
    main()
