// Emission factors (kg CO2 per unit)
export const CAR_FACTOR = 0.171;        // per km
export const BIKE_FACTOR = 0.005;       // per km
export const PUBLIC_FACTOR = 0.041;     // per km
export const FLIGHT_FACTOR = 0.115;     // per km

export const ELECTRICITY_FACTOR = 0.45;  // per kWh
export const AC_KW = 1.5;               // Average AC power draw in kW
export const APPLIANCE_KW = 0.5;        // Average appliance power draw in kW

export const FOOD_FACTORS: Record<string, number> = {
  vegan: 100.0,       // kg CO2/month
  vegetarian: 150.0,
  'non-vegetarian': 300.0,
};

export const CLOTHING_FACTOR = 15.0;    // kg CO2/item
export const ELECTRONICS_FACTOR = 80.0;  // kg CO2/item

export const RECYCLING_FACTORS: Record<string, number> = {
  rarely: 50.0,
  sometimes: 30.0,
  always: 10.0,
};

export const PLASTIC_FACTORS: Record<string, number> = {
  low: 10.0,
  average: 25.0,
  high: 50.0,
};

export interface CarbonEntryInput {
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
}

export interface CalculationResult {
  total_emissions: number;
  breakdown: {
    transportation: number;
    energy: number;
    food: number;
    shopping: number;
    waste: number;
  };
  percentages: {
    transportation: number;
    energy: number;
    food: number;
    shopping: number;
    waste: number;
  };
}

export function calculateEmissions(entry: CarbonEntryInput): CalculationResult {
  // 1. Transportation
  const transportCar = entry.transportation_car * CAR_FACTOR;
  const transportBike = entry.transportation_bike * BIKE_FACTOR;
  const transportPublic = entry.transportation_public * PUBLIC_FACTOR;
  const transportFlights = entry.transportation_flights * FLIGHT_FACTOR;
  const transportTotal = transportCar + transportBike + transportPublic + transportFlights;

  // 2. Energy
  const energyElectricity = entry.energy_electricity * ELECTRICITY_FACTOR;
  const energyAc = entry.energy_ac * AC_KW * ELECTRICITY_FACTOR;
  const energyAppliance = entry.energy_appliance * APPLIANCE_KW * ELECTRICITY_FACTOR;
  const energyTotal = energyElectricity + energyAc + energyAppliance;

  // 3. Food
  const foodTotal = FOOD_FACTORS[entry.food_preference.toLowerCase()] ?? 300.0;

  // 4. Shopping
  const shoppingClothing = entry.shopping_clothing * CLOTHING_FACTOR;
  const shoppingElectronics = entry.shopping_electronics * ELECTRONICS_FACTOR;
  const shoppingTotal = shoppingClothing + shoppingElectronics;

  // 5. Waste
  const wasteRecycling = RECYCLING_FACTORS[entry.waste_recycling.toLowerCase()] ?? 30.0;
  const wastePlastic = PLASTIC_FACTORS[entry.waste_plastic.toLowerCase()] ?? 25.0;
  const wasteTotal = wasteRecycling + wastePlastic;

  // 6. Total
  const total = transportTotal + energyTotal + foodTotal + shoppingTotal + wasteTotal;

  // Percentages
  let transportPct = 0;
  let energyPct = 0;
  let foodPct = 0;
  let shoppingPct = 0;
  let wastePct = 0;

  if (total > 0) {
    transportPct = (transportTotal / total) * 100;
    energyPct = (energyTotal / total) * 100;
    foodPct = (foodTotal / total) * 100;
    shoppingPct = (shoppingTotal / total) * 100;
    wastePct = (wasteTotal / total) * 100;
  }

  const roundToTwo = (num: number) => Math.round(num * 100) / 100;
  const roundToOne = (num: number) => Math.round(num * 10) / 10;

  return {
    total_emissions: roundToTwo(total),
    breakdown: {
      transportation: roundToTwo(transportTotal),
      energy: roundToTwo(energyTotal),
      food: roundToTwo(foodTotal),
      shopping: roundToTwo(shoppingTotal),
      waste: roundToTwo(wasteTotal),
    },
    percentages: {
      transportation: roundToOne(transportPct),
      energy: roundToOne(energyPct),
      food: roundToOne(foodPct),
      shopping: roundToOne(shoppingPct),
      waste: roundToOne(wastePct),
    },
  };
}
