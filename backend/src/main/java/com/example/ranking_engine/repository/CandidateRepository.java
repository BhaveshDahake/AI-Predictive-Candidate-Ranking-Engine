package com.example.ranking_engine.repository;

import com.example.ranking_engine.model.Candidate;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CandidateRepository extends JpaRepository<Candidate, String> {

    @Query(value = "SELECT id, name, " +
            "years_experience AS yearsExperience, " +
            "activity_score AS activityScore, " +
            "intent_score AS intentScore, " +
            "resume_text AS resumeText, " +
            "is_timeline_invalid AS isTimelineInvalid, " +
            "impossible_skills_ratio AS impossibleSkillsRatio, " +
            "experience_discrepancy AS experienceDiscrepancy, " +
            "is_education_invalid AS isEducationInvalid, " +
            "is_company_age_invalid AS isCompanyAgeInvalid, " +
            "is_consulting_only AS isConsultingOnly, " +
            "is_research_only AS isResearchOnly, " +
            "is_title_chaser AS isTitleChaser, " +
            "is_langchain_only AS isLangchainOnly, " +
            "notice_period AS noticePeriod, " +
            "willing_to_relocate AS willingToRelocate, " +
            "location AS location, " +
            "1 - (embedding <=> CAST(:jobVector AS vector)) AS semanticScore " +
            "FROM candidates " +
            "ORDER BY embedding <=> CAST(:jobVector AS vector) " +
            "LIMIT :limit", 
            nativeQuery = true)
    List<CandidateSearchResult> searchCandidatesByVector(
            @Param("jobVector") String jobVector, 
            @Param("limit") int limit
    );
}
