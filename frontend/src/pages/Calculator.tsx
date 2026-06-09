import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Car,
  Lightbulb,
  ShoppingBag,
  TrendingDown,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  Loader2,
  Calendar
} from 'lucide-react';
import api from '../services/api';
import type { CarbonEntry } from '../types';

export const Calculator: React.FC = () => {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CarbonEntry | null>(null);
  const navigate = useNavigate();

  // Questionnaire state
  const [formData, setFormData] = useState({
    transportation_car: 0,
    transportation_bike: 0,
    transportation_public: 0,
    transportation_flights: 0,
    energy_electricity: 0,
    energy_ac: 0,
    energy_appliance: 0,
    food_preference: 'non-vegetarian',
    shopping_clothing: 0,
    shopping_electronics: 0,
    waste_recycling: 'sometimes',
    waste_plastic: 'average',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { id, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [id]: type === 'number' ? Math.max(0, parseFloat(value) || 0) : value,
    }));
  };

  const nextStep = () => {
    setStep((prev) => Math.min(prev + 1, 4));
  };

  const prevStep = () => {
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/calculator/submit', formData);
      setResult(response.data);
      setStep(4); // Move to results step
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred while calculating emissions.');
    } finally {
      setIsLoading(false);
    }
  };

  const stepsCount = 3;

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">Carbon Calculator</h1>
        <p className="text-slate-400 mt-2">
          Tell us about your lifestyle to estimate your monthly carbon footprint.
        </p>
      </div>

      {step < 4 && (
        <div className="mb-8" aria-label="Calculator Progress">
          <div className="flex justify-between items-center max-w-sm mx-auto">
            {[1, 2, 3].map((num) => (
              <div key={num} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                    step >= num
                      ? 'bg-accent text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                  aria-current={step === num ? 'step' : undefined}
                >
                  {num}
                </div>
                {num < stepsCount && (
                  <div
                    className={`w-16 sm:w-24 h-1 mx-2 rounded transition-all ${
                      step > num ? 'bg-accent' : 'bg-slate-800'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="text-center mt-3 text-sm text-slate-400 font-medium">
            {step === 1 && 'Step 1: Transportation'}
            {step === 2 && 'Step 2: Energy & Diet'}
            {step === 3 && 'Step 3: Habits & Shopping'}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-950/40 border border-red-900 rounded-xl text-red-200 text-sm" role="alert">
          {error}
        </div>
      )}

      <div className="glass-card rounded-2xl p-6 sm:p-10 border border-slate-800 shadow-xl relative overflow-hidden">
        {step === 1 && (
          <div className="animate-fade-in space-y-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-primary/20 p-2.5 rounded-lg text-accent">
                <Car className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-white">Transportation</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="transportation_car" className="block text-sm font-medium text-slate-300 mb-2">
                  Car Distance (km / month)
                </label>
                <input
                  id="transportation_car"
                  type="number"
                  min="0"
                  value={formData.transportation_car}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="transportation_bike" className="block text-sm font-medium text-slate-300 mb-2">
                  Bicycle Distance (km / month)
                </label>
                <input
                  id="transportation_bike"
                  type="number"
                  min="0"
                  value={formData.transportation_bike}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="transportation_public" className="block text-sm font-medium text-slate-300 mb-2">
                  Public Transit Distance (bus/train in km / month)
                </label>
                <input
                  id="transportation_public"
                  type="number"
                  min="0"
                  value={formData.transportation_public}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="transportation_flights" className="block text-sm font-medium text-slate-300 mb-2">
                  Flight Distance (km / month)
                </label>
                <input
                  id="transportation_flights"
                  type="number"
                  min="0"
                  value={formData.transportation_flights}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button onClick={nextStep} className="btn-primary flex items-center space-x-2">
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="animate-fade-in space-y-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-primary/20 p-2.5 rounded-lg text-accent">
                <Lightbulb className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-white">Energy & Diet</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="energy_electricity" className="block text-sm font-medium text-slate-300 mb-2">
                  Electricity Usage (kWh / month)
                </label>
                <input
                  id="energy_electricity"
                  type="number"
                  min="0"
                  value={formData.energy_electricity}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="energy_ac" className="block text-sm font-medium text-slate-300 mb-2">
                  Air Conditioner Usage (hours / month)
                </label>
                <input
                  id="energy_ac"
                  type="number"
                  min="0"
                  value={formData.energy_ac}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="energy_appliance" className="block text-sm font-medium text-slate-300 mb-2">
                  Major Appliances (washing machine/oven in hours / month)
                </label>
                <input
                  id="energy_appliance"
                  type="number"
                  min="0"
                  value={formData.energy_appliance}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="food_preference" className="block text-sm font-medium text-slate-300 mb-2">
                  Diet Preference
                </label>
                <select
                  id="food_preference"
                  value={formData.food_preference}
                  onChange={handleInputChange}
                  className="text-input focusable"
                >
                  <option value="vegan">Vegan (Entirely plant-based)</option>
                  <option value="vegetarian">Vegetarian (No meat, dairy included)</option>
                  <option value="non-vegetarian">Non-Vegetarian (Consumes meat/poultry)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button onClick={prevStep} className="btn-secondary flex items-center space-x-2">
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button onClick={nextStep} className="btn-primary flex items-center space-x-2">
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <form onSubmit={handleSubmit} className="animate-fade-in space-y-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="bg-primary/20 p-2.5 rounded-lg text-accent">
                <ShoppingBag className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-white">Consumption & Waste Habits</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="shopping_clothing" className="block text-sm font-medium text-slate-300 mb-2">
                  New Clothing Purchased (items / month)
                </label>
                <input
                  id="shopping_clothing"
                  type="number"
                  min="0"
                  value={formData.shopping_clothing}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="shopping_electronics" className="block text-sm font-medium text-slate-300 mb-2">
                  New Electronics Purchased (devices / month)
                </label>
                <input
                  id="shopping_electronics"
                  type="number"
                  min="0"
                  value={formData.shopping_electronics}
                  onChange={handleInputChange}
                  className="text-input focusable"
                />
              </div>

              <div>
                <label htmlFor="waste_recycling" className="block text-sm font-medium text-slate-300 mb-2">
                  Recycling Frequency
                </label>
                <select
                  id="waste_recycling"
                  value={formData.waste_recycling}
                  onChange={handleInputChange}
                  className="text-input focusable"
                >
                  <option value="rarely">Rarely</option>
                  <option value="sometimes">Sometimes</option>
                  <option value="always">Always</option>
                </select>
              </div>

              <div>
                <label htmlFor="waste_plastic" className="block text-sm font-medium text-slate-300 mb-2">
                  Single-Use Plastic Consumption
                </label>
                <select
                  id="waste_plastic"
                  value={formData.waste_plastic}
                  onChange={handleInputChange}
                  className="text-input focusable"
                >
                  <option value="low">Low (Avoid bottles/containers)</option>
                  <option value="average">Average (Moderate plastic packaging)</option>
                  <option value="high">High (Rely on pre-packaged foods/bottles)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button type="button" onClick={prevStep} className="btn-secondary flex items-center space-x-2" disabled={isLoading}>
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary flex items-center space-x-2 px-6 shadow-lg shadow-primary/20"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Calculating...</span>
                  </>
                ) : (
                  <>
                    <span>Calculate footprint</span>
                    <TrendingDown className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {step === 4 && result && (
          <div className="animate-fade-in text-center space-y-6">
            <div className="flex justify-center text-accent mb-4">
              <CheckCircle className="w-16 h-16 animate-bounce" />
            </div>
            
            <h2 className="text-3xl font-extrabold text-white">Calculation Complete!</h2>
            <p className="text-slate-300 text-base max-w-lg mx-auto">
              Your carbon emissions have been updated. AI recommendations and analytics have been updated based on your response.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto py-6">
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-center">
                <span className="text-sm text-slate-400 font-semibold uppercase tracking-wider">Monthly Emissions</span>
                <span className="text-3xl font-extrabold text-accent mt-2">
                  {result.total_emissions} kg
                </span>
                <span className="text-xs text-slate-500 mt-1">CO₂ equivalent</span>
              </div>
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-center">
                <span className="text-sm text-slate-400 font-semibold uppercase tracking-wider">Annual Footprint</span>
                <span className="text-3xl font-extrabold text-green-400 mt-2">
                  {Math.round(result.total_emissions * 12)} kg
                </span>
                <span className="text-xs text-slate-500 mt-1">CO₂ equivalent / year</span>
              </div>
            </div>

            <div className="flex justify-center space-x-4 pt-4">
              <button
                onClick={() => {
                  setResult(null);
                  setStep(1);
                }}
                className="btn-secondary flex items-center space-x-2"
              >
                <Calendar className="w-4 h-4" />
                <span>Re-estimate</span>
              </button>
              <button onClick={() => navigate('/')} className="btn-primary flex items-center space-x-2">
                <span>View Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
