import json
from datetime import datetime
import os

def analyze_all_candidates():
    jsonl_path = r"c:\Users\bhave\Desktop\The Data & AI Challenge\dataset\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
    
    count = 0
    anomalies = []
    
    skill_anomalies_count = 0
    timeline_anomalies_count = 0
    company_age_anomalies_count = 0
    impossible_education_count = 0
    
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            candidate = json.loads(line)
            count += 1
            
            reasons = []
            
            # 1. Check skill duration vs proficiency
            expert_skills_zero_dur = 0
            for skill in candidate.get("skills", []):
                prof = skill.get("proficiency", "")
                dur = skill.get("duration_months", 0)
                if prof == "expert" and dur == 0:
                    expert_skills_zero_dur += 1
            
            if expert_skills_zero_dur >= 5:
                reasons.append(f"Skill Honeypot: {expert_skills_zero_dur} expert skills with 0 months used")
                skill_anomalies_count += 1
                
            # 2. Check career history timeline contradictions
            for job in candidate.get("career_history", []):
                company = job.get("company", "")
                start_str = job.get("start_date")
                end_str = job.get("end_date")
                dur_months = job.get("duration_months", 0)
                
                if start_str:
                    try:
                        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime(2026, 6, 29)
                        
                        actual_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                        if abs(dur_months - actual_months) > 24:
                            reasons.append(f"Timeline contradiction: job at {company} has duration_months={dur_months} but dates {start_str} to {end_str or 'present'} is {actual_months} months")
                            timeline_anomalies_count += 1
                    except ValueError:
                        pass
                
                if "Redrob" in company and dur_months > 36:
                    reasons.append(f"Company age contradiction: worked at {company} for {dur_months} months but company was founded recently")
                    company_age_anomalies_count += 1
                    
            # 3. Education vs Career timeline
            grad_years = [edu.get("end_year") for edu in candidate.get("education", []) if edu.get("end_year")]
            if grad_years:
                min_grad = min(grad_years)
                for job in candidate.get("career_history", []):
                    start_str = job.get("start_date")
                    if start_str:
                        try:
                            start_year = datetime.strptime(start_str, "%Y-%m-%d").year
                            if min_grad - start_year > 6:
                                reasons.append(f"Education anomaly: started working in {start_year} but graduated in {min_grad}")
                                impossible_education_count += 1
                        except ValueError:
                            pass
            
            if reasons:
                anomalies.append({
                    "candidate_id": candidate.get("candidate_id"),
                    "name": candidate.get("profile", {}).get("anonymized_name"),
                    "reasons": reasons
                })
                
    print(f"Total candidates checked: {count}")
    print(f"Skill anomalies: {skill_anomalies_count}")
    print(f"Timeline anomalies: {timeline_anomalies_count}")
    print(f"Company age anomalies: {company_age_anomalies_count}")
    print(f"Education anomalies: {impossible_education_count}")
    print(f"Total anomalous candidates: {len(anomalies)}")
    
    # Save a sample of anomalies to a file for review
    with open("anomalies_sample.json", "w") as out:
        json.dump(anomalies[:50], out, indent=2)

if __name__ == '__main__':
    analyze_all_candidates()
