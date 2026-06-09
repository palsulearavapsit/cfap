import supabase from './supabaseClient';
import { calculateEmissions } from '../utils/calculator';
import { generateRecommendations } from '../utils/recommender';

export const logoutUser = async () => {
  await supabase.auth.signOut();
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_email');
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    if (path !== '/login' && path !== '/register') {
      window.location.href = '/login';
    }
  }
};

const getUser = async () => {
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    throw new Error('Unauthenticated');
  }
  return user;
};

// Helper function to seed demo user data if they are logging in for the first time
async function seedDemoUserData(userId: string) {
  try {
    const now = new Date();

    // 1. Seed Carbon Entries
    const entry60DaysAgo = {
      user_id: userId,
      transportation_car: 1200.0,
      transportation_bike: 0.0,
      transportation_public: 0.0,
      transportation_flights: 2000.0,
      energy_electricity: 450.0,
      energy_ac: 120.0,
      energy_appliance: 40.0,
      food_preference: 'non-vegetarian',
      shopping_clothing: 8.0,
      shopping_electronics: 3.0,
      waste_recycling: 'rarely',
      waste_plastic: 'high',
      total_emissions: 980.5,
      created_at: new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000).toISOString(),
    };

    const entry30DaysAgo = {
      user_id: userId,
      transportation_car: 700.0,
      transportation_bike: 30.0,
      transportation_public: 150.0,
      transportation_flights: 0.0,
      energy_electricity: 300.0,
      energy_ac: 60.0,
      energy_appliance: 25.0,
      food_preference: 'vegetarian',
      shopping_clothing: 3.0,
      shopping_electronics: 0.0,
      waste_recycling: 'sometimes',
      waste_plastic: 'average',
      total_emissions: 495.2,
      created_at: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    };

    const entryCurrent = {
      user_id: userId,
      transportation_car: 250.0,
      transportation_bike: 120.0,
      transportation_public: 300.0,
      transportation_flights: 0.0,
      energy_electricity: 150.0,
      energy_ac: 15.0,
      energy_appliance: 15.0,
      food_preference: 'vegan',
      shopping_clothing: 1.0,
      shopping_electronics: 0.0,
      waste_recycling: 'always',
      waste_plastic: 'low',
      total_emissions: 215.4,
      created_at: now.toISOString(),
    };

    await supabase.from('carbon_entries').insert([entry60DaysAgo, entry30DaysAgo, entryCurrent]);

    // 2. Seed Recommendations
    const rec1 = {
      user_id: userId,
      title: 'Upgrade to LED Lighting',
      description:
        'Replace all incandescent bulbs with ENERGY STAR certified LEDs. They use up to 75% less energy and last 25x longer.',
      difficulty: 'Beginner',
      expected_reduction: 12.0,
      estimated_savings: 8.0,
      is_completed: true,
      created_at: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    };

    const rec2 = {
      user_id: userId,
      title: 'Smart Thermostat & Efficient Appliances',
      description:
        'Install a smart programmable thermostat and unplug idle electronics. Ensure new appliances are rated A+++ or ENERGY STAR.',
      difficulty: 'Intermediate',
      expected_reduction: 40.0,
      estimated_savings: 25.0,
      is_completed: false,
      created_at: now.toISOString(),
    };

    const rec3 = {
      user_id: userId,
      title: 'Integrate Meat-Free Days',
      description:
        'Try replacing red meat and dairy with plant-based alternatives on select days (e.g., Meat-Free Mondays). Raising livestock generates massive methane emissions.',
      difficulty: 'Beginner',
      expected_reduction: 45.0,
      estimated_savings: 30.0,
      is_completed: false,
      created_at: now.toISOString(),
    };

    await supabase.from('recommendations').insert([rec1, rec2, rec3]);

    // 3. Seed Challenge Progress
    const prog1 = {
      user_id: userId,
      challenge_id: 1, // No Plastic Day
      start_date: new Date(now.getTime() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      completion_status: 'completed',
      points_earned: 50,
    };

    const prog2 = {
      user_id: userId,
      challenge_id: 2, // Meat-Free Monday
      start_date: new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date(now.getTime() + 6 * 24 * 60 * 60 * 1000).toISOString(),
      completion_status: 'in_progress',
      points_earned: 0,
    };

    await supabase.from('challenge_progress').insert([prog1, prog2]);

    console.log('Successfully seeded demo user data.');
  } catch (err) {
    console.error('Error seeding demo user data:', err);
  }
}

export const api = {
  async post(url: string, body: any = {}): Promise<any> {
    if (url === '/auth/register') {
      const { data, error } = await supabase.auth.signUp({
        email: body.email,
        password: body.password,
      });

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return {
        data: {
          access_token: data.session?.access_token || 'registration_success',
          refresh_token: data.session?.refresh_token || '',
          user: data.user,
        },
      };
    }

    if (url === '/auth/login') {
      let data: any = null;
      let error: any = null;

      try {
        const res = await supabase.auth.signInWithPassword({
          email: body.email,
          password: body.password,
        });
        data = res.data;
        error = res.error;
      } catch (err) {
        error = err;
      }

      // Special handling to auto-create and seed the demo account on first attempt
      if (body.email === 'demo@ecotrack.ai' && error) {
        try {
          const signUpRes = await supabase.auth.signUp({
            email: body.email,
            password: body.password,
          });

          if (!signUpRes.error && signUpRes.data.user) {
            await seedDemoUserData(signUpRes.data.user.id);
            
            // Retry sign in
            const retryRes = await supabase.auth.signInWithPassword({
              email: body.email,
              password: body.password,
            });
            
            if (!retryRes.error && retryRes.data.session) {
              data = retryRes.data;
              error = null;
            }
          }
        } catch (signUpErr) {
          console.error('Failed to auto-create demo user:', signUpErr);
        }
      }

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return {
        data: {
          access_token: data.session?.access_token,
          refresh_token: data.session?.refresh_token,
          user: data.user,
        },
      };
    }

    if (url === '/challenges/join') {
      const user = await getUser();
      const startDate = new Date().toISOString();
      const endDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(); // 7 days duration

      // Verify if they already joined and it is in_progress
      const { data: existingProgress, error: checkError } = await supabase
        .from('challenge_progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('challenge_id', body.challenge_id)
        .eq('completion_status', 'in_progress')
        .maybeSingle();

      if (checkError) {
        throw { response: { data: { detail: checkError.message } } };
      }

      if (existingProgress) {
        throw { response: { data: { detail: 'You are already participating in this challenge' } } };
      }

      const { data, error } = await supabase
        .from('challenge_progress')
        .insert({
          user_id: user.id,
          challenge_id: body.challenge_id,
          start_date: startDate,
          end_date: endDate,
          completion_status: 'in_progress',
          points_earned: 0,
        })
        .select('*, challenge:challenges(*)')
        .single();

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return { data };
    }

    if (url.startsWith('/challenges/') && url.endsWith('/complete')) {
      const progressId = url.split('/')[2];
      const { data: progress, error: fetchError } = await supabase
        .from('challenge_progress')
        .select('*, challenge:challenges(*)')
        .eq('id', progressId)
        .single();

      if (fetchError || !progress) {
        throw { response: { data: { detail: fetchError?.message || 'Progress record not found' } } };
      }

      if (progress.completion_status !== 'in_progress') {
        throw { response: { data: { detail: `Challenge is already ${progress.completion_status}` } } };
      }

      const { data, error } = await supabase
        .from('challenge_progress')
        .update({
          completion_status: 'completed',
          points_earned: progress.challenge.points,
        })
        .eq('id', progressId)
        .select('*, challenge:challenges(*)')
        .single();

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return { data };
    }

    if (url === '/calculator/submit') {
      const user = await getUser();

      // Compute emissions
      const emissionsResult = calculateEmissions(body);

      // Save carbon entry
      const { data: entry, error: entryError } = await supabase
        .from('carbon_entries')
        .insert({
          user_id: user.id,
          ...body,
          total_emissions: emissionsResult.total_emissions,
        })
        .select()
        .single();

      if (entryError) {
        throw { response: { data: { detail: entryError.message } } };
      }

      // Delete incomplete recommendations
      const { error: deleteError } = await supabase
        .from('recommendations')
        .delete()
        .eq('user_id', user.id)
        .eq('is_completed', false);

      if (deleteError) {
        throw { response: { data: { detail: deleteError.message } } };
      }

      // Generate recommendations
      const recommendations = generateRecommendations(body);
      if (recommendations.length > 0) {
        const recsToInsert = recommendations.map((r) => ({
          user_id: user.id,
          title: r.title,
          description: r.description,
          difficulty: r.difficulty,
          expected_reduction: r.expected_reduction,
          estimated_savings: r.estimated_savings,
          is_completed: false,
        }));

        const { error: insertError } = await supabase.from('recommendations').insert(recsToInsert);
        if (insertError) {
          throw { response: { data: { detail: insertError.message } } };
        }
      }

      return { data: entry };
    }

    throw new Error(`Endpoint POST ${url} not supported`);
  },

  async get(url: string): Promise<any> {
    if (url === '/challenges/') {
      const { data, error } = await supabase
        .from('challenges')
        .select('*')
        .order('id', { ascending: true });

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return { data };
    }

    if (url === '/challenges/active') {
      const user = await getUser();
      const { data, error } = await supabase
        .from('challenge_progress')
        .select('*, challenge:challenges(*)')
        .eq('user_id', user.id)
        .order('start_date', { ascending: false });

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return { data };
    }

    if (url === '/recommendations/') {
      const user = await getUser();
      const { data, error } = await supabase
        .from('recommendations')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return { data };
    }

    if (url === '/analytics/summary') {
      const user = await getUser();
      const { data: entries, error: entriesError } = await supabase
        .from('carbon_entries')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (entriesError) {
        throw { response: { data: { detail: entriesError.message } } };
      }

      if (!entries || entries.length === 0) {
        return {
          data: {
            current_month_emissions: 0.0,
            previous_month_emissions: 0.0,
            reduction_percentage: 0.0,
            sustainability_score: 100,
            category_breakdown_percentages: {
              transportation: 0.0,
              energy: 0.0,
              food: 0.0,
              shopping: 0.0,
              waste: 0.0,
            },
          },
        };
      }

      const currentEntry = entries[0];
      const previousEntry = entries.length > 1 ? entries[1] : null;

      const currentEmissions = currentEntry.total_emissions;
      const previousEmissions = previousEntry ? previousEntry.total_emissions : 0.0;

      let reductionPercentage = 0.0;
      if (previousEmissions > 0) {
        reductionPercentage = ((previousEmissions - currentEmissions) / previousEmissions) * 100;
        reductionPercentage = Math.round(reductionPercentage * 10) / 10;
      }

      const calcResults = calculateEmissions(currentEntry);
      const percentages = calcResults.percentages;

      // Score calculation
      let baseScore = 80;
      if (currentEmissions > 100) {
        const penalty = Math.floor((currentEmissions - 100) / 10);
        baseScore -= penalty;
      }

      // Count completed challenges
      const { count: completedChallengesCount, error: chError } = await supabase
        .from('challenge_progress')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id)
        .eq('completion_status', 'completed');

      if (chError) {
        throw { response: { data: { detail: chError.message } } };
      }

      baseScore += (completedChallengesCount || 0) * 5;

      // Count completed recommendations
      const { count: completedRecsCount, error: recError } = await supabase
        .from('recommendations')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user.id)
        .eq('is_completed', true);

      if (recError) {
        throw { response: { data: { detail: recError.message } } };
      }

      baseScore += (completedRecsCount || 0) * 3;

      const sustainabilityScore = Math.max(10, Math.min(100, baseScore));

      return {
        data: {
          current_month_emissions: Math.round(currentEmissions * 100) / 100,
          previous_month_emissions: Math.round(previousEmissions * 100) / 100,
          reduction_percentage: reductionPercentage,
          sustainability_score: sustainabilityScore,
          category_breakdown_percentages: {
            transportation: percentages.transportation,
            energy: percentages.energy,
            food: percentages.food,
            shopping: percentages.shopping,
            waste: percentages.waste,
          },
        },
      };
    }

    if (url === '/analytics/history') {
      const user = await getUser();
      const { data: entries, error: entriesError } = await supabase
        .from('carbon_entries')
        .select('created_at, total_emissions')
        .eq('user_id', user.id)
        .order('created_at', { ascending: true });

      if (entriesError) {
        throw { response: { data: { detail: entriesError.message } } };
      }

      if (!entries || entries.length === 0) {
        return { data: { trends: [] } };
      }

      const trends = entries.slice(-6).map((entry: any) => {
        const date = new Date(entry.created_at);
        const label = date.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
        return {
          label,
          emissions: Math.round(entry.total_emissions * 100) / 100,
        };
      });

      return { data: { trends } };
    }

    throw new Error(`Endpoint GET ${url} not supported`);
  },

  async patch(url: string, _body: any = {}): Promise<any> {
    if (url.startsWith('/recommendations/') && url.endsWith('/complete')) {
      const recId = url.split('/')[2];
      const { data: rec, error: fetchError } = await supabase
        .from('recommendations')
        .select('*')
        .eq('id', recId)
        .single();

      if (fetchError || !rec) {
        throw { response: { data: { detail: fetchError?.message || 'Recommendation not found' } } };
      }

      const { data, error } = await supabase
        .from('recommendations')
        .update({ is_completed: !rec.is_completed })
        .eq('id', recId)
        .select()
        .single();

      if (error) {
        throw { response: { data: { detail: error.message } } };
      }

      return { data };
    }

    throw new Error(`Endpoint PATCH ${url} not supported`);
  },
};

export default api;
