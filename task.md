# Pending Project Tasks - EcoTrack AI

This task list identifies pending feature enhancements, security updates, and performance optimizations for the EcoTrack AI platform.

## 1. Authentication & Security
- [x] Implement actual user registration (sign-up) and login views on the frontend.
- [x] Implement secure password verification and token-based authentication (JWT or secure cookies) on the backend.
- [x] Replace default fallback user mock in `backend/routes/auth.py` with dynamic session validation.
- [x] Enforce rate-limiting on user registration/login endpoints to prevent brute-force attacks.

## 2. Advanced Analytics & Charts
- [x] Add view filtering controls (3-Month, 6-Month, Year-to-Date view) for the history line chart on the dashboard.
- [x] Add average carbon comparison charts showing user emissions relative to national averages.
- [x] Enhance category breakdown visualization with interactive tooltips displaying absolute values (in kg) alongside percentages.

## 3. Challenge Enhancements
- [x] Add description popups/modals to challenges detailing step-by-step rules and tracking habits.
- [x] Implement a challenge completion proof workflow (e.g. uploading proof images or linking device stats).
- [x] Store past completed challenges history dynamically in the user profile view.

## 4. Production Readiness & Infrastructure
- [x] Integrate Flask-Migrate (Alembic) for robust database schema versioning.
- [x] Add production database configuration profiles for PostgreSQL / Supabase, separating development and production setups cleanly.
- [x] Implement automatic daily backups of user footprint history.

## 5. UI/UX and Accessibility Refinements
- [x] Integrate a Dark/Light mode toggle utilizing HSL theme transitions.
- [x] Add keyboard-trap handling inside the wizard steps to prevent tab indexing outside of active views.
- [x] Add clear alert banners for instances when the Gemini API is unconfigured, warning users that fallback recommendations are active.
