CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    years_experience DOUBLE PRECISION NOT NULL,
    activity_score DOUBLE PRECISION NOT NULL,
    intent_score DOUBLE PRECISION NOT NULL,
    resume_text TEXT NOT NULL,
    is_timeline_invalid INTEGER DEFAULT 0,
    impossible_skills_ratio INTEGER DEFAULT 0,
    experience_discrepancy INTEGER DEFAULT 0,
    is_education_invalid INTEGER DEFAULT 0,
    is_company_age_invalid INTEGER DEFAULT 0,
    is_consulting_only INTEGER DEFAULT 0,
    is_research_only INTEGER DEFAULT 0,
    is_title_chaser INTEGER DEFAULT 0,
    is_langchain_only INTEGER DEFAULT 0,
    notice_period INTEGER DEFAULT 0,
    willing_to_relocate BOOLEAN DEFAULT FALSE,
    location VARCHAR(100),
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS candidates_embedding_hnsw_idx 
ON candidates USING hnsw (embedding vector_cosine_ops);
