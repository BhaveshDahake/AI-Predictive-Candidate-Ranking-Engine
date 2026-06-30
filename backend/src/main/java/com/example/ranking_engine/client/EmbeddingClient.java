package com.example.ranking_engine.client;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Component
public class EmbeddingClient {

    private final RestTemplate restTemplate;
    private final String serviceUrl;

    public EmbeddingClient(@Value("${app.embedding-service.url}") String serviceUrl) {
        this.restTemplate = new RestTemplate();
        this.serviceUrl = serviceUrl;
    }

    // Response DTO for embed
    public static class EmbedResponse {
        private List<Double> embedding;
        
        @JsonProperty("required_experience")
        private Double requiredExperience;

        public List<Double> getEmbedding() {
            return embedding;
        }

        public void setEmbedding(List<Double> embedding) {
            this.embedding = embedding;
        }

        public Double getRequiredExperience() {
            return requiredExperience;
        }

        public void setRequiredExperience(Double requiredExperience) {
            this.requiredExperience = requiredExperience;
        }
    }

    // DTO for rank request candidate
    public static class CandidateFeatures {
        @JsonProperty("candidate_id")
        private String candidateId;
        
        @JsonProperty("semantic_score")
        private Double semanticScore;
        
        @JsonProperty("experience_fit")
        private Double experienceFit;
        
        @JsonProperty("activity_score")
        private Double activityScore;
        
        @JsonProperty("intent_score")
        private Double intentScore;
        
        @JsonProperty("is_timeline_invalid")
        private Integer isTimelineInvalid;
        
        @JsonProperty("impossible_skills_ratio")
        private Integer impossibleSkillsRatio;
        
        @JsonProperty("experience_discrepancy")
        private Integer experienceDiscrepancy;

        @JsonProperty("is_education_invalid")
        private Integer isEducationInvalid;

        @JsonProperty("is_company_age_invalid")
        private Integer isCompanyAge_invalid;

        @JsonProperty("is_consulting_only")
        private Integer isConsultingOnly;

        @JsonProperty("is_research_only")
        private Integer isResearchOnly;

        @JsonProperty("is_title_chaser")
        private Integer isTitleChaser;

        @JsonProperty("is_langchain_only")
        private Integer isLangchainOnly;

        @JsonProperty("location_fit")
        private Double locationFit;

        @JsonProperty("notice_period")
        private Integer noticePeriod;

        public CandidateFeatures(String candidateId, Double semanticScore, Double experienceFit, 
                                 Double activityScore, Double intentScore, Integer isTimelineInvalid, 
                                 Integer impossibleSkillsRatio, Integer experienceDiscrepancy,
                                 Integer isEducationInvalid, Integer isCompanyAge_invalid,
                                 Integer isConsultingOnly, Integer isResearchOnly,
                                 Integer isTitleChaser, Integer isLangchainOnly,
                                 Double locationFit, Integer noticePeriod) {
            this.candidateId = candidateId;
            this.semanticScore = semanticScore;
            this.experienceFit = experienceFit;
            this.activityScore = activityScore;
            this.intentScore = intentScore;
            this.isTimelineInvalid = isTimelineInvalid;
            this.impossibleSkillsRatio = impossibleSkillsRatio;
            this.experienceDiscrepancy = experienceDiscrepancy;
            this.isEducationInvalid = isEducationInvalid;
            this.isCompanyAge_invalid = isCompanyAge_invalid;
            this.isConsultingOnly = isConsultingOnly;
            this.isResearchOnly = isResearchOnly;
            this.isTitleChaser = isTitleChaser;
            this.isLangchainOnly = isLangchainOnly;
            this.locationFit = locationFit;
            this.noticePeriod = noticePeriod;
        }

        // Getters and Setters
        public String getCandidateId() { return candidateId; }
        public Double getSemanticScore() { return semanticScore; }
        public Double getExperienceFit() { return experienceFit; }
        public Double getActivityScore() { return activityScore; }
        public Double getIntentScore() { return intentScore; }
        public Integer getIsTimelineInvalid() { return isTimelineInvalid; }
        public Integer getImpossibleSkillsRatio() { return impossibleSkillsRatio; }
        public Integer getExperienceDiscrepancy() { return experienceDiscrepancy; }
        public Integer getIsEducationInvalid() { return isEducationInvalid; }
        public Integer getIsCompanyAge_invalid() { return isCompanyAge_invalid; }
        public Integer getIsConsultingOnly() { return isConsultingOnly; }
        public Integer getIsResearchOnly() { return isResearchOnly; }
        public Integer getIsTitleChaser() { return isTitleChaser; }
        public Integer getIsLangchainOnly() { return isLangchainOnly; }
        public Double getLocationFit() { return locationFit; }
        public Integer getNoticePeriod() { return noticePeriod; }
    }

    public static class RankRequest {
        private List<CandidateFeatures> candidates;

        public RankRequest(List<CandidateFeatures> candidates) {
            this.candidates = candidates;
        }

        public List<CandidateFeatures> getCandidates() {
            return candidates;
        }

        public void setCandidates(List<CandidateFeatures> candidates) {
            this.candidates = candidates;
        }
    }

    // DTO for rank response candidate
    public static class RankedCandidate {
        @JsonProperty("candidate_id")
        private String candidateId;
        private Double score;

        public String getCandidateId() {
            return candidateId;
        }

        public void setCandidateId(String candidateId) {
            this.candidateId = candidateId;
        }

        public Double getScore() {
            return score;
        }

        public void setScore(Double score) {
            this.score = score;
        }
    }

    public static class RankResponse {
        @JsonProperty("ranked_candidates")
        private List<RankedCandidate> rankedCandidates;

        public List<RankedCandidate> getRankedCandidates() {
            return rankedCandidates;
        }

        public void setRankedCandidates(List<RankedCandidate> rankedCandidates) {
            this.rankedCandidates = rankedCandidates;
        }
    }

    public EmbedResponse getEmbedding(String text) {
        String url = serviceUrl + "/embed";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(Map.of("text", text), headers);
        
        try {
            System.out.println("Calling Flask embedding service at: " + url);
            return restTemplate.postForObject(url, requestEntity, EmbedResponse.class);
        } catch (Exception e) {
            System.err.println("Failed to fetch embedding: " + e.getMessage());
            throw new RuntimeException("Embedding service error: " + e.getMessage(), e);
        }
    }

    public List<RankedCandidate> getRankings(List<CandidateFeatures> candidates) {
        String url = serviceUrl + "/rank";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<RankRequest> requestEntity = new HttpEntity<>(new RankRequest(candidates), headers);
        
        try {
            System.out.println("Calling Flask ranking service at: " + url + " with " + candidates.size() + " candidates");
            RankResponse response = restTemplate.postForObject(url, requestEntity, RankResponse.class);
            return response != null ? response.getRankedCandidates() : List.of();
        } catch (Exception e) {
            System.err.println("Failed to fetch rankings: " + e.getMessage());
            throw new RuntimeException("Ranking service error: " + e.getMessage(), e);
        }
    }
}
