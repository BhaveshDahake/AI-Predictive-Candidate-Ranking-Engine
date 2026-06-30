package com.example.ranking_engine.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "candidates")
public class Candidate {

    @Id
    private String id;

    private String name;

    @Column(name = "years_experience")
    private Double yearsExperience;

    @Column(name = "activity_score")
    private Double activityScore;

    @Column(name = "intent_score")
    private Double intentScore;

    @Column(name = "resume_text", columnDefinition = "TEXT")
    private String resumeText;

    // Constructors
    public Candidate() {}

    public Candidate(String id, String name, Double yearsExperience, Double activityScore, Double intentScore, String resumeText) {
        this.id = id;
        this.name = name;
        this.yearsExperience = yearsExperience;
        this.activityScore = activityScore;
        this.intentScore = intentScore;
        this.resumeText = resumeText;
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Double getYearsExperience() {
        return yearsExperience;
    }

    public void setYearsExperience(Double yearsExperience) {
        this.yearsExperience = yearsExperience;
    }

    public Double getActivityScore() {
        return activityScore;
    }

    public void setActivityScore(Double activityScore) {
        this.activityScore = activityScore;
    }

    public Double getIntentScore() {
        return intentScore;
    }

    public void setIntentScore(Double intentScore) {
        this.intentScore = intentScore;
    }

    public String getResumeText() {
        return resumeText;
    }

    public void setResumeText(String resumeText) {
        this.resumeText = resumeText;
    }
}
