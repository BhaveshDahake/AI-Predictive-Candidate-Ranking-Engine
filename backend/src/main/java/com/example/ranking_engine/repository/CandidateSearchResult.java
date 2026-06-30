package com.example.ranking_engine.repository;

public interface CandidateSearchResult {
    String getId();
    String getName();
    Double getYearsExperience();
    Double getActivityScore();
    Double getIntentScore();
    String getResumeText();
    Double getSemanticScore();
    Integer getIsTimelineInvalid();
    Integer getImpossibleSkillsRatio();
    Integer getExperienceDiscrepancy();
    Integer getIsEducationInvalid();
    Integer getIsCompanyAgeInvalid();
    Integer getIsConsultingOnly();
    Integer getIsResearchOnly();
    Integer getIsTitleChaser();
    Integer getIsLangchainOnly();
    Integer getNoticePeriod();
    Boolean getWillingToRelocate();
    String getLocation();
}
