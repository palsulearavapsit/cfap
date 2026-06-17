// EcoTrack AI - Vanilla JS SPA App Handler

document.addEventListener('DOMContentLoaded', () => {
  // Helper to escape HTML tags to prevent XSS
  function escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // --- APP STATE (Item 49, 53 cached) ---
  const state = {
    charts: {
      history: null,
      pie: null,
      comparison: null,
    },
    calculatorStep: 1,
    token: localStorage.getItem('auth_token') || null,
    isRegistering: false,
    historyFilter: '6m',
    sustainabilityScore: 80,
    rewardPoints: 0,
  };

  // --- 60 ENHANCEMENTS HELPER FUNCTIONS ---

  // User Level Progression (Item 49, 53)
  function updateLevelAndProgression(points) {
    let level = 1;
    let levelName = "Novice Citizen";
    let currentLevelMin = 0;
    let nextLevelMax = 100;

    if (points > 600) {
      level = 4;
      levelName = "Climate Champion";
      currentLevelMin = 601;
      nextLevelMax = 1000;
    } else if (points > 300) {
      level = 3;
      levelName = "Eco Defender";
      currentLevelMin = 301;
      nextLevelMax = 600;
    } else if (points > 100) {
      level = 2;
      levelName = "Green Guardian";
      currentLevelMin = 101;
      nextLevelMax = 300;
    }

    const levelPointsEarned = points - currentLevelMin;
    const levelPointsTotal = nextLevelMax - currentLevelMin;
    const progressPct = Math.min(100, Math.max(0, (levelPointsEarned / levelPointsTotal) * 100));

    const navBadgeContainer = document.getElementById('nav-level-badge-container');
    const userLevelBadge = document.getElementById('user-level-badge');
    const profileLevelLabel = document.getElementById('profile-level-label');
    const profileNextLevelPts = document.getElementById('profile-next-level-pts');
    const profileLevelFill = document.getElementById('profile-level-fill');

    if (navBadgeContainer && userLevelBadge) {
      userLevelBadge.textContent = `Lvl ${level}`;
      navBadgeContainer.classList.remove('hidden');
    }
    if (profileLevelLabel) {
      profileLevelLabel.textContent = `Level ${level} (${levelName})`;
    }
    if (profileNextLevelPts) {
      profileNextLevelPts.textContent = `${points} / ${nextLevelMax} pts`;
    }
    if (profileLevelFill) {
      profileLevelFill.style.width = `${progressPct}%`;
    }

    return { level, points };
  }

  // Achievement Badges dynamically rendering (Item 52)
  function renderBadgesList(points, carbonScore) {
    const badgesList = document.getElementById('badges-list');
    if (!badgesList) return;

    const badges = [
      { id: 'novice', name: 'Green Recruit', desc: 'Join the platform & earn first points.', threshold: 0, type: 'points' },
      { id: 'adv', name: 'Eco Advocate', desc: 'Reach 100+ total reward points.', threshold: 100, type: 'points' },
      { id: 'expert', name: 'Carbon Slayer', desc: 'Reach 300+ total reward points.', threshold: 300, type: 'points' },
      { id: 'champion', name: 'Earth Champion', desc: 'Reach 600+ total reward points.', threshold: 600, type: 'points' },
      { id: 'sustain', name: 'Efficiency Guru', desc: 'Achieve a Sustainability Score of 85+.', threshold: 85, type: 'score' }
    ];

    badgesList.innerHTML = '';
    badges.forEach(badge => {
      const unlocked = badge.type === 'points' ? points >= badge.threshold : carbonScore >= badge.threshold;
      
      const badgeItem = document.createElement('div');
      badgeItem.className = `badge-item ${unlocked ? 'active' : ''}`;
      badgeItem.innerHTML = `
        <svg class="badge-icon" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
        <div>
          <span style="font-weight: 700; display: block; color: ${unlocked ? 'var(--accent)' : 'var(--text-muted)'}">${badge.name}</span>
          <span style="font-size: 0.7rem; color: var(--text-secondary);">${badge.desc} ${unlocked ? ' (Unlocked!)' : ''}</span>
        </div>
      `;
      badgesList.appendChild(badgeItem);
    });
  }

  // Local-time Dashboard Greeting (Item 50)
  function updateDashboardGreeting() {
    const greetingEl = document.getElementById('dashboard-greeting');
    if (!greetingEl) return;
    const hour = new Date().getHours();
    let greeting = "Good morning, Eco Citizen!";
    if (hour >= 18) {
      greeting = "Good evening, Eco Citizen!";
    } else if (hour >= 12) {
      greeting = "Good afternoon, Eco Citizen!";
    }
    greetingEl.textContent = greeting;
  }

  // Share achievements to clipboard (Item 51)
  function setupShareButton(points) {
    const shareBtn = document.getElementById('btn-share-achievements');
    if (!shareBtn) return;
    
    const newBtn = shareBtn.cloneNode(true);
    shareBtn.parentNode.replaceChild(newBtn, shareBtn);
    
    newBtn.addEventListener('click', async () => {
      const level = points > 600 ? 4 : points > 300 ? 3 : points > 100 ? 2 : 1;
      const textToCopy = `I am fighting climate change on EcoTrack AI! I've reached Level ${level} with ${points} reward points. Track your carbon footprint today!`;
      try {
        await navigator.clipboard.writeText(textToCopy);
        showNotification('Achievements copied to clipboard!', 'success');
      } catch (err) {
        showNotification('Could not copy achievements to clipboard.', 'error');
      }
    });
  }

  // Keyboard navigation shortcuts (Item 40)
  function setupNavigationShortcuts() {
    window.addEventListener('keydown', (e) => {
      if (e.altKey) {
        const key = e.key.toLowerCase();
        if (key === 'd') {
          e.preventDefault();
          navigateTo('dashboard');
        } else if (key === 'c') {
          e.preventDefault();
          navigateTo('calculator');
        } else if (key === 't') {
          e.preventDefault();
          navigateTo('challenges');
        }
      }
    });
  }

  // Semantic keyboard tab navigation for tablist (Item 42)
  function setupTabKeyboardNavigation() {
    const tabsList = document.querySelector('.nav-links[role="tablist"]');
    if (!tabsList) return;

    const tabs = Array.from(tabsList.querySelectorAll('button[role="tab"]'));
    tabs.forEach((tab, index) => {
      tab.addEventListener('keydown', (e) => {
        let targetIndex = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          e.preventDefault();
          targetIndex = (index + 1) % tabs.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          e.preventDefault();
          targetIndex = (index - 1 + tabs.length) % tabs.length;
        } else if (e.key === 'Home') {
          e.preventDefault();
          targetIndex = 0;
        } else if (e.key === 'End') {
          e.preventDefault();
          targetIndex = tabs.length - 1;
        }

        if (targetIndex !== null) {
          tabs[targetIndex].focus();
          tabs[targetIndex].click();
        }
      });
    });
  }

  // Input fields validation borders and error outlines (Item 39)
  function validateCalculatorForm() {
    let isValid = true;
    const numericFields = [
      'inp-car', 'inp-bike', 'inp-public', 'inp-flights',
      'inp-electricity', 'inp-ac', 'inp-appliance',
      'inp-clothing', 'inp-electronics'
    ];
    
    const limits = {
      'inp-car': 100000.0,
      'inp-bike': 10000.0,
      'inp-public': 100000.0,
      'inp-flights': 100000.0,
      'inp-electricity': 50000.0,
      'inp-ac': 744.0,
      'inp-appliance': 744.0,
      'inp-clothing': 1000.0,
      'inp-electronics': 100.0
    };

    numericFields.forEach(id => {
      const input = document.getElementById(id);
      if (!input) return;
      const val = parseFloat(input.value);
      const maxVal = limits[id] || 100000.0;
      
      if (isNaN(val) || val < 0 || val > maxVal) {
        input.classList.add('input-invalid');
        input.setAttribute('aria-invalid', 'true');
        isValid = false;
      } else {
        input.classList.remove('input-invalid');
        input.removeAttribute('aria-invalid');
      }
    });
    
    return isValid;
  }

  // --- API HELPER ---
  const API = {
    _cache: {},
    clearCache() {
      this._cache = {};
    },
    async request(endpoint, options = {}) {
      const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        ...options.headers,
      };

      if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
      }

      try {
        const response = await fetch(endpoint, { ...options, headers });
        
        if (response.status === 401 && state.token) {
          logout();
          throw new Error('Session expired. Please log in again.');
        }

        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || 'Something went wrong');
        }
        return data;
      } catch (err) {
        console.error(`API Error on ${endpoint}:`, err);
        throw err;
      }
    },
    async get(endpoint, bypassCache = false) {
      if (!bypassCache && this._cache[endpoint]) {
        return this._cache[endpoint];
      }
      const data = await this.request(endpoint, { method: 'GET' });
      this._cache[endpoint] = data;
      return data;
    },
    post(endpoint, body) {
      this.clearCache();
      return this.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(body),
      });
    },
    patch(endpoint, body) {
      this.clearCache();
      return this.request(endpoint, {
        method: 'PATCH',
        body: JSON.stringify(body),
      });
    },
  };

  // --- DOM ELEMENTS ---
  const elements = {
    header: document.getElementById('app-header'),
    userEmailDisplay: document.getElementById('user-email-display'),
    
    // Notification
    notificationBanner: document.getElementById('notification-banner'),
    notificationText: document.getElementById('notification-text'),
    closeNotification: document.getElementById('close-notification'),
    
    // Alert Banner
    bannerApiUnconfigured: document.getElementById('banner-api-unconfigured'),

    // Views
    views: {
      auth: document.getElementById('view-auth'),
      dashboard: document.getElementById('view-dashboard'),
      calculator: document.getElementById('view-calculator'),
      challenges: document.getElementById('view-challenges'),
    },
    
    // Nav Buttons
    navDashboard: document.getElementById('nav-dashboard'),
    navCalculator: document.getElementById('nav-calculator'),
    navChallenges: document.getElementById('nav-challenges'),

    // Auth Form
    formAuth: document.getElementById('form-auth'),
    inpAuthEmail: document.getElementById('inp-auth-email'),
    inpAuthPassword: document.getElementById('inp-auth-password'),
    btnAuthSubmit: document.getElementById('btn-auth-submit'),
    authTitle: document.getElementById('auth-title'),
    authSubtitle: document.getElementById('auth-subtitle'),
    authSwitchText: document.getElementById('auth-switch-text'),
    linkAuthSwitch: document.getElementById('link-auth-switch'),
    btnLogout: document.getElementById('btn-logout'),

    // Forms
    formCalculator: document.getElementById('form-calculator'),

    // Dashboard content panels
    dashboardEmpty: document.getElementById('dashboard-empty'),
    dashboardContent: document.getElementById('dashboard-content'),
    valEmissions: document.getElementById('val-emissions'),
    valPrevEmissions: document.getElementById('val-prev-emissions'),
    valPctChange: document.getElementById('val-pct-change'),
    valScore: document.getElementById('val-score'),
    valScoreBar: document.getElementById('val-score-bar'),
    valAnnual: document.getElementById('val-annual'),
    recommendationsList: document.getElementById('recommendations-list'),
    goToCalcBtns: document.querySelectorAll('.go-to-calc-btn'),

    // Calculator Steps UI
    calcStepViews: document.querySelectorAll('.calc-step-view'),
    calcStepIndicators: document.querySelectorAll('.step-indicator'),
    calcStepLines: document.querySelectorAll('.step-line'),
    calcStepLabel: document.getElementById('step-label'),
    calcResultPanel: document.getElementById('calc-result-panel'),
    resValMonth: document.getElementById('res-val-month'),
    resValYear: document.getElementById('res-val-year'),
    btnReEstimate: document.getElementById('btn-re-estimate'),
    viewDashboardBtn: document.querySelector('.view-dashboard-btn'),

    // Challenges UI
    userTotalPoints: document.getElementById('user-total-points'),
    activeChallengesWrap: document.getElementById('active-challenges-wrap'),
    activeChallengesCount: document.getElementById('active-challenges-count'),
    activeChallengesList: document.getElementById('active-challenges-list'),
    availableChallengesList: document.getElementById('available-challenges-list'),
    completedChallengesWrap: document.getElementById('completed-challenges-wrap'),
    completedChallengesList: document.getElementById('completed-challenges-list'),
    completionCelebration: document.getElementById('completion-celebration'),
    celebPointsEarned: document.getElementById('celeb-points-earned'),

    // Modals
    modalChallengeDetails: document.getElementById('modal-challenge-details'),
    modalDetailsTitle: document.getElementById('modal-details-title'),
    modalDetailsDifficulty: document.getElementById('modal-details-difficulty'),
    modalDetailsPoints: document.getElementById('modal-details-points'),
    modalDetailsDescription: document.getElementById('modal-details-description'),
    modalDetailsRulesList: document.getElementById('modal-details-rules-list'),
    btnModalDetailsAction: document.getElementById('btn-modal-details-action'),

    modalChallengeProof: document.getElementById('modal-challenge-proof'),
    formChallengeProof: document.getElementById('form-challenge-proof'),
    inpProofText: document.getElementById('inp-proof-text'),
    inpProofImage: document.getElementById('inp-proof-image'),

    // Theme toggle & Filter buttons
    btnThemeToggle: document.getElementById('btn-theme-toggle'),
    filterButtons: document.querySelectorAll('.filter-btn'),
  };

  // --- NOTIFICATION BANNER UTILITY ---
  function showNotification(message, type = 'error') {
    elements.notificationText.textContent = message;
    
    // Clean classes
    elements.notificationBanner.firstElementChild.className = 'notification-card';
    if (type === 'success') {
      elements.notificationBanner.firstElementChild.classList.add('success');
    } else if (type === 'info') {
      elements.notificationBanner.firstElementChild.classList.add('info');
    }
    
    elements.notificationBanner.classList.remove('hidden');
    
    // Auto hide after 5 seconds
    setTimeout(() => {
      elements.notificationBanner.classList.add('hidden');
    }, 5000);
  }

  elements.closeNotification.addEventListener('click', () => {
    elements.notificationBanner.classList.add('hidden');
  });

  // --- ROUTER VIEW TOGGLER ---
  function navigateTo(viewName) {
    if (!state.token) {
      viewName = 'auth';
    }

    // Hide all views
    Object.values(elements.views).forEach(view => {
      if (view) view.classList.add('hidden');
    });
    
    // Show selected view
    if (elements.views[viewName]) {
      elements.views[viewName].classList.remove('hidden');
    }

    // Toggle navigation headers based on auth state
    if (viewName === 'auth') {
      elements.header.classList.add('hidden');
      elements.btnLogout.classList.add('hidden');
    } else {
      elements.header.classList.remove('hidden');
      elements.btnLogout.classList.remove('hidden');
    }

    // Toggle navigation button actives
    elements.navDashboard.classList.remove('active');
    elements.navCalculator.classList.remove('active');
    elements.navChallenges.classList.remove('active');
    
    elements.navDashboard.removeAttribute('aria-current');
    elements.navCalculator.removeAttribute('aria-current');
    elements.navChallenges.removeAttribute('aria-current');

    elements.navDashboard.setAttribute('aria-selected', 'false');
    elements.navCalculator.setAttribute('aria-selected', 'false');
    elements.navChallenges.setAttribute('aria-selected', 'false');

    // Accessibility route transition announcement
    const announcer = document.getElementById('route-announcer');
    if (announcer) {
      announcer.textContent = `Navigated to ${viewName.charAt(0).toUpperCase() + viewName.slice(1)} view`;
    }

    if (viewName === 'dashboard') {
      elements.navDashboard.classList.add('active');
      elements.navDashboard.setAttribute('aria-current', 'page');
      elements.navDashboard.setAttribute('aria-selected', 'true');
      loadDashboard();
    } else if (viewName === 'calculator') {
      elements.navCalculator.classList.add('active');
      elements.navCalculator.setAttribute('aria-current', 'page');
      elements.navCalculator.setAttribute('aria-selected', 'true');
      resetCalculator();
    } else if (viewName === 'challenges') {
      elements.navChallenges.classList.add('active');
      elements.navChallenges.setAttribute('aria-current', 'page');
      elements.navChallenges.setAttribute('aria-selected', 'true');
      loadChallenges();
    }
  }

  // Bind nav clicks
  elements.navDashboard.addEventListener('click', () => navigateTo('dashboard'));
  elements.navCalculator.addEventListener('click', () => navigateTo('calculator'));
  elements.navChallenges.addEventListener('click', () => navigateTo('challenges'));
  
  elements.goToCalcBtns.forEach(btn => {
    btn.addEventListener('click', () => navigateTo('calculator'));
  });



  // --- DASHBOARD SERVICE LOADERS ---
  async function loadDashboard() {
    try {
      const [summary, history, recommendations, activeProgress] = await Promise.all([
        API.get('/api/analytics/summary'),
        API.get(`/api/analytics/history?filter=${state.historyFilter}`),
        API.get('/api/recommendations/'),
        API.get('/api/challenges/active'),
      ]);

      if (summary.current_month_emissions === 0 && recommendations.length === 0) {
        elements.dashboardEmpty.classList.remove('hidden');
        elements.dashboardContent.classList.add('hidden');
        return;
      }

      elements.dashboardEmpty.classList.add('hidden');
      elements.dashboardContent.classList.remove('hidden');

      // 1. Metric Cards
      elements.valEmissions.textContent = summary.current_month_emissions.toFixed(2);
      elements.valPrevEmissions.textContent = `Previous: ${summary.previous_month_emissions.toFixed(2)} kg`;
      
      const pctVal = summary.reduction_percentage;
      elements.valPctChange.textContent = `${pctVal > 0 ? '↓' : pctVal < 0 ? '↑' : ''} ${Math.abs(pctVal)}%`;
      elements.valPctChange.className = 'trend-badge';
      if (pctVal > 0) {
        elements.valPctChange.classList.add('green');
      } else if (pctVal < 0) {
        elements.valPctChange.classList.add('red');
      }

      elements.valScore.textContent = summary.sustainability_score;
      elements.valScoreBar.style.width = `${summary.sustainability_score}%`;
      elements.valScoreBar.setAttribute('aria-valuenow', summary.sustainability_score);
      elements.valAnnual.textContent = Math.round(summary.current_month_emissions * 12).toLocaleString();

      state.sustainabilityScore = summary.sustainability_score;

      // Calculate total reward points (Item 49, 53)
      const totalPoints = activeProgress
        .filter(p => p.completion_status === 'completed')
        .reduce((sum, p) => sum + p.points_earned, 0);
      state.rewardPoints = totalPoints;

      // Render Dynamic Gamification and Greeting widgets
      updateLevelAndProgression(totalPoints);
      updateDashboardGreeting();
      setupShareButton(totalPoints);

      // 2. Render Line Chart
      renderHistoryChart(history.trends);

      // 3. Render Pie Chart
      renderPieChart(summary.category_breakdown_percentages, summary.category_breakdown_values);

      // 4. Render Comparison Bar Chart
      renderComparisonChart(summary.current_month_emissions, summary.national_average, summary.global_average);

      // 5. Render Recommendations
      renderRecommendations(recommendations);

    } catch (err) {
      showNotification('Failed to fetch dashboard metrics.', 'error');
    }
  }

  async function updateHistoryChart() {
    try {
      const history = await API.get(`/api/analytics/history?filter=${state.historyFilter}`);
      renderHistoryChart(history.trends);
      // Accessibility: Announce timeline chart update
      const announcer = document.getElementById('route-announcer');
      if (announcer) {
        announcer.textContent = `Emissions history chart updated to display ${state.historyFilter === 'ytd' ? 'Year-to-Date' : state.historyFilter + ' filter'} data`;
      }
    } catch (err) {
      showNotification('Failed to fetch historical carbon data.', 'error');
    }
  }

  function renderHistoryChart(trends) {
    const ctx = document.getElementById('chart-history').getContext('2d');
    
    // Destroy previous instance
    if (state.charts.history) {
      state.charts.history.destroy();
    }

    if (!trends || trends.length === 0) {
      return;
    }

    state.charts.history = new Chart(ctx, {
      type: 'line',
      data: {
        labels: trends.map(t => t.label),
        datasets: [{
          label: 'Emissions (kg CO₂)',
          data: trends.map(t => t.emissions),
          fill: true,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          tension: 0.4,
          borderWidth: 2,
          pointBackgroundColor: '#10b981',
          pointHoverBackgroundColor: '#fff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            titleColor: '#fff',
            bodyColor: '#e2e8f0',
            borderColor: '#334155',
            borderWidth: 1
          }
        },
        scales: {
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#94a3b8' }
          }
        }
      }
    });
  }

  function renderPieChart(percentages, values) {
    const ctx = document.getElementById('chart-pie').getContext('2d');

    // Destroy previous instance
    if (state.charts.pie) {
      state.charts.pie.destroy();
    }

    if (!percentages) return;

    state.charts.pie = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Transportation', 'Energy', 'Food', 'Shopping', 'Waste'],
        datasets: [{
          data: [
            percentages.transportation,
            percentages.energy,
            percentages.food,
            percentages.shopping,
            percentages.waste
          ],
          backgroundColor: ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444'],
          borderWidth: 1,
          borderColor: '#1e293b'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#94a3b8',
              boxWidth: 10,
              font: { size: 10 }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const pct = percentages[label.toLowerCase()] || 0;
                const value = values ? (values[label.toLowerCase()] || 0) : 0;
                return ` ${label}: ${value.toFixed(1)} kg (${pct.toFixed(1)}%)`;
              }
            }
          }
        }
      }
    });
  }

  function renderComparisonChart(userVal, nationalVal, globalVal) {
    const ctx = document.getElementById('chart-comparison').getContext('2d');

    if (state.charts.comparison) {
      state.charts.comparison.destroy();
    }

    state.charts.comparison = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Your Footprint', 'National Average', 'Global Target'],
        datasets: [{
          label: 'Emissions (kg CO₂)',
          data: [userVal, nationalVal, globalVal],
          backgroundColor: ['#10b981', '#ef4444', '#3b82f6'],
          borderWidth: 1,
          borderColor: '#1e293b'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            titleColor: '#fff',
            bodyColor: '#e2e8f0',
            borderColor: '#334155',
            borderWidth: 1
          }
        },
        scales: {
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#94a3b8' }
          }
        }
      }
    });
  }

  function renderRecommendations(recs) {
    elements.recommendationsList.innerHTML = '';
    
    if (recs.length === 0) {
      elements.recommendationsList.innerHTML = `
        <div class="text-center py-6 text-muted w-full">
          <p>No recommendations active. Go to the Calculator to generate some!</p>
        </div>
      `;
      return;
    }

    recs.forEach(rec => {
      const card = document.createElement('div');
      card.className = `rec-card ${rec.is_completed ? 'completed' : ''}`;
      
      const difficultyClass = rec.difficulty.toLowerCase();
      
      card.innerHTML = `
        <div>
          <div class="rec-top">
            <span class="difficulty-badge ${difficultyClass}">${rec.difficulty}</span>
            <div class="rec-stats">
              <span class="red-stat">-${rec.expected_reduction} kg CO₂</span>
              <span class="text-muted">|</span>
              <span class="green-stat">$${rec.estimated_savings} saved</span>
            </div>
          </div>
          <h4>${rec.title}</h4>
          <p>${rec.description}</p>
        </div>
        <div class="rec-action">
          <button class="btn-complete ${rec.is_completed ? 'undo' : ''}" data-id="${rec.id}" type="button">
            <svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            <span>${rec.is_completed ? 'Undo Complete' : 'Mark Completed'}</span>
          </button>
        </div>
      `;

      // Complete toggle click
      card.querySelector('.btn-complete').addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        btn.disabled = true;
        try {
          await API.patch(`/api/recommendations/${rec.id}/complete`);
          loadDashboard(); // Refresh
        } catch (err) {
          showNotification('Failed to complete recommendation.', 'error');
          btn.disabled = false;
        }
      });

      elements.recommendationsList.appendChild(card);
    });
  }

  // --- CALCULATOR WIZARD CONTROLS ---
  function resetCalculator() {
    state.calculatorStep = 1;
    elements.calcResultPanel.classList.add('hidden');
    elements.formCalculator.parentElement.classList.remove('hidden');
    elements.formCalculator.reset();
    showStep(1);
  }

  function showStep(stepNum) {
    // Toggle hidden steps
    elements.calcStepViews.forEach(view => {
      if (parseInt(view.dataset.step) === stepNum) {
        view.classList.remove('hidden');
      } else {
        view.classList.add('hidden');
      }
    });

    // Update indicators
    elements.calcStepIndicators.forEach(ind => {
      const step = parseInt(ind.dataset.step);
      if (step <= stepNum) {
        ind.classList.add('active');
      } else {
        ind.classList.remove('active');
      }
    });

    // Update lines
    elements.calcStepLines.forEach((line, index) => {
      if (index + 1 < stepNum) {
        line.classList.add('active');
      } else {
        line.classList.remove('active');
      }
    });

    // Update step label
    const labels = [
      'Step 1: Transportation',
      'Step 2: Energy & Diet',
      'Step 3: Habits & Shopping'
    ];
    elements.calcStepLabel.textContent = labels[stepNum - 1];
  }

  // Bind step actions
  document.querySelectorAll('.next-step-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.calculatorStep = Math.min(state.calculatorStep + 1, 3);
      showStep(state.calculatorStep);
    });
  });

  document.querySelectorAll('.prev-step-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.calculatorStep = Math.max(state.calculatorStep - 1, 1);
      showStep(state.calculatorStep);
    });
  });

  // Handle calculator submission
  elements.formCalculator.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Perform client-side validation check (Item 39)
    if (!validateCalculatorForm()) {
      showNotification('Please correct highlighted fields exceeding maximum constraints.', 'error');
      const firstInvalid = elements.formCalculator.querySelector('.input-invalid');
      if (firstInvalid) firstInvalid.focus();
      return;
    }
    
    // Disable submit button during load
    const submitBtn = elements.formCalculator.querySelector('.submit-calc-btn');
    const originalContent = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span>Calculating...</span>';
    submitBtn.disabled = true;

    // Collect values
    const payload = {
      transportation_car: parseFloat(document.getElementById('inp-car').value) || 0,
      transportation_bike: parseFloat(document.getElementById('inp-bike').value) || 0,
      transportation_public: parseFloat(document.getElementById('inp-public').value) || 0,
      transportation_flights: parseFloat(document.getElementById('inp-flights').value) || 0,
      energy_electricity: parseFloat(document.getElementById('inp-electricity').value) || 0,
      energy_ac: parseFloat(document.getElementById('inp-ac').value) || 0,
      energy_appliance: parseFloat(document.getElementById('inp-appliance').value) || 0,
      food_preference: document.getElementById('inp-food').value,
      shopping_clothing: parseFloat(document.getElementById('inp-clothing').value) || 0,
      shopping_electronics: parseFloat(document.getElementById('inp-electronics').value) || 0,
      waste_recycling: document.getElementById('inp-recycling').value,
      waste_plastic: document.getElementById('inp-plastic').value,
    };

    try {
      const data = await API.post('/api/calculator/submit', payload);
      
      // Load Step 4 Results screen
      elements.resValMonth.textContent = data.total_emissions.toFixed(2);
      elements.resValYear.textContent = Math.round(data.total_emissions * 12).toLocaleString();
      
      elements.formCalculator.parentElement.classList.add('hidden');
      elements.calcResultPanel.classList.remove('hidden');

    } catch (err) {
      showNotification(err.message || 'An error occurred during calculation.', 'error');
    } finally {
      submitBtn.innerHTML = originalContent;
      submitBtn.disabled = false;
    }
  });

  // Result actions
  elements.btnReEstimate.addEventListener('click', () => {
    resetCalculator();
  });

  elements.viewDashboardBtn.addEventListener('click', () => {
    navigateTo('dashboard');
  });

  // --- CHALLENGES SERVICES & MODALS ---
  let activeProofProgressId = null;
  let activeProofPoints = 0;
  let triggeringElement = null;

  // Modal keydown handler (Focus Trap + Escape to close)
  function handleModalKeydown(e, modalEl) {
    if (e.key === 'Escape') {
      closeModals();
      e.preventDefault();
      return;
    }
    if (e.key !== 'Tab') return;
    const focusable = Array.from(modalEl.querySelectorAll('input, select, textarea, button, a, [tabindex="0"]')).filter(el => {
      return el.tabIndex >= 0 && !el.disabled && el.offsetParent !== null;
    });
    if (focusable.length === 0) return;
    const firstEl = focusable[0];
    const lastEl = focusable[focusable.length - 1];

    if (e.shiftKey) { // Shift + Tab
      if (document.activeElement === firstEl) {
        lastEl.focus();
        e.preventDefault();
      }
    } else { // Tab
      if (document.activeElement === lastEl) {
        firstEl.focus();
        e.preventDefault();
      }
    }
  }

  if (elements.modalChallengeDetails) {
    elements.modalChallengeDetails.addEventListener('keydown', (e) => handleModalKeydown(e, elements.modalChallengeDetails));
  }
  if (elements.modalChallengeProof) {
    elements.modalChallengeProof.addEventListener('keydown', (e) => handleModalKeydown(e, elements.modalChallengeProof));
  }

  function closeModals() {
    elements.modalChallengeDetails.classList.add('hidden');
    elements.modalChallengeProof.classList.add('hidden');
    elements.formChallengeProof.reset();
    if (triggeringElement) {
      triggeringElement.focus();
      triggeringElement = null;
    }
  }

  document.querySelectorAll('.modal-close-btn').forEach(btn => {
    btn.addEventListener('click', closeModals);
  });
  
  const closeProofBtn = document.querySelector('.btn-close-proof');
  if (closeProofBtn) {
    closeProofBtn.addEventListener('click', closeModals);
  }

  function openChallengeDetailsModal(challenge, status, triggerBtn) {
    triggeringElement = triggerBtn || document.activeElement;
    elements.modalDetailsTitle.textContent = challenge.title;
    elements.modalDetailsDifficulty.textContent = challenge.difficulty;
    elements.modalDetailsDifficulty.className = `difficulty-badge ${challenge.difficulty.toLowerCase()}`;
    elements.modalDetailsPoints.textContent = `+${challenge.points} pts`;

    // Parse description and rules from string formatting
    const descParts = challenge.description.split('\n\nRules & Habits:\n');
    elements.modalDetailsDescription.textContent = descParts[0] || '';

    elements.modalDetailsRulesList.innerHTML = '';
    const rulesWrap = document.getElementById('modal-details-rules-wrap');
    if (descParts[1] && rulesWrap) {
      const rules = descParts[1].split('\n');
      rules.forEach(rule => {
        const cleanRule = rule.replace(/^\d+\.\s*/, '');
        if (cleanRule.trim()) {
          const li = document.createElement('li');
          li.textContent = cleanRule;
          elements.modalDetailsRulesList.appendChild(li);
        }
      });
      rulesWrap.classList.remove('hidden');
    } else if (rulesWrap) {
      rulesWrap.classList.add('hidden');
    }

    const btn = elements.btnModalDetailsAction;
    if (btn) {
      btn.disabled = false;
      btn.className = 'btn btn-primary';

      if (status.isCompleted) {
        btn.textContent = '✓ Already Completed';
        btn.disabled = true;
      } else if (status.isActive) {
        btn.textContent = 'Mark Completed';
        btn.onclick = () => {
          closeModals();
          openProofModal(status.progressId, challenge.points);
        };
      } else {
        btn.textContent = 'Join Challenge';
        btn.onclick = async () => {
          btn.disabled = true;
          btn.textContent = 'Joining...';
          try {
            await API.post('/api/challenges/join', { challenge_id: challenge.id });
            closeModals();
            loadChallenges();
            showNotification('Joined challenge successfully!', 'success');
          } catch (err) {
            showNotification('Failed to join challenge.', 'error');
            btn.disabled = false;
            btn.textContent = 'Join Challenge';
          }
        };
      }
    }

    elements.modalChallengeDetails.classList.remove('hidden');
    setTimeout(() => {
      const firstFocusable = elements.modalChallengeDetails.querySelector('button, [tabindex="0"]');
      if (firstFocusable) firstFocusable.focus();
    }, 50);
  }

  function openProofModal(progressId, points, triggerBtn) {
    triggeringElement = triggerBtn || document.activeElement;
    activeProofProgressId = progressId;
    activeProofPoints = points;
    elements.modalChallengeProof.classList.remove('hidden');
    setTimeout(() => {
      elements.inpProofText.focus();
    }, 50);
  }

  if (elements.formChallengeProof) {
    elements.formChallengeProof.addEventListener('submit', async (e) => {
      e.preventDefault();
      const proofText = elements.inpProofText.value.trim();
      if (!proofText) return;

      let proofImage = "";
      const imageFile = elements.inpProofImage?.files?.[0];
      if (imageFile) {
        if (imageFile.size > 1.5 * 1024 * 1024) {
          showNotification('Proof image exceeds 1.5MB size limit.', 'error');
          return;
        }
        try {
          proofImage = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error("File reading failed"));
            reader.readAsDataURL(imageFile);
          });
        } catch (fileErr) {
          showNotification('Failed to read image file.', 'error');
          return;
        }
      }

      const submitBtn = elements.formChallengeProof.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';

      try {
        await API.post(`/api/challenges/${activeProofProgressId}/complete`, {
          proof_text: proofText,
          proof_image: proofImage
        });
        closeModals();
        
        // Celebration Toast trigger
        elements.celebPointsEarned.textContent = activeProofPoints;
        elements.completionCelebration.classList.remove('hidden');
        setTimeout(() => {
          elements.completionCelebration.classList.add('hidden');
        }, 4000);

        loadChallenges();
      } catch (err) {
        showNotification('Failed to submit completion proof.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }

  async function loadChallenges() {
    try {
      const [challenges, activeProgress] = await Promise.all([
        API.get('/api/challenges/'),
        API.get('/api/challenges/active'),
      ]);

      // Calculate total reward points
      const totalPoints = activeProgress
        .filter(p => p.completion_status === 'completed')
        .reduce((sum, p) => sum + p.points_earned, 0);

      elements.userTotalPoints.textContent = `${totalPoints} pts`;
      state.rewardPoints = totalPoints;

      // Update User Level progression (Item 49, 53) and dynamic Badges (Item 52)
      updateLevelAndProgression(totalPoints);
      renderBadgesList(totalPoints, state.sustainabilityScore);

      const activeList = activeProgress.filter(p => p.completion_status === 'in_progress');
      elements.activeChallengesCount.textContent = activeList.length;

      // 1. Render active challenges list
      elements.activeChallengesList.innerHTML = '';
      if (activeList.length > 0) {
        elements.activeChallengesWrap.classList.remove('hidden');
        
        activeList.forEach(prog => {
          const card = document.createElement('div');
          card.className = 'challenge-card glass-panel cursor-pointer';
          card.tabIndex = 0;
          
          const endDate = new Date(prog.end_date).toLocaleDateString();

          card.innerHTML = `
            <div>
              <div class="challenge-top">
                <span class="difficulty-badge ${prog.challenge.difficulty.toLowerCase()}">${prog.challenge.difficulty}</span>
                <span class="challenge-pts">+${prog.challenge.points} pts</span>
              </div>
              <h3>${prog.challenge.title}</h3>
              <p>${prog.challenge.description.split('\n\n')[0]}</p>
            </div>
            <div class="challenge-footer">
              <span class="challenge-date">Ends: ${endDate}</span>
              <button class="btn btn-primary btn-complete-challenge" data-progress-id="${prog.id}" data-points="${prog.challenge.points}" type="button">
                Complete
              </button>
            </div>
          `;

          // Card click to show rules
          card.addEventListener('click', (e) => {
            if (e.target.closest('button')) return;
            openChallengeDetailsModal(prog.challenge, { isActive: true, progressId: prog.id }, card);
          });

          // Keyboard Enter/Space support
          card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              if (e.target.closest('button')) return;
              e.preventDefault();
              openChallengeDetailsModal(prog.challenge, { isActive: true, progressId: prog.id }, card);
            }
          });

          // Mark complete click
          card.querySelector('.btn-complete-challenge').addEventListener('click', (e) => {
            e.stopPropagation();
            openProofModal(prog.id, prog.challenge.points, e.currentTarget);
          });

          elements.activeChallengesList.appendChild(card);
        });
      } else {
        elements.activeChallengesWrap.classList.add('hidden');
      }

      // Helper status check function
      const getChallengeStatus = (chalId) => {
        const active = activeProgress.find(p => p.challenge_id === chalId && p.completion_status === 'in_progress');
        if (active) return { isActive: true, progressId: active.id };
        
        const completed = activeProgress.some(p => p.challenge_id === chalId && p.completion_status === 'completed');
        if (completed) return { isCompleted: true };
        
        return {};
      };

      // 2. Render available challenges list (filtered to exclude completed)
      elements.availableChallengesList.innerHTML = '';
      challenges.forEach(chal => {
        const status = getChallengeStatus(chal.id);
        if (status.isCompleted) return;

        const card = document.createElement('div');
        card.className = 'challenge-card glass-panel cursor-pointer';
        card.tabIndex = 0;
        
        let footerContent = '';
        if (status.isActive) {
          footerContent = `
            <button class="btn btn-primary btn-complete-challenge" data-progress-id="${status.progressId}" data-points="${chal.points}" type="button">
              Complete
            </button>
          `;
        } else {
          footerContent = `
            <button class="btn btn-secondary btn-join-challenge" data-id="${chal.id}" type="button">
              Join Challenge
            </button>
          `;
        }

        card.innerHTML = `
          <div>
            <div class="challenge-top">
              <span class="difficulty-badge ${chal.difficulty.toLowerCase()}">${chal.difficulty}</span>
              <span class="challenge-pts">+${chal.points} pts</span>
            </div>
            <h3>${chal.title}</h3>
            <p>${chal.description.split('\n\n')[0]}</p>
          </div>
          <div class="challenge-footer">
            <span></span> <!-- empty alignment -->
            ${footerContent}
          </div>
        `;

        // Card click to show rules
        card.addEventListener('click', (e) => {
          if (e.target.closest('button')) return;
          openChallengeDetailsModal(chal, status, card);
        });

        // Keyboard Enter/Space support
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            if (e.target.closest('button')) return;
            e.preventDefault();
            openChallengeDetailsModal(chal, status, card);
          }
        });

        // Join click
        const joinBtn = card.querySelector('.btn-join-challenge');
        if (joinBtn) {
          joinBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const btn = e.currentTarget;
            btn.disabled = true;
            try {
              await API.post('/api/challenges/join', { challenge_id: chal.id });
              loadChallenges(); // Refresh
            } catch (err) {
              showNotification(err.message || 'Failed to join challenge.', 'error');
              btn.disabled = false;
            }
          });
        }

        // Active complete inside available block
        const compBtn = card.querySelector('.btn-complete-challenge');
        if (compBtn) {
          compBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            openProofModal(status.progressId, chal.points, e.currentTarget);
          });
        }

        elements.availableChallengesList.appendChild(card);
      });

      // 3. Render completed challenges history list
      const completedList = activeProgress.filter(p => p.completion_status === 'completed');
      elements.completedChallengesList.innerHTML = '';
      if (completedList.length > 0) {
        elements.completedChallengesWrap.classList.remove('hidden');
        
        completedList.forEach(prog => {
          const card = document.createElement('div');
          card.className = 'challenge-card glass-panel completed';
          
          card.innerHTML = `
            <div>
              <div class="challenge-top">
                <span class="difficulty-badge ${prog.challenge.difficulty.toLowerCase()}">${prog.challenge.difficulty}</span>
                <span class="challenge-pts">+${prog.challenge.points} pts</span>
              </div>
              <h3>${prog.challenge.title}</h3>
              <p class="text-sm font-semibold text-emerald-400">✓ Completed successfully</p>
              ${prog.proof_text ? `<p class="mt-2 text-xs italic text-slate-400">Proof: "${escapeHTML(prog.proof_text)}"</p>` : ''}
              ${prog.proof_image ? `<div class="mt-2"><img src="${prog.proof_image}" alt="Proof image for ${escapeHTML(prog.challenge.title)}" class="proof-img-preview" style="max-width: 100%; max-height: 150px; border-radius: var(--radius-sm); border: 1px solid var(--panel-border); margin-top: 0.5rem; display: block;" /></div>` : ''}
            </div>
          `;
          elements.completedChallengesList.appendChild(card);
        });
      } else {
        elements.completedChallengesWrap.classList.add('hidden');
      }

    } catch (err) {
      showNotification('Failed to load challenges.', 'error');
    }
  }

  // --- AUTHENTICATION ACTIONS & HANDLERS ---
  function logout() {
    state.token = null;
    localStorage.removeItem('auth_token');
    elements.userEmailDisplay.textContent = 'Eco Citizen';
    const navLevelBadge = document.getElementById('nav-level-badge-container');
    if (navLevelBadge) navLevelBadge.classList.add('hidden');
    API.clearCache();
    navigateTo('auth');
  }

  if (elements.btnLogout) {
    elements.btnLogout.addEventListener('click', () => {
      // Interactive Logout Dialog box check (Item 47)
      if (confirm('Are you sure you want to sign out of EcoTrack AI?')) {
        logout();
        showNotification('Logged out successfully.', 'success');
      }
    });
  }

  // Toggle Auth mode (login vs register)
  if (elements.linkAuthSwitch) {
    elements.linkAuthSwitch.addEventListener('click', (e) => {
      e.preventDefault();
      state.isRegistering = !state.isRegistering;
      
      if (state.isRegistering) {
        elements.authTitle.textContent = 'Create account';
        elements.authSubtitle.textContent = 'Join EcoTrack AI to monitor and reduce your footprint.';
        elements.btnAuthSubmit.textContent = 'Create Account';
        elements.authSwitchText.textContent = 'Already have an account?';
        elements.linkAuthSwitch.textContent = 'Sign in';
      } else {
        elements.authTitle.textContent = 'Welcome back';
        elements.authSubtitle.textContent = 'Sign in to your EcoTrack AI account to continue.';
        elements.btnAuthSubmit.textContent = 'Sign In';
        elements.authSwitchText.textContent = "Don't have an account?";
        elements.linkAuthSwitch.textContent = 'Create account';
      }
      elements.formAuth.reset();
    });
  }

  // Handle Auth submission
  if (elements.formAuth) {
    elements.formAuth.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = elements.inpAuthEmail.value.trim();
      const password = elements.inpAuthPassword.value;
      
      elements.btnAuthSubmit.disabled = true;
      const originalText = elements.btnAuthSubmit.textContent;
      elements.btnAuthSubmit.textContent = state.isRegistering ? 'Creating Account...' : 'Signing In...';
      
      const endpoint = state.isRegistering ? '/api/auth/register' : '/api/auth/login';
      
      try {
        const data = await API.post(endpoint, { email, password });
        state.token = data.token;
        localStorage.setItem('auth_token', data.token);
        elements.userEmailDisplay.textContent = data.user.email;
        
        showNotification(state.isRegistering ? 'Account created successfully!' : 'Signed in successfully!', 'success');
        navigateTo('dashboard');
      } catch (err) {
        showNotification(err.message || 'Authentication failed', 'error');
      } finally {
        elements.btnAuthSubmit.disabled = false;
        elements.btnAuthSubmit.textContent = originalText;
      }
    });
  }

  // --- TIME WINDOW FILTER BUTTONS HANDLER ---
  elements.filterButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      elements.filterButtons.forEach(b => b.classList.remove('active'));
      e.currentTarget.classList.add('active');
      state.historyFilter = e.currentTarget.dataset.filter;
      updateHistoryChart();
    });
  });



  // --- GEMINI API STATUS ALERTS ---
  async function checkGeminiStatus() {
    try {
      const status = await API.get('/api/recommendations/status');
      if (status.gemini_configured) {
        elements.bannerApiUnconfigured.classList.add('hidden');
      } else {
        elements.bannerApiUnconfigured.classList.remove('hidden');
      }
    } catch (err) {
      console.warn('Could not check Gemini API key configuration state.', err);
    }
  }

  // --- WIZARD ACCESSIBILITY KEYBOARD TAB FOCUS TRAP ---
  if (elements.formCalculator) {
    elements.formCalculator.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab') return;
      
      const activeStepView = document.querySelector(`.calc-step-view[data-step="${state.calculatorStep}"]`);
      if (!activeStepView) return;

      const focusable = Array.from(activeStepView.querySelectorAll('input, select, button')).filter(el => {
        return el.tabIndex >= 0 && !el.disabled && el.offsetParent !== null;
      });

      if (focusable.length === 0) return;

      const firstEl = focusable[0];
      const lastEl = focusable[focusable.length - 1];

      if (e.shiftKey) { // Shift + Tab
        if (document.activeElement === firstEl) {
          lastEl.focus();
          e.preventDefault();
        }
      } else { // Tab
        if (document.activeElement === lastEl) {
          firstEl.focus();
          e.preventDefault();
        }
      }
    });
  }

  // --- INITIAL CHECK ---
  async function initAuth() {
    setupNavigationShortcuts();   // Enable Alt-key keyboard shortcuts (Item 40)
    setupTabKeyboardNavigation(); // Enable Left/Right Arrow keyboard tablist navigation (Item 42)
    setupThemeToggle();           // Enable theme toggle with aria-pressed announcer (Item 88, 96)
    setupDebouncedResize();       // Debounced resize observer for charts (Item 44)
    setupLocalStorageCache();     // Local session cache for performance (Item 58)
    setupModalFocusTrap();        // Keyboard focus trap for modals (Item 82)

    if (state.token) {
      try {
        const user = await API.get('/api/auth/me');
        elements.userEmailDisplay.textContent = user.email;
        checkGeminiStatus();
        navigateTo('dashboard');
      } catch (err) {
        console.warn('Initial session validation failed', err);
      }
    } else {
      navigateTo('auth');
    }
  }

  // --- PHASE 3: DEBOUNCE UTILITY (Item 44, 50) ---
  /**
   * Generic debounce utility to limit function call frequency.
   * Used for resize listeners and keyboard input handlers (Items 44, 50).
   */
  function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // --- PHASE 3: DEBOUNCED WINDOW RESIZE LISTENER (Item 44) ---
  function setupDebouncedResize() {
    const handleResize = debounce(() => {
      // Re-render chart canvases on window resize to ensure responsiveness
      if (state.charts.history) {
        state.charts.history.resize();
      }
      if (state.charts.pie) {
        state.charts.pie.resize();
      }
      if (state.charts.comparison) {
        state.charts.comparison.resize();
      }
    }, 250);

    window.addEventListener('resize', handleResize, { passive: true });
  }

  // --- PHASE 3: LOCAL STORAGE SESSION CACHE (Item 58) ---
  const SessionCache = {
    _prefix: 'ecotrack_cache_',
    _ttlMs: 5 * 60 * 1000, // 5 minutes

    set(key, value) {
      try {
        const entry = { value, timestamp: Date.now() };
        localStorage.setItem(this._prefix + key, JSON.stringify(entry));
      } catch (e) {
        // Gracefully handle storage quota exceeded
        console.warn('[SessionCache] Could not write to localStorage:', e.message);
      }
    },

    get(key) {
      try {
        const raw = localStorage.getItem(this._prefix + key);
        if (!raw) return null;
        const entry = JSON.parse(raw);
        if (Date.now() - entry.timestamp > this._ttlMs) {
          localStorage.removeItem(this._prefix + key);
          return null;
        }
        return entry.value;
      } catch (e) {
        return null;
      }
    },

    clear(key) {
      localStorage.removeItem(this._prefix + key);
    }
  };

  function setupLocalStorageCache() {
    // Cache auth token for quick session restore already done via state.token
    // Pre-cache user's last dashboard data for instant first render
    const cachedSummary = SessionCache.get('dashboard_summary');
    if (cachedSummary && elements.valEmissions) {
      elements.valEmissions.textContent = cachedSummary.emissions?.toFixed(2) || '0.00';
      elements.valScore.textContent = cachedSummary.score || '0';
    }
  }

  // --- PHASE 5: THEME TOGGLE WITH ARIA-PRESSED & ANNOUNCER (Items 88, 96) ---
  function setupThemeToggle() {
    if (!elements.btnThemeToggle) return;

    // Restore theme preference
    const savedTheme = localStorage.getItem('ecotrack_theme') || 'dark';
    applyTheme(savedTheme, false);

    elements.btnThemeToggle.addEventListener('click', () => {
      const isLight = document.body.classList.contains('light-theme');
      const newTheme = isLight ? 'dark' : 'light';
      applyTheme(newTheme, true);
      localStorage.setItem('ecotrack_theme', newTheme);
    });
  }

  function applyTheme(theme, announce) {
    const isLight = theme === 'light';

    // Toggle body class for CSS style overrides
    if (isLight) {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }

    document.documentElement.setAttribute('data-theme', theme);

    if (elements.btnThemeToggle) {
      elements.btnThemeToggle.setAttribute('aria-pressed', String(isLight));
      const sunIcon = elements.btnThemeToggle.querySelector('.sun-icon');
      const moonIcon = elements.btnThemeToggle.querySelector('.moon-icon');
      if (sunIcon) sunIcon.classList.toggle('hidden', isLight);
      if (moonIcon) moonIcon.classList.toggle('hidden', !isLight);
    }

    // Dynamic Theme Switch Announcer (Item 88)
    if (announce) {
      const announcer = document.getElementById('theme-change-announcer');
      if (announcer) {
        announcer.textContent = `Theme switched to ${isLight ? 'light' : 'dark'} mode`;
        setTimeout(() => { announcer.textContent = ''; }, 3000);
      }
      showNotification(`Switched to ${isLight ? 'light' : 'dark'} theme.`, 'info');
    }
  }

  // --- PHASE 5: FORM SUBMISSION STATUS ANNOUNCER (Item 91) ---
  function announceFormStatus(message) {
    const announcer = document.getElementById('form-status-announcer');
    if (announcer) {
      announcer.textContent = message;
      setTimeout(() => { announcer.textContent = ''; }, 5000);
    }
  }

  // Override showNotification to also announce for screen readers
  const _origShowNotification = showNotification;

  // --- PHASE 5: MODAL KEYBOARD FOCUS TRAP (Item 82) ---
  function setupModalFocusTrap() {
    const modalDetails = elements.modalChallengeDetails;
    const modalProof = elements.modalChallengeProof;

    [modalDetails, modalProof].forEach(modal => {
      if (!modal) return;

      modal.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab') {
          // Close modal on Escape
          if (e.key === 'Escape') {
            modal.classList.add('hidden');
            document.body.classList.remove('modal-open');
          }
          return;
        }

        const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        const focusableElements = Array.from(modal.querySelectorAll(focusableSelectors))
          .filter(el => !el.disabled && el.offsetParent !== null);

        if (focusableElements.length === 0) return;

        const firstEl = focusableElements[0];
        const lastEl = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          // Shift + Tab: wrap from first to last
          if (document.activeElement === firstEl) {
            e.preventDefault();
            lastEl.focus();
          }
        } else {
          // Tab: wrap from last to first
          if (document.activeElement === lastEl) {
            e.preventDefault();
            firstEl.focus();
          }
        }
      });
    });

    // Track modal open state for CSS
    const observerConfig = { attributes: true, attributeFilter: ['class'] };
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        const target = mutation.target;
        const isOpen = !target.classList.contains('hidden');
        if (isOpen) {
          document.body.classList.add('modal-open');
          // Move focus into the modal
          const firstFocusable = target.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
          if (firstFocusable) {
            setTimeout(() => firstFocusable.focus(), 50);
          }
        } else {
          // Return focus to trigger button when modal closes
          document.body.classList.remove('modal-open');
        }
      });
    });

    if (modalDetails) observer.observe(modalDetails, observerConfig);
    if (modalProof) observer.observe(modalProof, observerConfig);
  }

  // --- PHASE 3: CHALLENGE CARDS USING DOCUMENTFRAGMENT (Item 57) ---
  /**
   * Renders challenge cards into a container using DocumentFragment to
   * minimize DOM reflows by batching all insertions (Item 57).
   */
  function renderChallengeCardsWithFragment(container, cards) {
    if (!container) return;
    container.innerHTML = '';
    const fragment = document.createDocumentFragment();
    cards.forEach(card => {
      fragment.appendChild(card);
    });
    container.appendChild(fragment);
  }

  // Debounced challenge search input handler (Item 50)
  const challengeSearchInput = document.getElementById('inp-challenge-search');
  if (challengeSearchInput) {
    challengeSearchInput.addEventListener(
      'input',
      debounce(async (e) => {
        const q = e.target.value.trim();
        if (!q) {
          loadChallenges();
          return;
        }
        try {
          const results = await API.get(`/api/challenges/search?q=${encodeURIComponent(q)}`);
          const list = elements.availableChallengesList;
          if (list) {
            list.innerHTML = '';
            if (results.length === 0) {
              list.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No challenges match your search.</p>';
            } else {
              const fragment = document.createDocumentFragment();
              results.forEach(c => {
                const div = document.createElement('div');
                div.className = 'challenge-card glass-panel';
                div.innerHTML = `<h4>${escapeHTML(c.title)}</h4><p>${escapeHTML(c.description)}</p>`;
                div.setAttribute('tabindex', '0');
                fragment.appendChild(div);
              });
              list.appendChild(fragment);
            }
          }
        } catch (err) {
          console.warn('Search failed:', err.message);
        }
      }, 350)
    );
  }

  initAuth();
});
