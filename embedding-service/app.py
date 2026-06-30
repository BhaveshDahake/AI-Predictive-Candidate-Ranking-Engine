from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
import xgboost as xgb
import numpy as np
import pandas as pd
import os
import re

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "message": "Flask ML Service is running."})

# Load SentenceTransformer model
print("Loading sentence-transformers/all-MiniLM-L6-v2...")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# Load XGBoost model
model_path = os.path.join(os.path.dirname(__file__), 'model.json')
xgb_model = xgb.XGBRegressor()

if os.path.exists(model_path):
    print(f"Loading pre-trained LTR model from {model_path}...")
    xgb_model.load_model(model_path)
else:
    print("No LTR model found. Training LTR model dynamically...")
    from train_xgboost import train_model
    train_model()
    xgb_model.load_model(model_path)

def extract_required_experience(text):
    if not text:
        return 7.0
        
    # Look for range like "5-9 years" or "5 to 9 years" or "5–9 years" (Unicode dash)
    range_match = re.search(r'(\d+)\s*(?:-|–|to)\s*(\d+)\s*years?', text, re.IGNORECASE)
    if range_match:
        min_exp = float(range_match.group(1))
        max_exp = float(range_match.group(2))
        mid_exp = (min_exp + max_exp) / 2.0
        print(f"Extracted experience range: {min_exp}-{max_exp} years (midpoint: {mid_exp})")
        return mid_exp
        
    # Look for "X+ years" or "at least X years"
    plus_match = re.search(r'(?:at least|minimum|required)?\s*(\d+)\+?\s*years?', text, re.IGNORECASE)
    if plus_match:
        val = float(plus_match.group(1))
        print(f"Extracted experience minimum: {val}+ years")
        return val
        
    # Default fallback is 7.0 years
    print("No experience pattern found in JD, using default midpoint: 7.0 years")
    return 7.0

@app.route('/embed', methods=['POST'])
def embed():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' parameter"}), 400
            
        text = data['text']
        print(f"Vectorizing job description/text (length: {len(text)} chars)...")
        
        # Extract experience required
        required_exp = extract_required_experience(text)
        
        # Compute embedding
        embedding = embed_model.encode(text).tolist()
        
        return jsonify({
            "embedding": embedding,
            "required_experience": required_exp
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/embed-bulk', methods=['POST'])
def embed_bulk():
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({"error": "Missing 'texts' parameter"}), 400
            
        texts = data['texts']
        print(f"Bulk vectorizing {len(texts)} texts...")
        
        embeddings = embed_model.encode(texts).tolist()
        
        return jsonify({
            "embeddings": embeddings
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/rank', methods=['POST'])
def rank():
    try:
        data = request.get_json()
        if not data or 'candidates' not in data:
            return jsonify({"error": "Missing 'candidates' parameter"}), 400
            
        candidates_list = data['candidates']
        print(f"Applying LTR model to rank {len(candidates_list)} candidates...")
        
        if len(candidates_list) == 0:
            return jsonify({"ranked_candidates": []})
            
        # Parse features into pandas DataFrame for XGBoost
        records = []
        for c in candidates_list:
            records.append({
                'semantic_score': float(c.get('semantic_score', 0.0)),
                'experience_fit': float(c.get('experience_fit', 0.0)),
                'activity_score': float(c.get('activity_score', 0.0)),
                'intent_score': float(c.get('intent_score', 0.0)),
                'is_timeline_invalid': int(c.get('is_timeline_invalid', 0)),
                'impossible_skills_ratio': int(c.get('impossible_skills_ratio', 0)),
                'experience_discrepancy': int(c.get('experience_discrepancy', 0)),
                'is_education_invalid': int(c.get('is_education_invalid', 0)),
                'is_company_age_invalid': int(c.get('is_company_age_invalid', 0)),
                'is_consulting_only': int(c.get('is_consulting_only', 0)),
                'is_research_only': int(c.get('is_research_only', 0)),
                'is_title_chaser': int(c.get('is_title_chaser', 0)),
                'is_langchain_only': int(c.get('is_langchain_only', 0)),
                'location_fit': float(c.get('location_fit', 0.0)),
                'notice_period': int(c.get('notice_period', 0))
            })
            
        df_features = pd.DataFrame(records)
        
        # Run prediction
        scores = xgb_model.predict(df_features)
        
        # Enrich candidates list with their scores
        ranked = []
        for i, score in enumerate(scores):
            c = candidates_list[i]
            
            final_score = float(score)
            # Suppress honeypot scores
            is_honeypot = int(c.get('is_timeline_invalid', 0)) == 1 or \
                          int(c.get('impossible_skills_ratio', 0)) == 1 or \
                          int(c.get('experience_discrepancy', 0)) == 1 or \
                          int(c.get('is_education_invalid', 0)) == 1 or \
                          int(c.get('is_company_age_invalid', 0)) == 1
                          
            if is_honeypot:
                final_score = -9999.0
                
            ranked.append({
                "candidate_id": c["candidate_id"],
                "score": final_score
            })
            
        # Sort candidates by score descending, breaking ties by candidate_id ascending
        ranked.sort(key=lambda x: (-x["score"], x["candidate_id"]))
        
        print(f"Ranked candidate #1: ID={ranked[0]['candidate_id']} (Score: {ranked[0]['score']:.4f})")
        
        return jsonify({
            "ranked_candidates": ranked
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
