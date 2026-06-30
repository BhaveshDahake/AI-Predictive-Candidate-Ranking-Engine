import xgboost as xgb
import numpy as np
import pandas as pd
import json
import os

def generate_synthetic_data(num_samples=5000):
    np.random.seed(42)
    
    # Generate features
    # 1. Semantic score: cosine similarity [0.0, 1.0], mostly around 0.3 to 0.9
    semantic_score = np.random.uniform(0.1, 0.95, num_samples)
    
    # 2. Candidate years of experience [1.0, 15.0]
    years_exp = np.random.uniform(1.0, 15.0, num_samples)
    experience_fit = years_exp - 7.0  # Midpoint of 5-9 years is 7
    
    # 3. Activity score [0.0, 100.0]
    activity_score = np.random.uniform(0.0, 100.0, num_samples)
    
    # 4. Intent score [0.0, 1.0]
    intent_score = np.random.choice([0.0, 1.0], size=num_samples, p=[0.7, 0.3])
    
    # Anomaly flags (honeypots)
    is_timeline_invalid = np.random.choice([0, 1], size=num_samples, p=[0.95, 0.05])
    impossible_skills_ratio = np.random.choice([0, 1], size=num_samples, p=[0.95, 0.05])
    experience_discrepancy = np.random.choice([0, 1], size=num_samples, p=[0.95, 0.05])
    is_education_invalid = np.random.choice([0, 1], size=num_samples, p=[0.95, 0.05])
    is_company_age_invalid = np.random.choice([0, 1], size=num_samples, p=[0.98, 0.02])
    
    # Anti-patterns
    is_consulting_only = np.random.choice([0, 1], size=num_samples, p=[0.8, 0.2])
    is_research_only = np.random.choice([0, 1], size=num_samples, p=[0.9, 0.1])
    is_title_chaser = np.random.choice([0, 1], size=num_samples, p=[0.9, 0.1])
    is_langchain_only = np.random.choice([0, 1], size=num_samples, p=[0.9, 0.1])
    
    # Behavioral and Demographics
    location_fit = np.random.choice([0.0, 0.5, 1.0], size=num_samples, p=[0.3, 0.3, 0.4])
    notice_period = np.random.choice([15, 30, 45, 60, 90, 120], size=num_samples, p=[0.2, 0.3, 0.1, 0.2, 0.1, 0.1])
    
    # Target relevance label [0 to 5]
    relevance = []
    for i in range(num_samples):
        # If any honeypot flag is set, set relevance to 0
        if (is_timeline_invalid[i] == 1 or impossible_skills_ratio[i] == 1 or 
            experience_discrepancy[i] == 1 or is_education_invalid[i] == 1 or 
            is_company_age_invalid[i] == 1):
            rel = 0.0
        else:
            # Base relevance on semantic score and experience fit
            # Experience fit: penalize being outside the 5-9 range (midpoint 7)
            exp_penalty = abs(experience_fit[i])
            if exp_penalty <= 2.0:
                exp_score = 3.0  # Perfect fit (5-9 years)
            elif exp_penalty <= 4.0:
                exp_score = 1.5  # Adjacent fit
            else:
                exp_score = 0.0  # Poor fit
                
            # Semantic search fit
            sem_score = semantic_score[i] * 4.0
            
            # Engagement velocity modifiers
            eng_score = (activity_score[i] + intent_score[i] * 100.0) / 200.0  # Max 1.0
            
            # Location fit modifier
            loc_score = location_fit[i] * 1.0
            
            # Notice period modifier
            if notice_period[i] <= 30:
                np_score = 0.5
            elif notice_period[i] <= 60:
                np_score = 0.2
            else:
                np_score = -0.5
                
            rel = sem_score + exp_score + eng_score + loc_score + np_score
            
            # Apply anti-pattern penalties
            if is_consulting_only[i] == 1:
                rel -= 1.5
            if is_research_only[i] == 1:
                rel -= 2.0
            if is_title_chaser[i] == 1:
                rel -= 1.0
            if is_langchain_only[i] == 1:
                rel -= 1.0
                
            # Bound it between 0.1 and 5.0
            rel = max(0.1, min(5.0, rel))
            
        relevance.append(rel)
        
    df = pd.DataFrame({
        'semantic_score': semantic_score,
        'experience_fit': experience_fit,
        'activity_score': activity_score,
        'intent_score': intent_score,
        'is_timeline_invalid': is_timeline_invalid,
        'impossible_skills_ratio': impossible_skills_ratio,
        'experience_discrepancy': experience_discrepancy,
        'is_education_invalid': is_education_invalid,
        'is_company_age_invalid': is_company_age_invalid,
        'is_consulting_only': is_consulting_only,
        'is_research_only': is_research_only,
        'is_title_chaser': is_title_chaser,
        'is_langchain_only': is_langchain_only,
        'location_fit': location_fit,
        'notice_period': notice_period,
        'relevance': relevance
    })
    
    return df

def train_model():
    print("Generating synthetic Learning to Rank (LTR) dataset...")
    df = generate_synthetic_data(10000)
    
    features = ['semantic_score', 'experience_fit', 'activity_score', 'intent_score', 
                'is_timeline_invalid', 'impossible_skills_ratio', 'experience_discrepancy',
                'is_education_invalid', 'is_company_age_invalid', 'is_consulting_only', 
                'is_research_only', 'is_title_chaser', 'is_langchain_only', 
                'location_fit', 'notice_period']
                
    X = df[features]
    y = df['relevance']
    
    print("Training XGBoost LTR regressor...")
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        random_state=42
    )
    model.fit(X, y)
    
    model_path = os.path.join(os.path.dirname(__file__), 'model.json')
    print(f"Saving trained model to {model_path}...")
    model.save_model(model_path)
    print("XGBoost LTR model training completed successfully.")

if __name__ == '__main__':
    train_model()
