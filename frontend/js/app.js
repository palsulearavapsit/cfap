// EcoTrack AI - Vanilla JS SPA App Handler

document.addEventListener('DOMContentLoaded', () => {
  // --- APP STATE ---
  const state = {
    charts: {
      history: null,
      pie: null,
    },
    calculatorStep: 1,
  };

  // --- API HELPER ---
  const API = {
    async request(endpoint, options = {}) {
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      try {
        const response = await fetch(endpoint, { ...options, headers });
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
    
    // Views
    views: {
      dashboard: document.getElementById('view-dashboard'),
      calculator: document.getElementById('view-calculator'),
      challenges: document.getElementById('view-challenges'),
    },
    
    // Nav Buttons
    navDashboard: document.getElementById('nav-dashboard'),
    navCalculator: document.getElementById('nav-calculator'),
    navChallenges: document.getElementById('nav-challenges'),

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
    completionCelebration: document.getElementById('completion-celebration'),
    celebPointsEarned: document.getElementById('celeb-points-earned'),
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
    // Hide all views
    Object.values(elements.views).forEach(view => view.classList.add('hidden'));
    
    // Show selected view
    if (elements.views[viewName]) {
      elements.views[viewName].classList.remove('hidden');
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
        API.get('/api/analytics/history'),
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
      elements.valAnnual.textContent = Math.round(summary.current_month_emissions * 12).toLocaleString();

      // 2. Render Line Chart
      renderHistoryChart(history.trends);

      // 3. Render Pie Chart
      renderPieChart(summary.category_breakdown_percentages);

      // 4. Render Recommendations
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

  function renderPieChart(breakdown) {
    const ctx = document.getElementById('chart-pie').getContext('2d');

    // Destroy previous instance
    if (state.charts.pie) {
      state.charts.pie.destroy();
    }

    if (!breakdown) return;

    state.charts.pie = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Transportation', 'Energy', 'Food', 'Shopping', 'Waste'],
        datasets: [{
          data: [
            breakdown.transportation,
            breakdown.energy,
            breakdown.food,
            breakdown.shopping,
            breakdown.waste
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
              label: (context) => ` ${context.label}: ${context.raw}%`
            }
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
          <button class="btn-complete ${rec.is_completed ? 'undo' : ''}" data-id="${rec.id}">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
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

  // --- CHALLENGES SERVICES ---
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
          card.className = 'challenge-card glass-panel';
          
          const endDate = new Date(prog.end_date).toLocaleDateString();

          card.innerHTML = `
            <div>
              <div class="challenge-top">
                <span class="difficulty-badge ${prog.challenge.difficulty.toLowerCase()}">${prog.challenge.difficulty}</span>
                <span class="challenge-pts">+${prog.challenge.points} pts</span>
              </div>
              <h3>${prog.challenge.title}</h3>
              <p>${prog.challenge.description}</p>
            </div>
            <div class="challenge-footer">
              <span class="challenge-date">Ends: ${endDate}</span>
              <button class="btn btn-primary btn-complete-challenge" data-progress-id="${prog.id}" data-points="${prog.challenge.points}">
                Mark Completed
              </button>
            </div>
          `;

          // Mark complete click
          card.querySelector('.btn-complete-challenge').addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            const progressId = btn.dataset.progressId;
            const points = parseInt(btn.dataset.points);
            
            try {
              await API.post(`/api/challenges/${progressId}/complete`);
              
              // Points celebration
              elements.celebPointsEarned.textContent = points;
              elements.completionCelebration.classList.remove('hidden');
              setTimeout(() => {
                elements.completionCelebration.classList.add('hidden');
              }, 4000);
              
              loadChallenges(); // Refresh
            } catch (err) {
              showNotification('Failed to complete challenge.', 'error');
              btn.disabled = false;
            }
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

      // 2. Render available challenges list
      elements.availableChallengesList.innerHTML = '';
      challenges.forEach(chal => {
        const card = document.createElement('div');
        card.className = 'challenge-card glass-panel';
        
        const status = getChallengeStatus(chal.id);

        let footerContent = '';
        if (status.isCompleted) {
          footerContent = '<span class="challenge-date font-bold">✓ Completed</span>';
        } else if (status.isActive) {
          footerContent = `
            <button class="btn btn-primary btn-complete-challenge" data-progress-id="${status.progressId}" data-points="${chal.points}">
              Complete
            </button>
          `;
        } else {
          footerContent = `
            <button class="btn btn-secondary btn-join-challenge" data-id="${chal.id}">
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
            <p>${chal.description}</p>
          </div>
          <div class="challenge-footer">
            <span></span> <!-- empty alignment -->
            ${footerContent}
          </div>
        `;

        // Join click
        const joinBtn = card.querySelector('.btn-join-challenge');
        if (joinBtn) {
          joinBtn.addEventListener('click', async (e) => {
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
          compBtn.addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            btn.disabled = true;
            const progressId = btn.dataset.progressId;
            const points = parseInt(btn.dataset.points);
            try {
              await API.post(`/api/challenges/${progressId}/complete`);
              
              elements.celebPointsEarned.textContent = points;
              elements.completionCelebration.classList.remove('hidden');
              setTimeout(() => {
                elements.completionCelebration.classList.add('hidden');
              }, 4000);
              
              loadChallenges(); // Refresh
            } catch (err) {
              showNotification('Failed to complete challenge.', 'error');
              btn.disabled = false;
            }
          });
        }

        elements.availableChallengesList.appendChild(card);
      });

    } catch (err) {
      showNotification('Failed to load challenges.', 'error');
    }
  }

  // --- INITIAL CHECK ---
  navigateTo('dashboard');
});
