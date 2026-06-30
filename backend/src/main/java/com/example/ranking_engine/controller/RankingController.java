package com.example.ranking_engine.controller;

import com.example.ranking_engine.repository.CandidateRepository;
import com.example.ranking_engine.service.RankingService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // Allow React frontend to fetch
public class RankingController {

    private final RankingService rankingService;
    private final CandidateRepository candidateRepository;

    public RankingController(RankingService rankingService, CandidateRepository candidateRepository) {
        this.rankingService = rankingService;
        this.candidateRepository = candidateRepository;
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStats() {
        long count = candidateRepository.count();
        return ResponseEntity.ok(Map.of("totalCandidates", count));
    }

    public static class RankRequest {
        private String jobDescription;
        private Integer limit = 100;

        public String getJobDescription() {
            return jobDescription;
        }

        public void setJobDescription(String jobDescription) {
            this.jobDescription = jobDescription;
        }

        public Integer getLimit() {
            return limit;
        }

        public void setLimit(Integer limit) {
            this.limit = limit;
        }
    }

    @PostMapping("/rank")
    public ResponseEntity<List<RankingService.EnrichedCandidate>> rankCandidates(@RequestBody RankRequest request) {
        if (request.getJobDescription() == null || request.getJobDescription().trim().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }

        int limit = request.getLimit() != null ? request.getLimit() : 100;
        System.out.println("Received API request to rank top " + limit + " candidates.");
        
        List<RankingService.EnrichedCandidate> ranked = rankingService.rankCandidates(request.getJobDescription(), limit);
        return ResponseEntity.ok(ranked);
    }
}
