import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Leaf, LogOut, LayoutDashboard, Calculator, Trophy } from 'lucide-react';
import { logoutUser } from '../services/api';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('access_token');
  const userEmail = localStorage.getItem('user_email') || 'User';

  const handleLogout = () => {
    logoutUser();
    navigate('/login');
  };

  if (!isAuthenticated) return null;

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 w-full glass-card border-b border-slate-800 px-6 py-4 flex items-center justify-between shadow-lg">
      <div className="flex items-center space-x-3 select-none">
        <div className="bg-accent/20 p-2 rounded-lg text-accent">
          <Leaf className="w-6 h-6 animate-pulse" aria-hidden="true" />
        </div>
        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-green-500 bg-clip-text text-transparent">
          EcoTrack AI
        </span>
      </div>

      <div className="flex items-center space-x-1 sm:space-x-4" aria-label="Main Navigation">
        <Link
          to="/"
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focusable ${
            isActive('/') ? 'bg-primary text-white' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
          }`}
          aria-current={isActive('/') ? 'page' : undefined}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span className="hidden md:inline">Dashboard</span>
        </Link>

        <Link
          to="/calculator"
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focusable ${
            isActive('/calculator') ? 'bg-primary text-white' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
          }`}
          aria-current={isActive('/calculator') ? 'page' : undefined}
        >
          <Calculator className="w-4 h-4" />
          <span className="hidden md:inline">Calculator</span>
        </Link>

        <Link
          to="/challenges"
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors focusable ${
            isActive('/challenges') ? 'bg-primary text-white' : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
          }`}
          aria-current={isActive('/challenges') ? 'page' : undefined}
        >
          <Trophy className="w-4 h-4" />
          <span className="hidden md:inline">Challenges</span>
        </Link>
      </div>

      <div className="flex items-center space-x-4">
        <span className="hidden lg:inline text-sm text-slate-400 font-medium bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800">
          {userEmail}
        </span>
        <button
          onClick={handleLogout}
          className="flex items-center space-x-2 bg-slate-800 hover:bg-red-900/40 border border-slate-700 hover:border-red-900 text-slate-300 hover:text-red-200 px-4 py-2 rounded-lg text-sm font-medium transition-all focusable"
          aria-label="Log out of application"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </nav>
  );
};
