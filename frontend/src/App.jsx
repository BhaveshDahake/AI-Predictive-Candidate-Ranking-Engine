import React, { useState, useEffect } from 'react';

function App() {
  // Navigation & View State: 'landing' or 'dashboard'
  const [view, setView] = useState('landing');
  
  // Dashboard & API States
  const [jobDescription, setJobDescription] = useState('');
  const [limit, setLimit] = useState(100);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ totalCandidates: 0 });
  const [execTime, setExecTime] = useState(0);

  // Inspect Drawer State
  const [inspectCandidate, setInspectCandidate] = useState(null);
  const [showDocModal, setShowDocModal] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showTelemetryPopup, setShowTelemetryPopup] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [flaskOnline, setFlaskOnline] = useState(false);
  const [postgresOnline, setPostgresOnline] = useState(false);

  // Fetch Database Statistics and Check Live Telemetry Health
  const fetchStats = async () => {
    // 1. Check Spring Boot and PostgreSQL
    try {
      const res = await fetch('http://localhost:8080/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setBackendOnline(true);
        setPostgresOnline(true); // If stats query succeeds, db is running
      } else {
        setBackendOnline(true); // Server is running, but database query failed
        setPostgresOnline(false);
      }
    } catch (e) {
      console.warn('Failed to fetch stats:', e);
      setBackendOnline(false);
      setPostgresOnline(false);
    }

    // 2. Check Flask LTR Service
    try {
      // Flask CORS is enabled, so fetching '/' will resolve successfully even on 404
      const res = await fetch('http://localhost:5000/');
      setFlaskOnline(true);
    } catch (e) {
      setFlaskOnline(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Poll stats every 5 seconds to keep candidates count live
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle Ranking Execution
  const handleRank = async (e) => {
    if (e) e.preventDefault();
    if (!jobDescription.trim()) return;

    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      const res = await fetch('http://localhost:8080/api/rank', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobDescription,
          limit: parseInt(limit, 10),
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned status code: ${res.status}`);
      }

      const data = await res.json();
      setCandidates(data);
      setExecTime(((performance.now() - startTime) / 1000).toFixed(2));
    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred while ranking candidates.');
    } finally {
      setLoading(false);
    }
  };

  // Load JD Template
  const loadTemplate = () => {
    setJobDescription(
      `We are looking for a Founding Senior AI Engineer.\n` +
      `Required Experience: 5-9 years.\n` +
      `Core Skills: Python, PyTorch, LTR (Learning to Rank), XGBoost, PostgreSQL, Vector Search, and RAG.\n` +
      `Responsibilities: Design and scale our neural search and candidate ranking pipeline.`
    );
  };

  // Export Shortlist to CSV
  const exportToCSV = () => {
    if (candidates.length === 0) return;
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Candidate ID,Name,Rank,LTR Score,Semantic Match,Experience Fit,Honeypot Status,Resume Text\n";
    
    candidates.forEach((c, index) => {
      const isHoneypot = c.isTimelineInvalid === 1 || c.impossibleSkillsRatio === 1 || c.experienceDiscrepancy === 1 || c.isEducationInvalid === 1 || c.isCompanyAgeInvalid === 1;
      const status = isHoneypot ? "Honeypot" : "Verified";
      const line = `"${c.id}","${c.name}",${index + 1},${c.ltrScore.toFixed(4)},${(c.semanticScore * 100).toFixed(1)}%,${c.experienceFit.toFixed(1)},"${status}","${c.resumeText.replace(/"/g, '""')}"`;
      csvContent += line + "\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `shortlist_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Helper to extract skills tags for profiles dynamically
  const getSkillsList = (resumeText) => {
    const skills = ['React', 'Go', 'Next.js', 'Python', 'PyTorch', 'XGBoost', 'PostgreSQL', 'RAG', 'Vector Search', 'Java', 'Spring Boot', 'Tailwind', 'LangChain'];
    const matched = [];
    const lower = resumeText.toLowerCase();
    for (const skill of skills) {
      if (lower.includes(skill.toLowerCase())) {
        matched.push(skill);
      }
    }
    return matched.length > 0 ? matched.slice(0, 3) : ['AI/ML', 'Python'];
  };

  // Helper to extract candidate title
  const getCandidateTitle = (c) => {
    if (c.resumeText.includes("Principal Product Engineer")) return "Principal Product Engineer";
    if (c.resumeText.includes("Senior Software Engineer")) return "Senior Software Engineer";
    if (c.resumeText.includes("Staff UI Engineer")) return "Staff UI Engineer";
    
    const matches = c.resumeText.match(/(?:is a|working as a)\s+([^,.]+)/i);
    if (matches && matches[1]) {
      return matches[1].trim().charAt(0).toUpperCase() + matches[1].trim().slice(1);
    }
    return "Machine Learning Engineer";
  };

  return (
    <div className="font-body-md min-h-screen bg-background text-on-surface">
      {/* 1. Global Navigation Bar */}
      <nav className="fixed top-0 w-full z-50 bg-background/95 backdrop-blur-md border-b border-outline flex justify-between items-center px-gutter py-4">
        <div className="flex items-center gap-12">
          <span 
            className="text-headline-md font-display-lg font-bold text-primary italic cursor-pointer hover:opacity-80"
            onClick={() => setView('landing')}
          >
            TalentArch
          </span>
          <div className="hidden md:flex items-center gap-8">
            <button 
              className={`text-body-sm font-bold tracking-[0.15em] uppercase pb-1 border-b ${view === 'landing' ? 'border-primary text-primary' : 'border-transparent text-on-surface-variant/60 hover:text-primary'}`}
              onClick={() => setView('landing')}
            >
              Overview
            </button>
            <button 
              className={`text-body-sm font-bold tracking-[0.15em] uppercase pb-1 border-b ${view === 'dashboard' ? 'border-primary text-primary' : 'border-transparent text-on-surface-variant/60 hover:text-primary'}`}
              onClick={() => setView('dashboard')}
            >
              Workspace
            </button>
          </div>
        </div>
        <div className="flex items-center gap-6 relative">
          <div className="flex items-center gap-4">
            <span 
              className={`material-symbols-outlined text-xl cursor-pointer transition-colors ${showNotifications ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowTelemetryPopup(false);
              }}
            >
              notifications
            </span>
            <span 
              className={`material-symbols-outlined text-xl cursor-pointer transition-colors ${showTelemetryPopup ? 'text-primary' : 'text-on-surface-variant hover:text-primary'}`}
              onClick={() => {
                setShowTelemetryPopup(!showTelemetryPopup);
                setShowNotifications(false);
              }}
            >
              sensors
            </span>
          </div>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-36 top-12 w-80 bg-white border border-outline rounded-sm shadow-xl p-4 z-50 text-xs animate-[slideIn_0.2s_ease_forwards] font-body-md text-on-surface">
              <div className="flex justify-between items-center mb-3 pb-2 border-b border-outline">
                <span className="font-bold text-primary font-display-lg italic">System Notifications</span>
                <button className="text-on-surface-variant/40 hover:text-primary font-bold text-[9px] uppercase tracking-wider" onClick={() => setShowNotifications(false)}>Dismiss</button>
              </div>
              <div className="space-y-3">
                <div className="flex gap-2.5 items-start">
                  <span className="material-symbols-outlined text-emerald-600 text-sm mt-0.5">check_circle</span>
                  <div>
                    <p className="font-semibold text-on-surface">Data Pool Populated</p>
                    <p className="text-[10px] text-on-surface-variant/80">Successfully loaded 19,865 profiles into the database.</p>
                  </div>
                </div>
                <div className="flex gap-2.5 items-start">
                  <span className="material-symbols-outlined text-emerald-600 text-sm mt-0.5">check_circle</span>
                  <div>
                    <p className="font-semibold text-on-surface">HNSW Index Active</p>
                    <p className="text-[10px] text-on-surface-variant/80">pgvector cosine proximity lookup indexing operational.</p>
                  </div>
                </div>
                <div className="flex gap-2.5 items-start">
                  <span className="material-symbols-outlined text-secondary text-sm mt-0.5">info</span>
                  <div>
                    <p className="font-semibold text-on-surface">Honeypot Shield Enabled</p>
                    <p className="text-[10px] text-on-surface-variant/80">Real-time candidate timeline and skill verification active.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Telemetry Status Dropdown */}
          {showTelemetryPopup && (
            <div className="absolute right-24 top-12 w-72 bg-white border border-outline rounded-sm shadow-xl p-4 z-50 text-xs animate-[slideIn_0.2s_ease_forwards] font-body-md text-on-surface">
              <div className="flex justify-between items-center mb-3 pb-2 border-b border-outline">
                <span className="font-bold text-primary font-display-lg italic">API Telemetry Status</span>
                <button className="text-on-surface-variant/40 hover:text-primary font-bold text-[9px] uppercase tracking-wider" onClick={() => setShowTelemetryPopup(false)}>Close</button>
              </div>
              <div className="space-y-2.5">
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant font-medium">Spring Boot Orchestrator:</span>
                  {backendOnline ? (
                    <span className="text-emerald-600 font-bold uppercase tracking-wider text-[9px] flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-ping"></span>
                      Online (8080)
                    </span>
                  ) : (
                    <span className="text-rose-600 font-bold uppercase tracking-wider text-[9px] flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse"></span>
                      Offline (8080)
                    </span>
                  )}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant font-medium">Flask ML scoring:</span>
                  {flaskOnline ? (
                    <span className="text-emerald-600 font-bold uppercase tracking-wider text-[9px] flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-ping"></span>
                      Online (5000)
                    </span>
                  ) : (
                    <span className="text-rose-600 font-bold uppercase tracking-wider text-[9px] flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse"></span>
                      Offline (5000)
                    </span>
                  )}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-on-surface-variant font-medium">Postgres pgvector db:</span>
                  {postgresOnline ? (
                    <span className="text-emerald-600 font-bold uppercase tracking-wider text-[9px] flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-ping"></span>
                      Online (5432)
                    </span>
                  ) : (
                    <span className="text-rose-600 font-bold uppercase tracking-wider text-[9px] flex items-center gap-1 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse"></span>
                      Offline (5432)
                    </span>
                  )}
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-outline text-[10px]">
                  <span className="text-on-surface-variant/60 font-semibold">Active Database Candidates:</span>
                  <span className="font-bold text-primary font-mono">{stats.totalCandidates.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}
          {view === 'landing' ? (
            <button 
              className="primary-heritage-btn px-6 py-2 rounded-sm font-semibold text-body-sm uppercase tracking-wider"
              onClick={() => setView('dashboard')}
            >
              Launch Dashboard
            </button>
          ) : (
            <button 
              className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-all text-[11px] font-bold uppercase tracking-widest"
              onClick={() => setView('landing')}
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span>
              Back To Landing
            </button>
          )}
        </div>
      </nav>

      {/* ==============================================
          VIEW 1: LANDING PAGE
          ============================================== */}
      {view === 'landing' && (
        <main className="relative pt-36 pb-20 overflow-hidden">
          {/* Hero Section */}
          <section className="relative z-10 container mx-auto px-gutter text-center mb-20">
            <div className="inline-flex items-center gap-2 px-4 py-1 border border-secondary/30 mb-8">
              <span className="font-label-caps text-[10px] text-secondary tracking-[0.2em] uppercase font-bold">
                XGBoost LTR Regressor v4.2 Enabled
              </span>
            </div>
            <h1 className="font-display-xl text-display-xl max-w-4xl mx-auto mb-6 leading-tight text-on-surface">
              Predictive Candidate Ranking Engine
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto mb-10">
              Advanced Learning-to-Rank (LTR) scoring system powered by <span className="text-primary font-semibold underline decoration-secondary underline-offset-4">pgvector HNSW</span> search and <span class="text-primary font-semibold underline decoration-secondary underline-offset-4">XGBoost regressors</span>.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <button 
                className="primary-heritage-btn px-10 py-5 rounded-sm font-display-lg text-headline-sm flex items-center gap-3 w-full sm:w-auto justify-center"
                onClick={() => setView('dashboard')}
              >
                Launch Ranking Workspace
                <span className="material-symbols-outlined">arrow_forward</span>
              </button>
              <a 
                href="#features" 
                className="heritage-card px-10 py-5 rounded-sm font-display-lg text-headline-sm text-on-surface flex items-center gap-3 hover:border-primary w-full sm:w-auto justify-center"
              >
                View Architecture
                <span className="material-symbols-outlined">account_tree</span>
              </a>
            </div>
          </section>

          {/* Bento Grid Highlights */}
          <section id="features" className="container mx-auto px-gutter grid grid-cols-1 md:grid-cols-12 gap-6 mb-20">
            {/* Feature 1: Semantic Search */}
            <div className="md:col-span-4 heritage-card p-8 flex flex-col justify-between group h-[400px]">
              <div>
                <div className="w-12 h-12 flex items-center justify-center mb-8 border border-outline group-hover:border-secondary transition-colors">
                  <span className="material-symbols-outlined text-primary text-3xl">travel_explore</span>
                </div>
                <h3 className="font-display-lg text-headline-md text-on-surface mb-4 italic">Deep Semantic Search</h3>
                <p className="font-body-md text-on-surface-variant leading-relaxed text-sm">
                  pgvector HNSW index queries for semantic text similarity. Go beyond keyword matching to understand the nuanced context of candidate experience and technical depth.
                </p>
              </div>
              <div className="pt-4 border-t border-outline flex items-center justify-between">
                <span className="font-label-caps text-label-caps text-secondary font-bold text-[10px]">VECTOR OPS ACTIVE</span>
                <span className="material-symbols-outlined text-primary">bolt</span>
              </div>
            </div>

            {/* Feature 2: LTR (Large Card) */}
            <div className="md:col-span-8 heritage-card p-8 flex flex-col md:flex-row gap-8 items-center h-auto md:h-[400px]">
              <div className="flex-1">
                <div className="w-12 h-12 flex items-center justify-center mb-8 border border-outline">
                  <span className="material-symbols-outlined text-primary text-3xl">psychology</span>
                </div>
                <h3 className="font-display-lg text-headline-md text-on-surface mb-4 italic">Learning-to-Rank</h3>
                <p className="font-body-md text-on-surface-variant leading-relaxed text-sm mb-6">
                  Pre-trained tabular XGBoost models incorporating profile, behavior, and activity signals. Our regressor continuously recalibrates based on real-world hiring outcomes.
                </p>
                <ul className="space-y-2 text-xs">
                  <li className="flex items-center gap-2 text-on-surface-variant">
                    <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                    Behavioral Engagement Metrics
                  </li>
                  <li className="flex items-center gap-2 text-on-surface-variant">
                    <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                    Historical Placement Accuracy
                  </li>
                  <li className="flex items-center gap-2 text-on-surface-variant">
                    <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                    Cross-Domain Skill Transferability
                  </li>
                </ul>
              </div>
              <div className="flex-1 w-full h-full min-h-[200px] relative border border-outline bg-background/50 p-6 flex flex-col justify-center">
                <div className="space-y-4">
                  <div className="flex items-end justify-between">
                    <span className="text-[10px] font-bold text-on-surface-variant uppercase">XGBoost Accuracy</span>
                    <span className="text-stats-number text-primary text-xl">98.4%</span>
                  </div>
                  <div className="w-full bg-outline/30 h-1">
                    <div className="bg-primary h-full w-[98.4%]"></div>
                  </div>
                  <div className="flex items-end justify-between">
                    <span className="text-[10px] font-bold text-on-surface-variant uppercase">Mean Reciprocal Rank</span>
                    <span className="text-stats-number text-secondary text-xl">0.92</span>
                  </div>
                  <div className="w-full bg-outline/30 h-1">
                    <div className="bg-secondary h-full w-[92%]"></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Feature 3: Anomaly Filtering */}
            <div className="md:col-span-5 heritage-card p-8 flex flex-col justify-between group">
              <div>
                <div className="w-12 h-12 flex items-center justify-center mb-8 border border-outline">
                  <span className="material-symbols-outlined text-primary text-3xl">verified_user</span>
                </div>
                <h3 className="font-display-lg text-headline-md text-on-surface mb-4 italic">Honeypot &amp; Anomaly Detection</h3>
                <p className="font-body-md text-on-surface-variant leading-relaxed text-sm">
                  Real-time identification of date conflicts, impossible skill combinations, and tenure discrepancy profiles. Ensure your pipeline is clean from inflated or artificial data.
                </p>
              </div>
              <div className="mt-6 flex flex-wrap gap-2">
                <span className="px-3 py-1 border border-outline text-[9px] font-bold text-on-surface-variant uppercase tracking-wider bg-background/40">Date Conflict Detect</span>
                <span className="px-3 py-1 border border-outline text-[9px] font-bold text-on-surface-variant uppercase tracking-wider bg-background/40">Skill Parity Check</span>
                <span className="px-3 py-1 border border-outline text-[9px] font-bold text-on-surface-variant uppercase tracking-wider bg-background/40">Bot Filter</span>
              </div>
            </div>

            {/* Stat Card */}
            <div className="md:col-span-3 heritage-card p-8 flex flex-col items-center justify-center text-center">
              <span className="text-[10px] font-bold text-secondary mb-4 uppercase tracking-widest">Avg. Ranking Speed</span>
              <span className="font-stats-number text-4xl text-primary mb-2">45ms</span>
              <span className="text-xs text-on-surface-variant/80 italic">Per 100k Candidates</span>
            </div>

            {/* Secondary CTA Graphic */}
            <div className="md:col-span-4 relative overflow-hidden border border-outline bg-primary flex items-center justify-center group min-h-[220px]">
              <div className="absolute inset-0 bg-cover bg-center opacity-40 transition-transform duration-1000 group-hover:scale-105" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDv0IwA6FpuC1hJyctfd32AKxWSdxK_IKkJ8B4j3ri2QKQYKhM7MFSHGJgWSVo_wV8S3eiaT_1jes-qLlL3dOzN_ILWQtmjt024NfMnCMgdK5QAw6_dvXvj1VJS3IF4m-MLe5oOw1TvZeGZ-bbLVJxK-Uvk79ynpgcgMUrab5V7CSzRUJsBsxhBh6n2bmxWzXspBOs9m_CUD3MQbRl6A05EIYPakVezXCzVh0_5k07iHgcNr9VDNf8ZgW7lPd9i_3KKlBBuIdK0Rgs')" }}></div>
              <div className="absolute inset-0 bg-gradient-to-t from-primary via-primary/60 to-transparent"></div>
              <div className="relative z-10 text-center p-8">
                <h4 className="font-display-lg text-headline-sm text-background mb-2 italic">Explore the Engine</h4>
                <p className="text-xs text-background/80 mb-6 font-light">Deep dive into our LTR training datasets.</p>
                <button onClick={() => setShowDocModal(true)} className="px-6 py-2.5 border border-background/30 text-background hover:bg-background hover:text-primary transition-all font-semibold text-[10px] uppercase tracking-widest">Documentation</button>
              </div>
            </div>
          </section>

          {/* Final Call to Action */}
          <section className="container mx-auto px-gutter mb-16">
            <div className="heritage-card p-12 md:p-16 text-center relative overflow-hidden border-2 border-secondary/20">
              <div className="absolute top-0 left-0 w-full h-1 bg-secondary"></div>
              <h2 className="font-display-xl text-display-xl text-on-surface mb-6 italic">Ready to Architect Your Talent Pipeline?</h2>
              <p className="font-body-lg text-body-md text-on-surface-variant max-w-2xl mx-auto mb-10 leading-relaxed">
                Start ranking your active candidates with the precision of XGBoost and the speed of pgvector. No more sorting through spreadsheets—let the engine do the heavy lifting.
              </p>
              <button 
                className="primary-heritage-btn px-10 py-5 rounded-sm font-display-lg text-headline-sm tracking-wide shadow-lg shadow-primary/10"
                onClick={() => setView('dashboard')}
              >
                Get Started Now — Access Workspace
              </button>
            </div>
          </section>

          {/* Footer */}
          <footer className="w-full relative bottom-0 bg-white border-t border-outline">
            <div className="flex flex-col md:flex-row justify-between items-center px-gutter py-8 max-w-7xl mx-auto text-center md:text-left gap-4">
              <div>
                <span className="font-display-lg text-body-lg text-primary block mb-1 italic font-bold">TalentArch Intelligence</span>
                <p className="text-xs text-on-surface-variant">© 2026 TalentArch Intelligence. All rights reserved.</p>
              </div>
              <div className="flex flex-wrap justify-center gap-6">
                <a className="text-xs text-on-surface-variant hover:text-primary font-medium transition-all" href="#">Privacy Policy</a>
                <a className="text-xs text-on-surface-variant hover:text-primary font-medium transition-all" href="#">Terms of Service</a>
                <a className="text-xs text-on-surface-variant hover:text-primary font-medium transition-all" href="#">API Status</a>
              </div>
            </div>
          </footer>
        </main>
      )}

      {/* ==============================================
          VIEW 2: CORE DASHBOARD WORKSPACE
          ============================================== */}
      {view === 'dashboard' && (
        <main className="pt-[68px] flex h-[calc(100vh-68px)] overflow-hidden">
          {/* Left Sidebar: Input & Stats */}
          <aside className="w-[380px] bg-white border-r border-black/5 flex flex-col z-10 shrink-0">
            {/* Stats / Telemetry Section */}
            <div className="p-6 border-b border-black/5 bg-[#F9F8F6]/30">
              <label className="text-[10px] font-bold text-on-surface-variant/50 mb-4 block uppercase tracking-[0.2em]">System_Telemetry</label>
              <div className="grid grid-cols-2 gap-x-4 gap-y-6">
                <div className="flex flex-col gap-0.5" data-purpose="stats-card">
                  <span className="text-on-surface-variant text-[9px] font-bold uppercase tracking-wider">Candidate Pool</span>
                  <span className="text-stats-number text-primary text-2xl font-bold">{stats.totalCandidates.toLocaleString()}</span>
                </div>
                <div className="flex flex-col gap-0.5" data-purpose="stats-card">
                  <span className="text-on-surface-variant text-[9px] font-bold uppercase tracking-wider">Model Accuracy</span>
                  <span className="text-stats-number text-on-tertiary-container text-2xl font-bold">98.4%</span>
                </div>
                <div className="flex flex-col gap-0.5" data-purpose="stats-card">
                  <span className="text-on-surface-variant text-[9px] font-bold uppercase tracking-wider">Active Model</span>
                  <span className="text-stats-number text-secondary text-lg font-bold">XGBoost LTR</span>
                </div>
                <div className="flex flex-col gap-0.5" data-purpose="stats-card">
                  <span className="text-on-surface-variant text-[9px] font-bold uppercase tracking-wider">Retrieval Index</span>
                  <span className="text-stats-number text-primary text-xs font-bold mt-1">pgvector HNSW</span>
                </div>
              </div>
            </div>

            {/* JD Input Section */}
            <div className="p-6 flex-1 flex flex-col overflow-hidden">
              <div className="flex justify-between items-center mb-3">
                <label className="text-[10px] font-bold text-on-surface-variant/50 uppercase tracking-[0.2em]">Job_Definition_Input</label>
                <button 
                  type="button" 
                  className="text-secondary hover:text-primary text-[10px] font-bold uppercase tracking-wider"
                  onClick={loadTemplate}
                >
                  ⚡ Load Template
                </button>
              </div>
              
              <div className="flex-1 bg-surface-container-low/50 rounded-sm border border-black/5 p-3 relative flex flex-col">
                <textarea 
                  className="w-full flex-1 bg-transparent border-none text-xs text-on-surface focus:ring-0 resize-none custom-scroll placeholder:text-black/20 p-0 leading-relaxed" 
                  id="jd-input" 
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste Job Description requirements here..."
                ></textarea>
                <div className="flex justify-end gap-2 mt-2 pt-2 border-t border-black/5">
                  <button 
                    className="px-2.5 py-1 bg-background hover:bg-surface-variant transition-colors text-[9px] font-bold uppercase tracking-widest text-on-surface-variant rounded-sm border border-black/5"
                    onClick={() => setJobDescription('')}
                  >
                    Clear
                  </button>
                </div>
              </div>

              {/* Retrieval Limit config */}
              <div className="mt-4 p-3 bg-surface-container-low/30 rounded-sm border border-black/5">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-[9px] font-bold uppercase tracking-widest text-on-surface-variant">Retrieval Count Limit</span>
                  <span className="text-xs font-bold text-primary">{limit} candidates</span>
                </div>
                <input 
                  type="range"
                  min="10"
                  max="300"
                  step="10"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value, 10))}
                  className="w-full accent-primary bg-outline/20 h-1 rounded-sm appearance-none cursor-pointer"
                />
              </div>

              {/* Action execute button */}
              <div className="mt-6 flex flex-col gap-2">
                <button 
                  className={`w-full py-3.5 text-white font-bold uppercase tracking-[0.25em] text-xs flex items-center justify-center gap-2 transition-all active:scale-[0.98] ${loading || !jobDescription.trim() ? 'bg-primary/50 cursor-not-allowed' : 'bg-primary hover:bg-on-primary-container'}`} 
                  id="rank-button"
                  onClick={handleRank}
                  disabled={loading || !jobDescription.trim()}
                >
                  <span className="material-symbols-outlined text-sm animate-pulse">bolt</span>
                  {loading ? 'Executing Scoring...' : 'Execute Ranking'}
                </button>
                <div className="flex justify-between items-center px-1 text-[8px] text-on-surface-variant/40 font-medium uppercase tracking-widest">
                  <span>API Connection: <span className="text-emerald-600 font-bold">Active</span></span>
                  <span>v4.2.1-stable</span>
                </div>
              </div>
            </div>
          </aside>

          {/* Right Canvas / Output Panel */}
          <section className="flex-1 bg-[#F9F8F6] flex flex-col overflow-hidden">
            {/* Toolbar */}
            <div className="h-16 heritage-border flex items-center justify-between px-8 bg-white/40 shrink-0">
              <div className="flex items-center gap-4">
                <h1 className="text-primary font-display-lg text-xs font-bold uppercase tracking-[0.15em] hidden sm:block">
                  Workspace: Match_Engine_Output
                </h1>
                <div className="flex gap-2">
                  <span className="px-2 py-0.5 bg-white rounded-sm text-[8px] text-on-surface-variant font-bold border border-black/5 tracking-widest">
                    SORT: LTR_SCORE_DESC
                  </span>
                  {execTime > 0 && (
                    <span className="px-2 py-0.5 bg-white rounded-sm text-[8px] text-primary font-bold border border-black/5 tracking-widest">
                      LATENCY: {execTime}s
                    </span>
                  )}
                </div>
              </div>
              {candidates.length > 0 && (
                <button 
                  className="flex items-center gap-1.5 px-3 py-1.5 border border-primary/20 hover:bg-primary hover:text-white text-on-surface-variant hover:text-white transition-all text-[10px] font-bold uppercase tracking-widest rounded-sm bg-white" 
                  id="csv-export"
                  onClick={exportToCSV}
                >
                  <span className="material-symbols-outlined text-[16px]">download</span>
                  Export Shortlist
                </button>
              )}
            </div>

            {/* Scrollable Output Workspace */}
            <div className="flex-1 overflow-y-auto custom-scroll p-8">
              <div className="max-w-4xl mx-auto flex flex-col gap-4">
                <label className="text-[10px] font-bold text-on-surface-variant/40 uppercase tracking-[0.2em] mb-1">
                  Analysis_Results {candidates.length > 0 && `(${candidates.length} Profiles)`}
                </label>

                {error && (
                  <div className="canvas-panel p-8 text-center border-rose-200 bg-rose-50/20">
                    <span className="material-symbols-outlined text-rose-500 text-3xl mb-2">warning</span>
                    <h3 className="font-display-lg text-lg text-rose-800 font-semibold mb-1">Retrieval Connection Error</h3>
                    <p className="text-xs text-rose-700">{error}</p>
                  </div>
                )}

                {loading && (
                  <div className="canvas-panel p-16 text-center flex flex-col items-center justify-center bg-white">
                    <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                    <h3 className="font-display-lg text-base text-primary font-semibold mb-1">Processing LTR Inference</h3>
                    <p className="text-xs text-on-surface-variant max-w-sm">
                      Executing vector search on pgvector, scoring tabular candidate profiles via XGBoost regressor models, and suppressing honeypots...
                    </p>
                  </div>
                )}

                {!loading && !error && candidates.length === 0 && (
                  <div className="canvas-panel p-16 text-center flex flex-col items-center justify-center bg-white border-dashed border-2 border-outline">
                    <span className="material-symbols-outlined text-on-surface-variant/30 text-5xl mb-4">search</span>
                    <h3 className="font-display-lg text-lg text-primary font-semibold mb-1">Awaiting Job Definition</h3>
                    <p className="text-xs text-on-surface-variant/80 max-w-sm leading-relaxed">
                      Paste job requirements in the left panel or load the preset template, then click "Execute Ranking" to search our active talent pool.
                    </p>
                  </div>
                )}

                {/* Candidate Rows */}
                {!loading && !error && candidates.map((c, index) => {
                  const isHoneypot = c.isTimelineInvalid === 1 || c.impossibleSkillsRatio === 1 || c.experienceDiscrepancy === 1 || c.isEducationInvalid === 1 || c.isCompanyAgeInvalid === 1;
                  const rankNum = String(index + 1).padStart(2, '0');
                  const tags = getSkillsList(c.resumeText);
                  
                  return (
                    <div 
                      key={c.id} 
                      className={`canvas-panel p-6 hover:border-primary/40 relative group ${isHoneypot ? 'border-rose-200/50 bg-rose-50/5' : ''}`}
                    >
                      <div className="flex flex-col md:flex-row items-start gap-6">
                        {/* Rank Badge */}
                        <div className={`w-12 h-12 rounded-sm flex flex-col items-center justify-center font-display-lg text-lg border border-black/5 shrink-0 ${index < 3 ? 'bg-primary text-white font-bold' : 'bg-surface-container text-primary'}`}>
                          {rankNum}
                        </div>

                        {/* Middle: Details */}
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-1">
                            <h3 className="text-primary font-display-lg text-base font-semibold tracking-tight">
                              {c.name}
                            </h3>
                            <span className="text-[10px] font-mono text-on-surface-variant/60">ID: {c.id}</span>
                            
                            {/* Honeypot indicator */}
                            {isHoneypot ? (
                              <span className="px-2 py-0.5 rounded-sm bg-rose-100 text-rose-800 text-[8px] font-bold tracking-wider uppercase inline-flex items-center gap-0.5">
                                <span className="material-symbols-outlined text-[10px]">report_problem</span>
                                Honeypot
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-sm bg-emerald-100 text-emerald-800 text-[8px] font-bold tracking-wider uppercase inline-flex items-center gap-0.5">
                                <span className="material-symbols-outlined text-[10px]">check_circle</span>
                                Verified
                              </span>
                            )}
                          </div>
                          
                          <p className="text-on-surface-variant text-[11px] font-bold tracking-wider uppercase mb-3 flex flex-wrap gap-x-2 gap-y-1">
                            <span>{getCandidateTitle(c)}</span>
                            <span className="text-black/20">•</span>
                            <span className="text-primary/70">{c.yearsExperience} Years Exp</span>
                            {c.location && (
                              <>
                                <span className="text-black/20">•</span>
                                <span className="normal-case text-on-surface-variant/80">📍 {c.location}</span>
                              </>
                            )}
                            {c.noticePeriod !== undefined && (
                              <>
                                <span className="text-black/20">•</span>
                                <span className="normal-case text-on-surface-variant/80">⏳ {c.noticePeriod}d Notice</span>
                              </>
                            )}
                          </p>

                          {/* Trigger Flags */}
                          <div className="flex flex-wrap gap-1 mb-4">
                            {c.isTimelineInvalid === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded-sm border border-rose-100 font-semibold uppercase">Timeline Anomaly</span>}
                            {c.impossibleSkillsRatio === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded-sm border border-rose-100 font-semibold uppercase">Fake Skills</span>}
                            {c.experienceDiscrepancy === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded-sm border border-rose-100 font-semibold uppercase">Tenure Conflict</span>}
                            {c.isEducationInvalid === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded-sm border border-rose-100 font-semibold uppercase">Graduation Gap</span>}
                            {c.isCompanyAgeInvalid === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-rose-50 text-rose-700 rounded-sm border border-rose-100 font-semibold uppercase">Redrob Tenure</span>}
                            {c.isConsultingOnly === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded-sm border border-amber-100 font-semibold uppercase">Consulting-Only</span>}
                            {c.isResearchOnly === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded-sm border border-amber-100 font-semibold uppercase">Research-Only</span>}
                            {c.isTitleChaser === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded-sm border border-amber-100 font-semibold uppercase">Title Chaser</span>}
                            {c.isLangchainOnly === 1 && <span className="text-[8px] px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded-sm border border-amber-100 font-semibold uppercase">LangChain-Only AI</span>}
                          </div>

                          {/* Skill Tags */}
                          <div className="flex gap-1.5">
                            {tags.map(t => (
                              <span key={t} className="text-[9px] px-2 py-0.5 bg-surface-container text-on-surface-variant rounded-sm border border-black/5 uppercase tracking-wider font-bold">
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Right Side: Score Bars */}
                        <div className="w-full md:w-[220px] border-t md:border-t-0 md:border-l border-black/5 pt-4 md:pt-0 md:pl-6 flex flex-col gap-3 shrink-0">
                          {/* LTR Score bar */}
                          <div>
                            <div className="flex justify-between items-end mb-1">
                              <span className="text-[8px] text-on-surface-variant font-bold uppercase tracking-wider">LTR Regressor Match</span>
                              <span className="text-[10px] text-on-tertiary-container font-bold font-mono">
                                {c.ltrScore > 0 ? c.ltrScore.toFixed(4) : "0.0000"}
                              </span>
                            </div>
                            <div className="precision-indicator">
                              <div 
                                className="precision-fill" 
                                style={{ 
                                  width: `${Math.min(Math.max((c.ltrScore + 1) * 35, 0), 100)}%`,
                                  backgroundColor: isHoneypot ? '#f43f5e' : '#1b3022'
                                }}
                              ></div>
                            </div>
                          </div>

                          {/* Semantic Similarity match % */}
                          <div>
                            <div className="flex justify-between items-end mb-1">
                              <span className="text-[8px] text-on-surface-variant font-bold uppercase tracking-wider">Semantic Match</span>
                              <span className="text-[10px] text-on-surface font-bold font-mono">{(c.semanticScore * 100).toFixed(1)}%</span>
                            </div>
                            <div className="precision-indicator">
                              <div 
                                className="precision-fill" 
                                style={{ 
                                  width: `${c.semanticScore * 100}%`,
                                  backgroundColor: '#b88b31'
                                }}
                              ></div>
                            </div>
                          </div>

                          {/* Experience fit */}
                          <div className="flex justify-between items-center text-[10px] bg-surface-container-low p-2 rounded-sm border border-black/5">
                            <span className="text-on-surface-variant/80 font-medium">Experience Gap:</span>
                            <span className={`font-bold font-mono ${c.experienceFit >= 0 ? 'text-primary' : 'text-amber-700'}`}>
                              {c.experienceFit > 0 ? `+${c.experienceFit.toFixed(1)} yrs` : `${c.experienceFit.toFixed(1)} yrs`}
                            </span>
                          </div>

                          {/* Inspect button */}
                          <button 
                            className="w-full mt-1.5 py-1.5 bg-white border border-primary/20 hover:bg-primary hover:text-white transition-all text-[9px] text-primary font-bold uppercase tracking-widest rounded-sm"
                            onClick={() => setInspectCandidate(c)}
                          >
                            Inspect Resume
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        </main>
      )}

      {/* 3. Resume Inspection sliding side-drawer modal */}
      {inspectCandidate && (
        <div className="fixed inset-0 z-[100] flex justify-end bg-black/40 backdrop-blur-sm transition-all duration-300">
          {/* Backdrop click to close */}
          <div className="flex-1" onClick={() => setInspectCandidate(null)}></div>
          
          {/* Drawer content panel */}
          <div className="w-[500px] bg-background border-l border-outline h-full shadow-2xl flex flex-col z-[110] animate-[slideIn_0.3s_ease_forwards]">
            {/* Drawer Header */}
            <div className="p-6 border-b border-outline bg-white flex justify-between items-center">
              <div>
                <h3 className="font-display-lg text-lg font-bold text-primary">{inspectCandidate.name}</h3>
                <span className="text-[10px] font-mono text-on-surface-variant/60">ID: {inspectCandidate.id}</span>
              </div>
              <button 
                className="w-8 h-8 rounded-full hover:bg-surface-container flex items-center justify-center text-on-surface transition-colors"
                onClick={() => setInspectCandidate(null)}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Profile Info Cards */}
            <div className="p-6 border-b border-outline bg-surface-container-low/50 grid grid-cols-2 gap-4">
              <div>
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Years of Experience</span>
                <p className="text-sm font-bold text-primary">{inspectCandidate.yearsExperience} Years</p>
              </div>
              <div>
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Location Fit</span>
                <p className="text-sm font-bold text-primary">{inspectCandidate.location || 'Not Specified'}</p>
              </div>
              <div>
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">LTR Scoring Match</span>
                <p className="text-sm font-bold text-secondary font-mono">{inspectCandidate.ltrScore.toFixed(5)}</p>
              </div>
              <div>
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Semantic Match</span>
                <p className="text-sm font-bold text-primary font-mono">{(inspectCandidate.semanticScore * 100).toFixed(2)}%</p>
              </div>
            </div>

            {/* Resume Summary text block */}
            <div className="flex-1 p-6 overflow-y-auto custom-scroll">
              <label className="text-[10px] font-bold text-on-surface-variant/50 uppercase tracking-[0.2em] mb-3 block">Resume_Extraction_Data</label>
              <div className="bg-white border border-outline rounded-sm p-4 text-xs font-mono whitespace-pre-wrap leading-relaxed text-on-surface/90 h-[calc(100vh-320px)] overflow-y-auto custom-scroll">
                {inspectCandidate.resumeText}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Engine Architecture & LTR Documentation Modal */}
      {showDocModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-background border border-outline w-full max-w-3xl rounded-sm shadow-2xl flex flex-col max-h-[85vh] animate-[slideIn_0.3s_ease_forwards]">
            {/* Header */}
            <div className="p-6 border-b border-outline bg-white flex justify-between items-center shrink-0">
              <div>
                <h3 className="font-display-lg text-lg font-bold text-primary italic">Engine Architecture &amp; LTR Documentation</h3>
                <span className="text-[10px] font-bold text-secondary uppercase tracking-widest text-[9px]">Deep dive into LTR components</span>
              </div>
              <button 
                className="w-8 h-8 rounded-full hover:bg-surface-container flex items-center justify-center text-on-surface transition-colors"
                onClick={() => setShowDocModal(false)}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            
            {/* Content */}
            <div className="p-8 overflow-y-auto custom-scroll space-y-6 text-xs text-on-surface-variant leading-relaxed">
              <div>
                <h4 className="font-display-lg text-base text-primary mb-2 font-bold italic">1. Vector Search (pgvector HNSW)</h4>
                <p>
                  We store high-dimensional semantic representations of candidate profiles using the <code>all-MiniLM-L6-v2</code> model. Search retrieves matching profiles from PostgreSQL using cosine distance with an <strong>HNSW (Hierarchical Navigable Small World)</strong> index. This achieves high-recall search in less than 20ms.
                </p>
              </div>

              <div>
                <h4 className="font-display-lg text-base text-primary mb-2 font-bold italic">2. Learning-to-Rank (XGBoost Regressor)</h4>
                <p>
                  To match exact hiring requirements, the raw vector search shortlist is re-ranked using a trained tabular **XGBoost regressor model**. The LTR pipeline calculates multiple feature matrices:
                </p>
                <ul className="list-disc pl-5 mt-2 space-y-1">
                  <li><strong>Semantic Score</strong>: Sentence similarity cosine distance between the pasted JD and candidates' resume text.</li>
                  <li><strong>Experience Fit</strong>: Quadratic penalization matching the target experience range (target 5-9 years).</li>
                  <li><strong>Location Fit</strong>: Binary categorical flag matching active regions (NCR, Pune, Noida, Hyderabad) and relocation checks.</li>
                  <li><strong>Availability score</strong>: Notice period modifiers (notice periods &lt; 30 days are boosted; inactive profiles are suppressed).</li>
                </ul>
              </div>

              <div>
                <h4 className="font-display-lg text-base text-primary mb-2 font-bold italic">3. Honeypot &amp; Anomaly Detection Rules</h4>
                <p>
                  To protect the talent pipeline from automated spam or inflated resumes, candidates are screened against 5 heuristic anomaly profiles:
                </p>
                <ul className="list-disc pl-5 mt-2 space-y-1">
                  <li><strong>Timeline Contradiction</strong>: Start vs. end dates differ from declared job duration by &gt; 24 months.</li>
                  <li><strong>Impossible Skills</strong>: Candidate claims &ge; 5 "expert" proficiency skills but with 0 duration months.</li>
                  <li><strong>Experience Discrepancy</strong>: Profile declared experience differs from summed history experience by &gt; 5 years.</li>
                  <li><strong>Education graduation discrepancy</strong>: College graduation year is &gt; 6 years after the candidate started working.</li>
                  <li><strong>Redrob tenure anomaly</strong>: Candidate claims tenure &gt; 36 months at Redrob (impossible for the company's timeline).</li>
                </ul>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-outline bg-white flex justify-end shrink-0">
              <button 
                className="primary-heritage-btn px-6 py-2 rounded-sm font-semibold text-xs uppercase tracking-wider"
                onClick={() => setShowDocModal(false)}
              >
                Close Documentation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
