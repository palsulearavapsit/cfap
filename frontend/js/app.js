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

  // --- APP STATE ---
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
  };

  // --- API HELPER ---
  const API = {
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
    get(endpoint) {
      return this.request(endpoint, { method: 'GET' });
    },
    post(endpoint, body) {
      return this.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(body),
      });
    },
    patch(endpoint, body) {
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

    if (viewName === 'dashboard') {
      elements.navDashboard.classList.add('active');
      elements.navDashboard.setAttribute('aria-current', 'page');
      loadDashboard();
    } else if (viewName === 'calculator') {
      elements.navCalculator.classList.add('active');
      elements.navCalculator.setAttribute('aria-current', 'page');
      resetCalculator();
    } else if (viewName === 'challenges') {
      elements.navChallenges.classList.add('active');
      elements.navChallenges.setAttribute('aria-current', 'page');
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
      const [summary, history, recommendations] = await Promise.all([
        API.get('/api/analytics/summary'),
        API.get(`/api/analytics/history?filter=${state.historyFilter}`),
        API.get('/api/recommendations/'),
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

      const submitBtn = elements.formChallengeProof.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';

      try {
        await API.post(`/api/challenges/${activeProofProgressId}/complete`, { proof_text: proofText });
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
    navigateTo('auth');
  }

  if (elements.btnLogout) {
    elements.btnLogout.addEventListener('click', () => {
      logout();
      showNotification('Logged out successfully.', 'success');
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
      loadDashboard();
    });
  });

  // --- THEME TOGGLE ACTIONS ---
  if (elements.btnThemeToggle) {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
      document.body.classList.add('light-theme');
      elements.btnThemeToggle.querySelector('.sun-icon').classList.add('hidden');
      elements.btnThemeToggle.querySelector('.moon-icon').classList.remove('hidden');
    }

    elements.btnThemeToggle.addEventListener('click', () => {
      const isLight = document.body.classList.toggle('light-theme');
      localStorage.setItem('theme', isLight ? 'light' : 'dark');
      
      elements.btnThemeToggle.querySelector('.sun-icon').classList.toggle('hidden', isLight);
      elements.btnThemeToggle.querySelector('.moon-icon').classList.toggle('hidden', !isLight);
      
      // Action 15: Announce theme updates dynamically to assistive screen readers
      showNotification(`Switched to ${isLight ? 'light' : 'dark'} theme.`, 'info');
    });
  }

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

  initAuth();
});
