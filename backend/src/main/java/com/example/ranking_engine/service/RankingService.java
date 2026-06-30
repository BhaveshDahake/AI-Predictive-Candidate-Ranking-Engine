package com.example.ranking_engine.service;

import com.example.ranking_engine.client.EmbeddingClient;
import com.example.ranking_engine.repository.CandidateRepository;
import com.example.ranking_engine.repository.CandidateSearchResult;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class RankingService {

    private final CandidateRepository candidateRepository;
    private final EmbeddingClient embeddingClient;

    public RankingService(CandidateRepository candidateRepository, EmbeddingClient embeddingClient) {
        this.candidateRepository = candidateRepository;
        this.embeddingClient = embeddingClient;
    }

    public static class EnrichedCandidate {
        private String id;
        private String name;
        private Double yearsExperience;
        private Double activityScore;
        private Double intentScore;
        private String resumeText;
        private Double semanticScore;
        private Double experienceFit;
        private Integer isTimelineInvalid;
        private Integer impossibleSkillsRatio;
        private Integer experienceDiscrepancy;
        private Integer isEducationInvalid;
        private Integer isCompanyAgeInvalid;
        private Integer isConsultingOnly;
        private Integer isResearchOnly;
        private Integer isTitleChaser;
        private Integer isLangchainOnly;
        private Double locationFit;
        private Integer noticePeriod;
        private String location;
        private Double ltrScore;

        // Constructors
        public EnrichedCandidate() {}

        public EnrichedCandidate(CandidateSearchResult result, Double experienceFit, Double locationFit, Double ltrScore) {
            this.id = result.getId();
            this.name = result.getName();
            this.yearsExperience = result.getYearsExperience();
            this.activityScore = result.getActivityScore();
            this.intentScore = result.getIntentScore();
            this.resumeText = result.getResumeText();
            this.semanticScore = result.getSemanticScore();
            this.isTimelineInvalid = result.getIsTimelineInvalid() != null ? result.getIsTimelineInvalid() : 0;
            this.impossibleSkillsRatio = result.getImpossibleSkillsRatio() != null ? result.getImpossibleSkillsRatio() : 0;
            this.experienceDiscrepancy = result.getExperienceDiscrepancy() != null ? result.getExperienceDiscrepancy() : 0;
            this.isEducationInvalid = result.getIsEducationInvalid() != null ? result.getIsEducationInvalid() : 0;
            this.isCompanyAgeInvalid = result.getIsCompanyAgeInvalid() != null ? result.getIsCompanyAgeInvalid() : 0;
            this.isConsultingOnly = result.getIsConsultingOnly() != null ? result.getIsConsultingOnly() : 0;
            this.isResearchOnly = result.getIsResearchOnly() != null ? result.getIsResearchOnly() : 0;
            this.isTitleChaser = result.getIsTitleChaser() != null ? result.getIsTitleChaser() : 0;
            this.isLangchainOnly = result.getIsLangchainOnly() != null ? result.getIsLangchainOnly() : 0;
            this.locationFit = locationFit;
            this.noticePeriod = result.getNoticePeriod() != null ? result.getNoticePeriod() : 0;
            this.location = result.getLocation();
            this.experienceFit = experienceFit;
            this.ltrScore = ltrScore;
        }

        // Getters and Setters
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public Double getYearsExperience() { return yearsExperience; }
        public void setYearsExperience(Double yearsExperience) { this.yearsExperience = yearsExperience; }
        public Double getActivityScore() { return activityScore; }
        public void setActivityScore(Double activityScore) { this.activityScore = activityScore; }
        public Double getIntentScore() { return intentScore; }
        public void setIntentScore(Double intentScore) { this.intentScore = intentScore; }
        public String getResumeText() { return resumeText; }
        public void setResumeText(String resumeText) { this.resumeText = resumeText; }
        public Double getSemanticScore() { return semanticScore; }
        public void setSemanticScore(Double semanticScore) { this.semanticScore = semanticScore; }
        public Double getExperienceFit() { return experienceFit; }
        public void setExperienceFit(Double experienceFit) { this.experienceFit = experienceFit; }
        public Integer getIsTimelineInvalid() { return isTimelineInvalid; }
        public void setIsTimelineInvalid(Integer isTimelineInvalid) { this.isTimelineInvalid = isTimelineInvalid; }
        public Integer getImpossibleSkillsRatio() { return impossibleSkillsRatio; }
        public void setImpossibleSkillsRatio(Integer impossibleSkillsRatio) { this.impossibleSkillsRatio = impossibleSkillsRatio; }
        public Integer getExperienceDiscrepancy() { return experienceDiscrepancy; }
        public void setExperienceDiscrepancy(Integer experienceDiscrepancy) { this.experienceDiscrepancy = experienceDiscrepancy; }
        public Integer getIsEducationInvalid() { return isEducationInvalid; }
        public void setIsEducationInvalid(Integer isEducationInvalid) { this.isEducationInvalid = isEducationInvalid; }
        public Integer getIsCompanyAgeInvalid() { return isCompanyAgeInvalid; }
        public void setIsCompanyAgeInvalid(Integer isCompanyAgeInvalid) { this.isCompanyAgeInvalid = isCompanyAgeInvalid; }
        public Integer getIsConsultingOnly() { return isConsultingOnly; }
        public void setIsConsultingOnly(Integer isConsultingOnly) { this.isConsultingOnly = isConsultingOnly; }
        public Integer getIsResearchOnly() { return isResearchOnly; }
        public void setIsResearchOnly(Integer isResearchOnly) { this.isResearchOnly = isResearchOnly; }
        public Integer getIsTitleChaser() { return isTitleChaser; }
        public void setIsTitleChaser(Integer isTitleChaser) { this.isTitleChaser = isTitleChaser; }
        public Integer getIsLangchainOnly() { return isLangchainOnly; }
        public void setIsLangchainOnly(Integer isLangchainOnly) { this.isLangchainOnly = isLangchainOnly; }
        public Double getLocationFit() { return locationFit; }
        public void setLocationFit(Double locationFit) { this.locationFit = locationFit; }
        public Integer getNoticePeriod() { return noticePeriod; }
        public void setNoticePeriod(Integer noticePeriod) { this.noticePeriod = noticePeriod; }
        public String getLocation() { return location; }
        public void setLocation(String location) { this.location = location; }
        public Double getLtrScore() { return ltrScore; }
        public void setLtrScore(Double ltrScore) { this.ltrScore = ltrScore; }
    }

    public List<EnrichedCandidate> rankCandidates(String jobDescription, int retrievalLimit) {
        // 1. Get embedding and required experience midpoint
        System.out.println("Step 1: Generating embedding for job description...");
        EmbeddingClient.EmbedResponse embedResponse = embeddingClient.getEmbedding(jobDescription);
        List<Double> embedding = embedResponse.getEmbedding();
        Double requiredExperience = embedResponse.getRequiredExperience();
        
        System.out.println("Extracted required experience midpoint: " + requiredExperience);

        // Convert double list to pgvector string format
        String jobVectorStr = "[" + embedding.stream()
                .map(String::valueOf)
                .collect(Collectors.joining(",")) + "]";

        // 2. Perform vector search in PostgreSQL
        System.out.println("Step 2: Performing vector search in PostgreSQL (limit " + retrievalLimit + ")...");
        List<CandidateSearchResult> rawCandidates = candidateRepository.searchCandidatesByVector(jobVectorStr, retrievalLimit);
        System.out.println("PostgreSQL returned " + rawCandidates.size() + " candidate profiles.");

        if (rawCandidates.isEmpty()) {
            return List.of();
        }

        // 3. Map to XGBoost features
        System.out.println("Step 3: Engineering tabular features for LTR...");
        List<EmbeddingClient.CandidateFeatures> featureList = new ArrayList<>();
        Map<String, Double> expFitMap = new HashMap<>();
        Map<String, Double> locFitMap = new HashMap<>();

        for (CandidateSearchResult c : rawCandidates) {
            // experience_fit = candidate experience - required experience midpoint
            double expFit = c.getYearsExperience() - requiredExperience;
            expFitMap.put(c.getId(), expFit);

            // Noida/Pune location fit calculation
            double locationFit = 0.0;
            String loc = c.getLocation() != null ? c.getLocation().toLowerCase() : "";
            boolean willingToRelocate = c.getWillingToRelocate() != null && c.getWillingToRelocate();
            
            if (loc.contains("noida") || loc.contains("pune") || loc.contains("delhi") || 
                loc.contains("ncr") || loc.contains("gurgaon") || loc.contains("hyderabad") || 
                loc.contains("mumbai")) {
                locationFit = 1.0;
            } else if ((loc.contains("bangalore") || loc.contains("bengaluru") || 
                        loc.contains("chennai") || loc.contains("kolkata") || 
                        loc.contains("ahmedabad")) && willingToRelocate) {
                locationFit = 1.0;
            } else if (willingToRelocate) {
                locationFit = 0.5;
            }
            locFitMap.put(c.getId(), locationFit);

            featureList.add(new EmbeddingClient.CandidateFeatures(
                    c.getId(),
                    c.getSemanticScore(),
                    expFit,
                    c.getActivityScore(),
                    c.getIntentScore(),
                    c.getIsTimelineInvalid() != null ? c.getIsTimelineInvalid() : 0,
                    c.getImpossibleSkillsRatio() != null ? c.getImpossibleSkillsRatio() : 0,
                    c.getExperienceDiscrepancy() != null ? c.getExperienceDiscrepancy() : 0,
                    c.getIsEducationInvalid() != null ? c.getIsEducationInvalid() : 0,
                    c.getIsCompanyAgeInvalid() != null ? c.getIsCompanyAgeInvalid() : 0,
                    c.getIsConsultingOnly() != null ? c.getIsConsultingOnly() : 0,
                    c.getIsResearchOnly() != null ? c.getIsResearchOnly() : 0,
                    c.getIsTitleChaser() != null ? c.getIsTitleChaser() : 0,
                    c.getIsLangchainOnly() != null ? c.getIsLangchainOnly() : 0,
                    locationFit,
                    c.getNoticePeriod() != null ? c.getNoticePeriod() : 0
            ));
        }

        // 4. Send features to LTR microservice
        System.out.println("Step 4: Sending features to XGBoost Flask server for scoring...");
        List<EmbeddingClient.RankedCandidate> rankings = embeddingClient.getRankings(featureList);

        // Map LTR scores back to candidate IDs
        Map<String, Double> scoreMap = rankings.stream()
                .collect(Collectors.toMap(
                        EmbeddingClient.RankedCandidate::getCandidateId,
                        EmbeddingClient.RankedCandidate::getScore,
                        (v1, v2) -> v1 // handle duplicates if any
                ));

        // 5. Enrich and sort candidates by LTR score descending (break ties alphabetically by candidate ID)
        System.out.println("Step 5: Enriching candidate list with scores and tie-breaking...");
        List<EnrichedCandidate> enrichedCandidates = rawCandidates.stream()
                .map(c -> {
                    Double ltrScore = scoreMap.getOrDefault(c.getId(), 0.0);
                    Double expFit = expFitMap.getOrDefault(c.getId(), 0.0);
                    Double locFit = locFitMap.getOrDefault(c.getId(), 0.0);
                    return new EnrichedCandidate(c, expFit, locFit, ltrScore);
                })
                .sorted((c1, c2) -> {
                    // Sort descending by LTR score
                    int scoreCompare = Double.compare(c2.getLtrScore(), c1.getLtrScore());
                    if (scoreCompare != 0) {
                        return scoreCompare;
                    }
                    // Break ties: sort ascending by candidate ID
                    return c1.getId().compareTo(c2.getId());
                })
                .collect(Collectors.toList());

        System.out.println("Final ranking process completed. Top candidate ID: " + enrichedCandidates.get(0).getId());
        return enrichedCandidates;
    }
}
