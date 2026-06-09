export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface CarbonEntry {
  id: number;
  user_id: string;
  transportation_car: number;
  transportation_bike: number;
  transportation_public: number;
  transportation_flights: number;
  energy_electricity: number;
  energy_ac: number;
  energy_appliance: number;
  food_preference: string;
  shopping_clothing: number;
  shopping_electronics: number;
  waste_recycling: string;
  waste_plastic: string;
  total_emissions: number;
  created_at: string;
}

export interface Recommendation {
  id: number;
  user_id: string;
  title: string;
  description: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  expected_reduction: number;
  estimated_savings: number;
  is_completed: boolean;
  created_at: string;
}

export interface Challenge {
  id: number;
  title: string;
  description: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  points: number;
}

export interface ChallengeProgress {
  id: number;
  user_id: string;
  challenge_id: number;
  start_date: string;
  end_date: string;
  completion_status: 'in_progress' | 'completed' | 'failed';
  points_earned: number;
  challenge: Challenge;
}

export interface CategoryBreakdown {
  transportation: number;
  energy: number;
  food: number;
  shopping: number;
  waste: number;
}

export interface AnalyticsSummary {
  current_month_emissions: number;
  previous_month_emissions: number;
  reduction_percentage: number;
  sustainability_score: number;
  category_breakdown_percentages: CategoryBreakdown;
}

export interface TrendPoint {
  label: string;
  emissions: number;
}

export interface HistoryAnalytics {
  trends: TrendPoint[];
}
