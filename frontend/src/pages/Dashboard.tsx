import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  Trophy,
  Leaf,
  CheckCircle,
  HelpCircle,
  Loader2,
  ChevronRight,
  TrendingUp as TrendIcon
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title as ChartTitle,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Pie } from 'react-chartjs-2';
import api from '../services/api';
import type { AnalyticsSummary, HistoryAnalytics, Recommendation } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  ChartTitle,
  Tooltip,
  Legend,
  Filler
);

export const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [history, setHistory] = useState<HistoryAnalytics | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchDashboardData = async () => {
    try {
      const [sumRes, histRes, recRes] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/analytics/history'),
        api.get('/recommendations/'),
      ]);
      setSummary(sumRes.data);
      setHistory(histRes.data);
      setRecommendations(recRes.data);
    } catch (err: any) {
      setError('Failed to fetch dashboard analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleToggleRecommendation = async (recId: number) => {
    setActionLoadingId(recId);
    try {
      await api.patch(`/recommendations/${recId}/complete`);
      // Update recommendation state locally and re-fetch summary to update score dynamically
      setRecommendations((prev) =>
        prev.map((r) => (r.id === recId ? { ...r, is_completed: !r.is_completed } : r))
      );
      const sumRes = await api.get('/analytics/summary');
      setSummary(sumRes.data);
    } catch (err: any) {
      console.error('Failed to toggle recommendation status', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 text-accent animate-spin" />
        <p className="text-slate-400">Loading your sustainability metrics...</p>
      </div>
    );
  }

  // Check if user has no carbon data entries yet
  const hasNoData = !summary || summary.current_month_emissions === 0;

  // Chart configs
  const lineChartData = {
    labels: history?.trends.map((t) => t.label) || [],
    datasets: [
      {
        fill: true,
        label: 'Emissions (kg CO₂)',
        data: history?.trends.map((t) => t.emissions) || [],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        borderWidth: 2,
        pointBackgroundColor: '#10b981',
        pointHoverBackgroundColor: '#fff',
      },
    ],
  };

  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleColor: '#fff',
        bodyColor: '#e2e8f0',
        borderColor: '#334155',
        borderWidth: 1,
      },
    },
    scales: {
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#94a3b8',
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#94a3b8',
        },
      },
    },
  };

  const breakdown = summary?.category_breakdown_percentages;
  const pieChartData = {
    labels: ['Transportation', 'Energy', 'Food', 'Shopping', 'Waste'],
    datasets: [
      {
        data: breakdown
          ? [breakdown.transportation, breakdown.energy, breakdown.food, breakdown.shopping, breakdown.waste]
          : [0, 0, 0, 0, 0],
        backgroundColor: [
          '#10b981', // Transportation
          '#f59e0b', // Energy
          '#3b82f6', // Food (using blue)
          '#8b5cf6', // Shopping
          '#ef4444', // Waste
        ],
        borderWidth: 1,
        borderColor: '#1e293b',
      },
    ],
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#94a3b8',
          font: {
            size: 11,
          },
          boxWidth: 12,
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => ` ${context.label}: ${context.raw}%`,
        },
      },
    },
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      {error && (
        <div className="mb-6 p-4 bg-red-950/40 border border-red-900 rounded-xl text-red-200 text-sm" role="alert">
          {error}
        </div>
      )}

      {hasNoData ? (
        <div className="text-center py-16 px-6 glass-card rounded-3xl border border-slate-800 shadow-xl max-w-2xl mx-auto animate-slide-up">
          <Leaf className="w-16 h-16 text-accent mx-auto mb-6 animate-pulse" />
          <h1 className="text-3xl font-extrabold text-white">Welcome to EcoTrack AI!</h1>
          <p className="text-slate-300 mt-4 text-base max-w-md mx-auto leading-relaxed">
            Ready to reduce your carbon footprint? Complete your first lifestyle questionnaire to unlock interactive charts, customized action plans, and sustainability challenges!
          </p>
          <button
            onClick={() => navigate('/calculator')}
            className="btn-primary mt-8 inline-flex items-center space-x-2 py-3 px-6 shadow-lg shadow-primary/20 text-base"
          >
            <span>Start Calculator Wizard</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      ) : (
        <div className="space-y-8 animate-fade-in">
          {/* Main Grid: Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Emission Summary Card */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-lg flex flex-col justify-between relative overflow-hidden">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Current Monthly Emissions</span>
                  <h2 className="text-4xl font-extrabold text-white mt-1.5">{summary?.current_month_emissions} kg</h2>
                  <span className="text-xs text-slate-500 mt-1 block">CO₂ equivalent</span>
                </div>
                <div className="bg-primary/10 p-2.5 rounded-xl text-accent">
                  <Leaf className="w-6 h-6" />
                </div>
              </div>
              
              <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between text-sm">
                <span className="text-slate-400">Previous: {summary?.previous_month_emissions} kg</span>
                {summary && summary.reduction_percentage !== 0 && (
                  <span
                    className={`flex items-center space-x-0.5 font-bold ${
                      summary.reduction_percentage > 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {summary.reduction_percentage > 0 ? (
                      <TrendingDown className="w-4 h-4" />
                    ) : (
                      <TrendingUp className="w-4 h-4" />
                    )}
                    <span>{Math.abs(summary.reduction_percentage)}%</span>
                  </span>
                )}
              </div>
            </div>

            {/* Improvement Score Card */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-lg flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Sustainability Score</span>
                  <h2 className="text-4xl font-extrabold text-white mt-1.5">{summary?.sustainability_score} / 100</h2>
                  <p className="text-xs text-slate-500 mt-1 block">Based on calculations & activities</p>
                </div>
                <div className="bg-yellow-500/10 p-2.5 rounded-xl text-yellow-500">
                  <Trophy className="w-6 h-6" />
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800">
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-accent h-2 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)] transition-all duration-500"
                    style={{ width: `${summary?.sustainability_score}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Annual Equivalent Card */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-lg flex flex-col justify-between">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Projected Annual Emissions</span>
                  <h2 className="text-4xl font-extrabold text-white mt-1.5">
                    {Math.round(summary ? summary.current_month_emissions * 12 : 0)} kg
                  </h2>
                  <span className="text-xs text-slate-500 mt-1 block">CO₂ equivalent / year</span>
                </div>
                <div className="bg-blue-500/10 p-2.5 rounded-xl text-blue-400">
                  <TrendIcon className="w-6 h-6" />
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800 flex justify-between text-sm text-slate-400">
                <span>Calculated from latest entry</span>
                <span className="text-xs text-green-400 font-semibold bg-green-500/10 px-2 py-0.5 rounded">Active</span>
              </div>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Historical Emissions Line Chart */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-lg lg:col-span-2 flex flex-col justify-between">
              <div className="mb-4">
                <h3 className="text-lg font-bold text-white">Emission History</h3>
                <p className="text-xs text-slate-400">Tracking monthly CO₂ emissions over time</p>
              </div>
              <div className="h-64 relative" role="img" aria-label="Emission History Line Chart" aria-describedby="emission-history-desc">
                <Line data={lineChartData} options={lineChartOptions} />
                <div id="emission-history-desc" className="sr-only">
                  This line chart shows your monthly CO₂ emissions history.
                  {history?.trends && history.trends.length > 0 ? (
                    ` Your emissions trends over the recorded period: ${history.trends.map((t) => `${t.label}: ${t.emissions} kg`).join(', ')}.`
                  ) : (
                    " No historical emission data is available currently."
                  )}
                </div>
              </div>
            </div>

            {/* Category Breakdown Pie Chart */}
            <div className="glass-card p-6 rounded-2xl border border-slate-800 shadow-lg flex flex-col justify-between">
              <div className="mb-4">
                <h3 className="text-lg font-bold text-white">Category Breakdown</h3>
                <p className="text-xs text-slate-400">Percentage distribution of emissions</p>
              </div>
              <div className="h-64 relative" role="img" aria-label="Category Breakdown Pie Chart" aria-describedby="category-breakdown-desc">
                <Pie data={pieChartData} options={pieChartOptions} />
                <div id="category-breakdown-desc" className="sr-only">
                  This pie chart displays the percentage distribution of your carbon emissions across categories.
                  {breakdown ? (
                    ` The breakdown is: Transportation ${breakdown.transportation}%, Energy ${breakdown.energy}%, Food ${breakdown.food}%, Shopping ${breakdown.shopping}%, and Waste ${breakdown.waste}%.`
                  ) : (
                    " No breakdown data is available currently."
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* AI Recommendations Section */}
          <div className="glass-card p-6 sm:p-8 rounded-2xl border border-slate-800 shadow-lg">
            <div className="mb-6 flex justify-between items-center">
              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-accent animate-pulse" />
                  AI Personalized Recommendations
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Tailored suggestions based on your highest emission categories to help you reduce footprint and save money.
                </p>
              </div>
              <button onClick={() => navigate('/calculator')} className="btn-secondary py-1.5 px-3.5 text-xs font-semibold">
                Update Profile
              </button>
            </div>

            {recommendations.length === 0 ? (
              <div className="text-center py-8 bg-slate-900/50 border border-slate-800 rounded-xl">
                <HelpCircle className="w-10 h-10 text-slate-500 mx-auto mb-2" />
                <p className="text-slate-400 text-sm">No recommendations generated. Complete your calculator wizard first.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className={`p-5 rounded-xl border transition-all flex flex-col justify-between ${
                      rec.is_completed
                        ? 'bg-slate-900/40 border-slate-800 opacity-60'
                        : 'bg-slate-900 border-slate-800/80 hover:border-accent/30'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded uppercase tracking-wider ${
                            rec.difficulty === 'Beginner' && 'bg-green-500/10 text-green-400'
                          } ${
                            rec.difficulty === 'Intermediate' && 'bg-blue-500/10 text-blue-400'
                          } ${
                            rec.difficulty === 'Advanced' && 'bg-orange-500/10 text-orange-400'
                          } ${
                            rec.difficulty === 'Expert' && 'bg-red-500/10 text-red-400'
                          }`}
                        >
                          {rec.difficulty}
                        </span>
                        
                        <div className="flex items-center space-x-2 text-xs">
                          <span className="text-accent font-semibold">-{rec.expected_reduction} kg CO₂</span>
                          <span className="text-slate-500">|</span>
                          <span className="text-green-400 font-semibold">${rec.estimated_savings} saved</span>
                        </div>
                      </div>

                      <h4 className={`font-bold text-base ${rec.is_completed ? 'line-through text-slate-500' : 'text-white'}`}>
                        {rec.title}
                      </h4>
                      <p className="text-slate-300 text-xs mt-1.5 leading-relaxed">{rec.description}</p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/50 flex justify-end">
                      <button
                        onClick={() => handleToggleRecommendation(rec.id)}
                        disabled={actionLoadingId === rec.id}
                        className={`flex items-center space-x-1.5 text-xs font-semibold py-1.5 px-3 rounded-lg border transition-all focusable ${
                          rec.is_completed
                            ? 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
                            : 'bg-primary/10 border-primary/20 text-accent hover:bg-primary/20 hover:border-primary/40'
                        }`}
                      >
                        {actionLoadingId === rec.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : rec.is_completed ? (
                          <>
                            <CheckCircle className="w-3.5 h-3.5 text-slate-400" />
                            <span>Undo Complete</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3.5 h-3.5 text-accent" />
                            <span>Mark Completed</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
