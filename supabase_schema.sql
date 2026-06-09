-- Supabase Schema for EcoTrack AI Platform
-- Run this in your Supabase SQL Editor to set up the tables, constraints, and Row Level Security.

-- 1. CHALLENGES TABLE
CREATE TABLE IF NOT EXISTS public.challenges (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    difficulty VARCHAR(50) NOT NULL, -- Beginner, Intermediate, Advanced, Expert
    points INTEGER DEFAULT 0 NOT NULL
);

-- Pre-seed challenges
INSERT INTO public.challenges (id, title, description, difficulty, points)
VALUES 
    (1, 'No Plastic Day', 'Avoid single-use plastics for an entire day.', 'Beginner', 50),
    (2, 'Meat-Free Monday', 'Eat only plant-based meals today.', 'Intermediate', 100),
    (3, 'Public Transport Week', 'Commute using only public transit or active transit (walk/bike) for 5 days.', 'Advanced', 250),
    (4, 'Zero Waste Weekend', 'Generate absolutely zero landfill waste from Friday night to Monday morning.', 'Expert', 500)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    difficulty = EXCLUDED.difficulty,
    points = EXCLUDED.points;

-- 2. CARBON ENTRIES TABLE
CREATE TABLE IF NOT EXISTS public.carbon_entries (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    transportation_car DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    transportation_bike DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    transportation_public DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    transportation_flights DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    energy_electricity DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    energy_ac DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    energy_appliance DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    food_preference VARCHAR(50) DEFAULT 'non-vegetarian' NOT NULL,
    shopping_clothing DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    shopping_electronics DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    waste_recycling VARCHAR(50) DEFAULT 'rarely' NOT NULL,
    waste_plastic VARCHAR(50) DEFAULT 'average' NOT NULL,
    total_emissions DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_carbon_user_created ON public.carbon_entries(user_id, created_at DESC);

-- 3. RECOMMENDATIONS TABLE
CREATE TABLE IF NOT EXISTS public.recommendations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(50) NOT NULL,
    expected_reduction DOUBLE PRECISION NOT NULL,
    estimated_savings DOUBLE PRECISION NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recommendation_user_created ON public.recommendations(user_id, created_at DESC);

-- 4. CHALLENGE PROGRESS TABLE
CREATE TABLE IF NOT EXISTS public.challenge_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    challenge_id INTEGER REFERENCES public.challenges(id) ON DELETE CASCADE NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    completion_status VARCHAR(50) DEFAULT 'in_progress' NOT NULL, -- in_progress, completed, failed
    points_earned INTEGER DEFAULT 0 NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_challenge_progress_user ON public.challenge_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_challenge ON public.challenge_progress(challenge_id);


-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- Enable RLS on all tables
ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.carbon_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenge_progress ENABLE ROW LEVEL SECURITY;

-- Policies for Challenges (Anyone can read, write is restricted)
CREATE POLICY "Allow public read access to challenges" ON public.challenges
    FOR SELECT USING (true);

-- Policies for Carbon Entries (Users can only access/modify their own data)
CREATE POLICY "Allow users to manage their own carbon entries" ON public.carbon_entries
    FOR ALL USING (auth.uid() = user_id);

-- Policies for Recommendations (Users can only access/modify their own data)
CREATE POLICY "Allow users to manage their own recommendations" ON public.recommendations
    FOR ALL USING (auth.uid() = user_id);

-- Policies for Challenge Progress (Users can only access/modify their own data)
CREATE POLICY "Allow users to manage their own challenge progress" ON public.challenge_progress
    FOR ALL USING (auth.uid() = user_id);
