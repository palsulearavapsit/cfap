import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';

// Lazy load page components to minimize initial chunk size
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Calculator = lazy(() => import('./pages/Calculator').then(m => ({ default: m.Calculator })));
const Challenges = lazy(() => import('./pages/Challenges').then(m => ({ default: m.Challenges })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const PageLoader: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    <p className="text-muted text-sm animate-pulse">Loading green analytics...</p>
  </div>
);

// Guard for authenticated routes
const PrivateRoute: React.FC = () => {
  const token = localStorage.getItem('access_token');
  return token ? (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-white px-4 py-2.5 rounded-lg z-50 focus:ring-2 focus:ring-accent focus:outline-none font-medium shadow-lg"
      >
        Skip to main content
      </a>
      <Navbar />
      <main id="main-content" className="flex-grow focus:outline-none" tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  ) : (
    <Navigate to="/login" replace />
  );
};

// Guard for guest-only routes (redirects to dashboard if already logged in)
const GuestRoute: React.FC = () => {
  const token = localStorage.getItem('access_token');
  return !token ? <Outlet /> : <Navigate to="/" replace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Guest Routes */}
            <Route element={<GuestRoute />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Route>

            {/* Authenticated Private Routes */}
            <Route element={<PrivateRoute />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/calculator" element={<Calculator />} />
              <Route path="/challenges" element={<Challenges />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
