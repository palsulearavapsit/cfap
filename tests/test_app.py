import unittest
import json
from backend.app import create_app
from backend.models import db, User, CarbonEntry, Challenge, ChallengeProgress, Recommendation
from backend.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test_secret_key"
    GEMINI_API_KEY = None  # Force rule-based fallback recommendations in tests

class EcoTrackTestCase(unittest.TestCase):

    def setUp(self):
        # Create app instance with testing configuration
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Database tables are created automatically by create_app inside with app.app_context() block.
        # But let's verify challenges table was seeded.
        self.assertEqual(Challenge.query.count(), 4)

    def tearDown(self):
        # Roll back and remove database session and close context
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_calculator_calculations(self):
        payload = {
            "transportation_car": 500,
            "transportation_bike": 20,
            "transportation_public": 100,
            "transportation_flights": 0,
            "energy_electricity": 150,
            "energy_ac": 20,
            "energy_appliance": 10,
            "food_preference": "vegan",
            "shopping_clothing": 2,
            "shopping_electronics": 0,
            "waste_recycling": "always",
            "waste_plastic": "low"
        }

        # Car: 500 * 0.171 = 85.5
        # Bike: 20 * 0.005 = 0.1
        # Public: 100 * 0.041 = 4.1
        # Electricity: 150 * 0.45 = 67.5
        # AC: 20 * 1.5 * 0.45 = 13.5
        # Appliance: 10 * 0.5 * 0.45 = 2.25
        # Food: vegan = 100.0
        # Shopping clothing: 2 * 15.0 = 30.0
        # Waste: recycling (always) = 10.0, plastic (low) = 10.0 => 20.0
        # Expected Total = 85.5 + 0.1 + 4.1 + 67.5 + 13.5 + 2.25 + 100.0 + 30.0 + 20.0 = 322.95

        res = self.client.post('/api/calculator/submit',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data["total_emissions"], 322.95)

        # Verify carbon entry was added to database
        entry = CarbonEntry.query.filter_by(user_id=data["user_id"]).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.total_emissions, 322.95)

        # Verify recommendations were pre-seeded/generated in the database
        recs = Recommendation.query.filter_by(user_id=data["user_id"]).all()
        self.assertGreater(len(recs), 0)

    def test_challenges_flow(self):
        # 1. Join a challenge
        join_res = self.client.post('/api/challenges/join',
            data=json.dumps({"challenge_id": 1}),
            content_type='application/json'
        )
        self.assertEqual(join_res.status_code, 201)
        progress = json.loads(join_res.data.decode('utf-8'))
        self.assertEqual(progress["challenge_id"], 1)
        self.assertEqual(progress["completion_status"], "in_progress")

        # 2. Get active challenges
        act_res = self.client.get('/api/challenges/active')
        self.assertEqual(act_res.status_code, 200)
        active_list = json.loads(act_res.data.decode('utf-8'))
        self.assertEqual(len(active_list), 1)

        # 3. Complete the challenge
        comp_res = self.client.post(f'/api/challenges/{progress["id"]}/complete')
        self.assertEqual(comp_res.status_code, 200)
        comp_data = json.loads(comp_res.data.decode('utf-8'))
        self.assertEqual(comp_data["completion_status"], "completed")
        self.assertEqual(comp_data["points_earned"], 50)  # Challenge 1 has 50 points

if __name__ == '__main__':
    unittest.main()
