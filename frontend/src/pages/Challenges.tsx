import React, { useEffect, useState } from 'react';
import { Trophy, Calendar, Check, Play, Loader2, Sparkles, Award } from 'lucide-react';
import api from '../services/api';
import type { Challenge, ChallengeProgress } from '../types';

export const Challenges: React.FC = () => {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [activeProgress, setActiveProgress] = useState<ChallengeProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [pointsCelebrated, setPointsCelebrated] = useState(0);

  const fetchChallengesData = async () => {
    try {
      const [chRes, actRes] = await Promise.all([
        api.get('/challenges/'),
        api.get('/challenges/active'),
      ]);
      setChallenges(chRes.data);
      setActiveProgress(actRes.data);
    } catch (err: any) {
      setError('Failed to fetch challenges.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchChallengesData();
  }, []);

  const handleJoin = async (challengeId: number) => {
    setActionLoadingId(challengeId);
    setError(null);
    try {
      await api.post('/challenges/join', { challenge_id: challengeId });
      await fetchChallengesData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join challenge.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleComplete = async (progressId: number, challengePoints: number) => {
    setActionLoadingId(progressId);
    setError(null);
    try {
      await api.post(`/challenges/${progressId}/complete`);
      setPointsCelebrated(challengePoints);
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 5000);
      await fetchChallengesData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to complete challenge.');
    } finally {
      setActionLoadingId(null);
    }
  };

  // Calculate total reward points earned by the user
  const totalPoints = activeProgress
    .filter((p) => p.completion_status === 'completed')
    .reduce((sum, p) => sum + p.points_earned, 0);

  // Helper to check if a challenge is already active
  const getChallengeStatus = (challengeId: number) => {
    const prog = activeProgress.find(
      (p) => p.challenge_id === challengeId && p.completion_status === 'in_progress'
    );
    if (prog) return { isActive: true, progressId: prog.id };
    
    const isComp = activeProgress.some(
      (p) => p.challenge_id === challengeId && p.completion_status === 'completed'
    );
    if (isComp) return { isCompleted: true };
    
    return {};
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 text-accent animate-spin" />
        <p className="text-slate-400">Loading sustainability challenges...</p>
      </div>
    );
  }

  const activeChallenges = activeProgress.filter((p) => p.completion_status === 'in_progress');

  return (
    <div className="max-w-6xl mx-auto px-4 py-12 relative">
      {showCelebration && (
        <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
          <div className="bg-slate-900 border border-accent p-8 rounded-2xl shadow-2xl flex flex-col items-center text-center animate-bounce border-t-8 border-t-accent max-w-sm mx-4">
            <Sparkles className="w-12 h-12 text-yellow-400 mb-3" />
            <h3 className="text-xl font-bold text-white">Challenge Completed!</h3>
            <p className="text-slate-300 mt-1">
              You earned <span className="text-accent font-extrabold">{pointsCelebrated}</span> points!
            </p>
          </div>
        </div>
      )}

      {/* Header card with points */}
      <div className="glass-card p-6 md:p-8 rounded-3xl border border-slate-800 shadow-xl flex flex-col md:flex-row justify-between items-center mb-10 gap-6">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Trophy className="w-8 h-8 text-yellow-500" />
            Sustainability Challenges
          </h1>
          <p className="text-slate-400 mt-2 max-w-lg">
            Build eco-friendly habits, join monthly challenges, and earn points for keeping your carbon emissions low.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 px-8 py-5 rounded-2xl flex items-center space-x-4">
          <div className="bg-yellow-500/10 p-3 rounded-full text-yellow-500">
            <Award className="w-8 h-8" />
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block">Total Reward Points</span>
            <span className="text-3xl font-extrabold text-white tracking-tight">{totalPoints} pts</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-8 p-4 bg-red-950/40 border border-red-900 rounded-xl text-red-200 text-sm" role="alert">
          {error}
        </div>
      )}

      {/* Active Participated Challenges Section */}
      {activeChallenges.length > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Play className="w-5 h-5 text-accent" />
            Active Challenges ({activeChallenges.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {activeChallenges.map((prog) => (
              <div
                key={prog.id}
                className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between hover:border-accent/40 transition-all shadow-lg animate-slide-up"
              >
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-xs font-semibold px-2.5 py-1 rounded bg-accent/10 text-accent uppercase tracking-wider">
                      {prog.challenge.difficulty}
                    </span>
                    <span className="text-sm font-bold text-yellow-500">
                      +{prog.challenge.points} pts
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white">{prog.challenge.title}</h3>
                  <p className="text-slate-300 mt-2 text-sm leading-relaxed">
                    {prog.challenge.description}
                  </p>
                  
                  <div className="flex items-center space-x-2 text-xs text-slate-400 mt-4 bg-slate-900 px-3 py-2 rounded-lg border border-slate-800 w-fit">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>
                      Ends on: {new Date(prog.end_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
                  <button
                    onClick={() => handleComplete(prog.id, prog.challenge.points)}
                    disabled={actionLoadingId === prog.id}
                    className="btn-primary flex items-center space-x-2 py-2 px-4 text-sm font-semibold disabled:opacity-50"
                  >
                    {actionLoadingId === prog.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Mark Completed</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Challenges Section */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-6">Available Challenges</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
          {challenges.map((chal) => {
            const { isActive, progressId, isCompleted } = getChallengeStatus(chal.id);
            const isButtonDisabled = actionLoadingId === chal.id || isActive || isCompleted;

            return (
              <div
                key={chal.id}
                className="glass-card glass-card-hover p-6 rounded-2xl border border-slate-800 flex flex-col justify-between shadow-lg"
              >
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span
                      className={`text-xs font-semibold px-2.5 py-1 rounded uppercase tracking-wider ${
                        chal.difficulty === 'Beginner' && 'bg-green-500/10 text-green-400'
                      } ${
                        chal.difficulty === 'Intermediate' && 'bg-blue-500/10 text-blue-400'
                      } ${
                        chal.difficulty === 'Advanced' && 'bg-orange-500/10 text-orange-400'
                      } ${
                        chal.difficulty === 'Expert' && 'bg-red-500/10 text-red-400'
                      }`}
                    >
                      {chal.difficulty}
                    </span>
                    <span className="text-sm font-bold text-yellow-500">
                      +{chal.points} pts
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white">{chal.title}</h3>
                  <p className="text-slate-300 mt-2 text-sm leading-relaxed">
                    {chal.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
                  {isCompleted ? (
                    <span className="flex items-center space-x-1.5 text-slate-500 text-sm font-medium">
                      <Check className="w-4 h-4 text-slate-500" />
                      <span>Completed</span>
                    </span>
                  ) : isActive ? (
                    <button
                      onClick={() => handleComplete(progressId!, chal.points)}
                      disabled={actionLoadingId === progressId}
                      className="btn-primary flex items-center space-x-2 py-2 px-4 text-sm font-semibold"
                    >
                      {actionLoadingId === progressId ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Check className="w-4 h-4" />
                          <span>Complete</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={() => handleJoin(chal.id)}
                      disabled={isButtonDisabled}
                      className="btn-secondary flex items-center space-x-2 py-2 px-4 text-sm font-semibold disabled:opacity-50"
                    >
                      {actionLoadingId === chal.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5" />
                          <span>Join Challenge</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
