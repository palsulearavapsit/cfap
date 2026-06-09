import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Leaf, Mail, Lock, Loader2 } from 'lucide-react';
import api from '../services/api';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_email', email);
      
      navigate('/');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Invalid email or password. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await api.post('/auth/login', {
        email: 'demo@ecotrack.ai',
        password: 'demouser123',
      });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_email', 'demo@ecotrack.ai');
      
      navigate('/');
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Failed to connect to the demo account. Please make sure the backend server is running.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md glass-card p-8 rounded-2xl shadow-2xl border border-slate-800 animate-slide-up">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary/20 p-3 rounded-2xl text-accent mb-4">
            <Leaf className="w-8 h-8" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">EcoTrack AI</h1>
          <p className="text-slate-400 mt-2 text-sm text-center">
            Sign in to calculate and reduce your carbon footprint
          </p>
        </div>

        {error && (
          <div
            className="mb-6 p-4 bg-red-950/40 border border-red-900 rounded-lg text-red-200 text-sm"
            role="alert"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-semibold text-slate-300 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3 w-5 h-5 text-slate-500" aria-hidden="true" />
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="text-input pl-11 focusable"
                required
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-semibold text-slate-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 w-5 h-5 text-slate-500" aria-hidden="true" />
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="text-input pl-11 focusable"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary flex items-center justify-center space-x-2 py-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed text-base font-semibold shadow-lg shadow-primary/20"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>

          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full btn-secondary flex items-center justify-center space-x-2 py-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed text-base font-semibold"
          >
            <span>Try Demo Account</span>
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-slate-400">
          New to EcoTrack AI?{' '}
          <Link to="/register" className="text-accent hover:underline focusable rounded p-0.5 font-semibold">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
};
