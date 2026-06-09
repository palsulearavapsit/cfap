import type { CarbonEntryInput } from './calculator';

export interface RecommendationInput {
  title: string;
  description: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  expected_reduction: number;
  estimated_savings: number;
  is_completed: boolean;
}

export function generateRecommendations(entry: CarbonEntryInput): RecommendationInput[] {
  const recommendationsToAdd: RecommendationInput[] = [];

  // 1. Transportation Recommendations
  const carEmissions = entry.transportation_car * 0.171;
  const flightsEmissions = entry.transportation_flights * 0.115;

  if (carEmissions > 100 || flightsEmissions > 150) {
    recommendationsToAdd.push({
      title: 'Switch to Public Transit',
      description:
        'Replace 50% of your solo car drives with bus or train commutes. Public transit significantly cuts per-passenger emissions.',
      difficulty: 'Intermediate',
      expected_reduction: 65.0, // kg CO2 / month
      estimated_savings: 50.0, // USD / month
      is_completed: false,
    });
    recommendationsToAdd.push({
      title: 'Active Commuting (Cycling/Walking)',
      description:
        'Cycle or walk for short trips under 5km. It has zero emissions and improves cardiovascular health.',
      difficulty: 'Beginner',
      expected_reduction: 35.0,
      estimated_savings: 20.0,
      is_completed: false,
    });
  }

  if (flightsEmissions > 200) {
    recommendationsToAdd.push({
      title: 'Offset Flight Emissions & Reduce Trips',
      description:
        'Combine business trips or opt for high-speed rail instead of short-haul flights. Purchase gold-standard carbon offsets for necessary flights.',
      difficulty: 'Advanced',
      expected_reduction: 120.0,
      estimated_savings: 150.0,
      is_completed: false,
    });
  }

  // 2. Energy Recommendations
  const elecEmissions = entry.energy_electricity * 0.45;
  const acEmissions = entry.energy_ac * 1.5 * 0.45;

  if (elecEmissions > 80) {
    recommendationsToAdd.push({
      title: 'Upgrade to LED Lighting',
      description:
        'Replace all incandescent bulbs with ENERGY STAR certified LEDs. They use up to 75% less energy and last 25x longer.',
      difficulty: 'Beginner',
      expected_reduction: 12.0,
      estimated_savings: 8.0,
      is_completed: false,
    });
    recommendationsToAdd.push({
      title: 'Smart Thermostat & Efficient Appliances',
      description:
        'Install a smart programmable thermostat and unplug idle electronics. Ensure new appliances are rated A+++ or ENERGY STAR.',
      difficulty: 'Intermediate',
      expected_reduction: 40.0,
      estimated_savings: 25.0,
      is_completed: false,
    });
  }

  if (acEmissions > 50) {
    recommendationsToAdd.push({
      title: 'Reduce AC Usage & Thermostat Settings',
      description:
        'Set your AC to 24-26°C (75-78°F) rather than lower. Use ceiling fans to circulate air and close blinds during peak sunlight.',
      difficulty: 'Beginner',
      expected_reduction: 25.0,
      estimated_savings: 18.0,
      is_completed: false,
    });
  }

  // 3. Food Recommendations
  const foodPreference = entry.food_preference.toLowerCase();
  if (foodPreference === 'non-vegetarian') {
    recommendationsToAdd.push({
      title: 'Integrate Meat-Free Days',
      description:
        'Try replacing red meat and dairy with plant-based alternatives on select days (e.g., Meat-Free Mondays). Raising livestock generates massive methane emissions.',
      difficulty: 'Beginner',
      expected_reduction: 45.0,
      estimated_savings: 30.0,
      is_completed: false,
    });
  } else if (foodPreference === 'vegetarian') {
    recommendationsToAdd.push({
      title: 'Transition towards Plant-Based Diet',
      description:
        'Reduce cheese, butter, and milk consumption. Source foods locally to reduce food miles and packaging waste.',
      difficulty: 'Intermediate',
      expected_reduction: 15.0,
      estimated_savings: 10.0,
      is_completed: false,
    });
  }

  // 4. Shopping Recommendations
  const clothingEmissions = entry.shopping_clothing * 15.0;
  const electronicsEmissions = entry.shopping_electronics * 80.0;

  if (clothingEmissions > 30) {
    recommendationsToAdd.push({
      title: 'Choose Sustainable & Second-Hand Fashion',
      description:
        "Avoid fast fashion. Buy high-quality, durable garments or explore thrift stores. Extend your clothes' lifetime by washing at lower temperatures.",
      difficulty: 'Beginner',
      expected_reduction: 20.0,
      estimated_savings: 40.0,
      is_completed: false,
    });
  }

  if (electronicsEmissions > 70) {
    recommendationsToAdd.push({
      title: 'Extend Electronics Lifecycle & Repair',
      description:
        'Instead of upgrading devices yearly, repair existing ones and buy refurbished electronics when replacement is necessary. Recycle old devices safely.',
      difficulty: 'Intermediate',
      expected_reduction: 75.0,
      estimated_savings: 120.0,
      is_completed: false,
    });
  }

  // 5. Waste Recommendations
  if (entry.waste_recycling.toLowerCase() === 'rarely') {
    recommendationsToAdd.push({
      title: 'Set Up Household Recycling Station',
      description:
        'Separate paper, cardboard, glass, and metal from general landfill waste. Check local guidelines for recyclable plastics.',
      difficulty: 'Beginner',
      expected_reduction: 15.0,
      estimated_savings: 0.0,
      is_completed: false,
    });
  }

  if (['average', 'high'].includes(entry.waste_plastic.toLowerCase())) {
    recommendationsToAdd.push({
      title: 'Adopt Zero-Waste Shopping Habits',
      description:
        'Carry reusable canvas bags, purchase items in bulk, and refuse single-use plastic water bottles. Bring containers for bulk food.',
      difficulty: 'Beginner',
      expected_reduction: 10.0,
      estimated_savings: 15.0,
      is_completed: false,
    });
  }

  // If no specific triggers, add generic high-value items
  if (recommendationsToAdd.length === 0) {
    recommendationsToAdd.push({
      title: 'Compost Organic Waste',
      description:
        'Start composting your kitchen scraps and garden clippings. This prevents organic matter from producing methane in landfills.',
      difficulty: 'Intermediate',
      expected_reduction: 12.0,
      estimated_savings: 5.0,
      is_completed: false,
    });
    recommendationsToAdd.push({
      title: 'Mindful Consumption Check',
      description:
        'Before making any purchase, wait 48 hours to determine if it is a necessity or impulse buy.',
      difficulty: 'Beginner',
      expected_reduction: 15.0,
      estimated_savings: 50.0,
      is_completed: false,
    });
  }

  return recommendationsToAdd;
}
