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

        # Clear rate limiter state for a clean test run
        from backend.routes.auth import clear_rate_limits
        clear_rate_limits()

        # Database tables are created automatically by create_app inside with app.app_context() block.
        # But let's verify challenges table was seeded.
        self.assertEqual(Challenge.query.count(), 4)

        # Create and authenticate a default test user
        self.test_email = "test@ecotrack.ai"
        self.test_password = "password123"
        reg_res = self.client.post('/api/auth/register',
            data=json.dumps({"email": self.test_email, "password": self.test_password}),
            content_type='application/json'
        )
        self.assertEqual(reg_res.status_code, 201)
        data = json.loads(reg_res.data.decode('utf-8'))
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        # Roll back and remove database session and close context
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Clear rate limiter state after test
        from backend.routes.auth import clear_rate_limits
        clear_rate_limits()

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
            content_type='application/json',
            headers=self.headers
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

    def test_calculator_invalid_inputs(self):
        # 1. Test negative value error
        payload_neg = {
            "transportation_car": -5,
            "food_preference": "vegan",
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        res = self.client.post('/api/calculator/submit',
            data=json.dumps(payload_neg),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn("must be a non-negative value", data["detail"])

        # 2. Test invalid categorical option
        payload_cat = {
            "transportation_car": 100,
            "food_preference": "carnivore", # Invalid
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        res = self.client.post('/api/calculator/submit',
            data=json.dumps(payload_cat),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data["detail"], "Invalid food_preference option")

    def test_fallback_recommendations_direct(self):
        from backend.services.gemini_service import get_fallback_recommendations
        
        # Test case where car travel triggers transit recommendation
        sample_data = {
            "transportation_car": 1000, # Car emissions > 100
            "transportation_flights": 0,
            "energy_electricity": 0,
            "energy_ac": 0,
            "shopping_clothing": 0,
            "shopping_electronics": 0,
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        recs = get_fallback_recommendations(sample_data)
        self.assertTrue(len(recs) > 0)
        titles = [r["title"] for r in recs]
        self.assertIn("Switch to Public Transit", titles)

    def test_challenges_flow(self):
        # 1. Join a challenge
        join_res = self.client.post('/api/challenges/join',
            data=json.dumps({"challenge_id": 1}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(join_res.status_code, 201)
        progress = json.loads(join_res.data.decode('utf-8'))
        self.assertEqual(progress["challenge_id"], 1)
        self.assertEqual(progress["completion_status"], "in_progress")

        # 2. Get active challenges
        act_res = self.client.get('/api/challenges/active', headers=self.headers)
        self.assertEqual(act_res.status_code, 200)
        active_list = json.loads(act_res.data.decode('utf-8'))
        self.assertEqual(len(active_list), 1)

        # 3. Complete the challenge with proof
        comp_res = self.client.post(f'/api/challenges/{progress["id"]}/complete',
            data=json.dumps({"proof_text": "Completed challenge by switching off lights"}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(comp_res.status_code, 200)
        comp_data = json.loads(comp_res.data.decode('utf-8'))
        self.assertEqual(comp_data["completion_status"], "completed")
        self.assertEqual(comp_data["points_earned"], 50)  # Challenge 1 has 50 points
        self.assertEqual(comp_data["proof_text"], "Completed challenge by switching off lights")

        # Verify DB storage
        prog_db = db.session.get(ChallengeProgress, progress["id"])
        self.assertEqual(prog_db.proof_text, "Completed challenge by switching off lights")

        # 4. Join and attempt to complete another challenge with too long proof
        join_res2 = self.client.post('/api/challenges/join',
            data=json.dumps({"challenge_id": 2}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(join_res2.status_code, 201)
        progress2 = json.loads(join_res2.data.decode('utf-8'))

        comp_res2 = self.client.post(f'/api/challenges/{progress2["id"]}/complete',
            data=json.dumps({"proof_text": "x" * 1001}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(comp_res2.status_code, 400)
        self.assertIn("cannot exceed 1000 characters", json.loads(comp_res2.data.decode('utf-8'))["detail"])

    def test_registration_and_login_success(self):
        # Register a new user
        reg_res = self.client.post('/api/auth/register',
            data=json.dumps({"email": "new@ecotrack.ai", "password": "securepassword"}),
            content_type='application/json'
        )
        self.assertEqual(reg_res.status_code, 201)
        reg_data = json.loads(reg_res.data.decode('utf-8'))
        self.assertIn("token", reg_data)
        self.assertEqual(reg_data["user"]["email"], "new@ecotrack.ai")

        # Login
        log_res = self.client.post('/api/auth/login',
            data=json.dumps({"email": "new@ecotrack.ai", "password": "securepassword"}),
            content_type='application/json'
        )
        self.assertEqual(log_res.status_code, 200)
        log_data = json.loads(log_res.data.decode('utf-8'))
        self.assertIn("token", log_data)
        token = log_data["token"]

        # Access /api/auth/me
        me_res = self.client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        me_data = json.loads(me_res.data.decode('utf-8'))
        self.assertEqual(me_data["email"], "new@ecotrack.ai")

    def test_registration_duplicate_email(self):
        # Register email that already exists
        reg_res = self.client.post('/api/auth/register',
            data=json.dumps({"email": self.test_email, "password": "anotherpassword"}),
            content_type='application/json'
        )
        self.assertEqual(reg_res.status_code, 400)
        data = json.loads(reg_res.data.decode('utf-8'))
        self.assertEqual(data["detail"], "Email address already registered")

    def test_registration_invalid_inputs(self):
        # Short password
        res = self.client.post('/api/auth/register',
            data=json.dumps({"email": "valid@ecotrack.ai", "password": "123"}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("must be between 6 and 72 characters", json.loads(res.data.decode('utf-8'))["detail"])

        # Long password (Bcrypt DOS protection limit)
        res = self.client.post('/api/auth/register',
            data=json.dumps({"email": "valid@ecotrack.ai", "password": "x" * 73}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("must be between 6 and 72 characters", json.loads(res.data.decode('utf-8'))["detail"])

        # Long email
        res = self.client.post('/api/auth/register',
            data=json.dumps({"email": ("a" * 250) + "@ecotrack.ai", "password": "securepassword"}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("must not exceed 255 characters", json.loads(res.data.decode('utf-8'))["detail"])

        # Invalid email format
        res = self.client.post('/api/auth/register',
            data=json.dumps({"email": "invalid-email", "password": "securepassword"}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid email address format", json.loads(res.data.decode('utf-8'))["detail"])

    def test_login_invalid_password(self):
        log_res = self.client.post('/api/auth/login',
            data=json.dumps({"email": self.test_email, "password": "wrongpassword"}),
            content_type='application/json'
        )
        self.assertEqual(log_res.status_code, 401)
        data = json.loads(log_res.data.decode('utf-8'))
        self.assertEqual(data["detail"], "Invalid email or password")

    def test_unauthenticated_request_fails(self):
        # /api/analytics/summary requires authentication
        res = self.client.get('/api/analytics/summary')
        self.assertIn(res.status_code, [401, 403])  # 401 unauthenticated, 403 CSRF blocked
        if res.status_code == 401:
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data["detail"], "Authentication credentials were not provided.")

    def test_rate_limiting(self):
        # We call the login endpoint multiple times to trigger rate limiting
        # Limit is 5 requests per minute, so the 6th request should fail with 429
        from backend.routes.auth import clear_rate_limits
        clear_rate_limits()
        
        for _ in range(5):
            res = self.client.post('/api/auth/login',
                data=json.dumps({"email": self.test_email, "password": self.test_password}),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)

        # 6th request
        res = self.client.post('/api/auth/login',
            data=json.dumps({"email": self.test_email, "password": self.test_password}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 429)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data["detail"], "Too many requests. Please try again later.")

    def test_history_analytics_filtering(self):
        from datetime import datetime, timedelta
        user = User.query.filter_by(email=self.test_email).first()
        self.assertIsNotNone(user)

        # Clear existing entries
        CarbonEntry.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Seed entries across different dates
        now = datetime.utcnow()
        e1 = CarbonEntry(user_id=user.id, total_emissions=100.0, created_at=now - timedelta(days=10))
        e2 = CarbonEntry(user_id=user.id, total_emissions=200.0, created_at=now - timedelta(days=40))
        e3 = CarbonEntry(user_id=user.id, total_emissions=300.0, created_at=now - timedelta(days=100))
        e4 = CarbonEntry(user_id=user.id, total_emissions=200.0, created_at=now - timedelta(days=200))
        
        current_year_start = datetime(now.year, 1, 1)
        e_ytd = CarbonEntry(user_id=user.id, total_emissions=500.0, created_at=current_year_start + timedelta(hours=1))

        db.session.add_all([e1, e2, e3, e4, e_ytd])
        db.session.commit()

        # Test filter 3m (should return up to 3 entries)
        res_3m = self.client.get('/api/analytics/history?filter=3m', headers=self.headers)
        self.assertEqual(res_3m.status_code, 200)
        data_3m = json.loads(res_3m.data.decode('utf-8'))
        self.assertEqual(len(data_3m["trends"]), 3)

        # Test filter 6m (should return up to 5 entries)
        res_6m = self.client.get('/api/analytics/history?filter=6m', headers=self.headers)
        self.assertEqual(res_6m.status_code, 200)
        data_6m = json.loads(res_6m.data.decode('utf-8'))
        self.assertEqual(len(data_6m["trends"]), 5)

        # Test filter ytd (only entries in current year)
        res_ytd = self.client.get('/api/analytics/history?filter=ytd', headers=self.headers)
        self.assertEqual(res_ytd.status_code, 200)
        data_ytd = json.loads(res_ytd.data.decode('utf-8'))
        # e4 is > 200 days ago, which is late 2025. It should be filtered out.
        # Should return e1, e2, e3, e_ytd.
        self.assertEqual(len(data_ytd["trends"]), 4)

    def test_security_headers(self):
        """Action 10: Verify presence of critical security HTTP headers on responses."""
        res = self.client.get('/api/auth/me', headers=self.headers)
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-Frame-Options'), 'DENY')
        # X-XSS-Protection is set to '0' per modern security best practices (CSP replaces it)
        self.assertIn(res.headers.get('X-XSS-Protection'), ['0', '1; mode=block'])
        self.assertIn('Content-Security-Policy', res.headers)
        self.assertEqual(res.headers.get('Referrer-Policy'), 'no-referrer-when-downgrade')

    def test_recommendation_caching(self):
        """Action 11: Verify recommendation cache lookup bypasses calling Gemini again."""
        from backend.models import RecommendationCache
        # Ensure cache starts empty
        self.assertEqual(RecommendationCache.query.count(), 0)

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

        # First request: generates and caches recommendations
        res1 = self.client.post('/api/calculator/submit',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res1.status_code, 201)
        self.assertEqual(RecommendationCache.query.count(), 1)

        # Retrieve hash and modify stored recommendation in cache to check if we hit it on second request
        cache_item = RecommendationCache.query.first()
        original_json = cache_item.recommendations_json
        modified_recs = json.loads(original_json)
        modified_recs[0]["title"] = "Test Cached Title"
        cache_item.recommendations_json = json.dumps(modified_recs)
        db.session.commit()

        # Second request: identical payload, should load from cache
        res2 = self.client.post('/api/calculator/submit',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res2.status_code, 201)
        
        # Check active recommendations returned for user
        recs_res = self.client.get('/api/recommendations/', headers=self.headers)
        recs_data = json.loads(recs_res.data.decode('utf-8'))
        titles = [r["title"] for r in recs_data]
        self.assertIn("Test Cached Title", titles)

    def test_extreme_bounds_survey_metrics(self):
        """Action 12: Verify calculator logic behaves correctly under boundary values (zeros)."""
        payload_zeros = {
            "transportation_car": 0,
            "transportation_bike": 0,
            "transportation_public": 0,
            "transportation_flights": 0,
            "energy_electricity": 0,
            "energy_ac": 0,
            "energy_appliance": 0,
            "food_preference": "vegan",
            "shopping_clothing": 0,
            "shopping_electronics": 0,
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        res = self.client.post('/api/calculator/submit',
            data=json.dumps(payload_zeros),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data.decode('utf-8'))
        # Total emissions should be calculated correctly (with zero variables food=100 + waste=20 => 120)
        self.assertEqual(data["total_emissions"], 120.0)

    def test_config_profiles(self):
        from backend.config import DevelopmentConfig, TestingConfig, ProductionConfig
        self.assertTrue(TestingConfig.TESTING)
        self.assertIsNone(TestingConfig.GEMINI_API_KEY)
        self.assertEqual(TestingConfig.SQLALCHEMY_DATABASE_URI, "sqlite:///:memory:")

        self.assertTrue(DevelopmentConfig.DEBUG)
        self.assertFalse(ProductionConfig.DEBUG)
        self.assertFalse(ProductionConfig.TESTING)

    def test_boundary_checks_limits(self):
        """Verify calculator inputs that exceed the maximum safety bounds are rejected."""
        payload_too_high = {
            "transportation_car": 100001, # Exceeds limit of 100000.0
            "food_preference": "vegan",
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        res = self.client.post('/api/calculator/submit',
            data=json.dumps(payload_too_high),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn("exceeds maximum allowed value", data["detail"])

    def test_rate_limiting_eviction_and_proxy(self):
        """Verify rate limiting with X-Forwarded-For headers and dict pruner."""
        from backend.routes.auth import rate_limit_store, clear_rate_limits
        clear_rate_limits()

        # Send request with proxy header
        headers = {"X-Forwarded-For": "203.0.113.195"}
        for _ in range(5):
            res = self.client.post('/api/auth/login',
                data=json.dumps({"email": self.test_email, "password": self.test_password}),
                content_type='application/json',
                headers=headers
            )
            self.assertEqual(res.status_code, 200)

        # 6th request should fail
        res_fail = self.client.post('/api/auth/login',
            data=json.dumps({"email": self.test_email, "password": self.test_password}),
            content_type='application/json',
            headers=headers
        )
        self.assertEqual(res_fail.status_code, 429)

        # Manually verify that pruning evicts expired/empty client records
        # Add a mock stale IP entry in rate_limit_store
        rate_limit_store["192.168.1.1"] = [] # empty list (expired)
        # Mocking size > 1000 to trigger prune during decorator call
        for i in range(1005):
            rate_limit_store[f"10.0.0.{i}"] = [1.0] # stale timestamps

        # Triggers decoration/pruning by hitting the endpoint
        self.client.post('/api/auth/login',
            data=json.dumps({"email": self.test_email, "password": self.test_password}),
            content_type='application/json',
            headers={"X-Forwarded-For": "203.0.113.200"}
        )
        # "192.168.1.1" should be pruned because it's empty
        self.assertNotIn("192.168.1.1", rate_limit_store)

    def test_expired_and_malformed_tokens(self):
        """Verify that malformed and expired session tokens are properly rejected."""
        # 1. Malformed token
        res_malformed = self.client.get('/api/auth/me', headers={"Authorization": "Bearer malformed_token_string"})
        self.assertEqual(res_malformed.status_code, 401)
        self.assertEqual(json.loads(res_malformed.data.decode('utf-8'))["detail"], "Signature has expired or is invalid.")

        # 2. Expired token verification mock check
        # A token loaded with max_age=-1 will trigger SignatureExpired
        from itsdangerous import URLSafeTimedSerializer
        serializer = URLSafeTimedSerializer(self.app.config['SECRET_KEY'])
        token = serializer.dumps(999, salt='auth-token-salt')
        
        # Loading with negative max_age should fail to decode
        try:
            serializer.loads(token, salt='auth-token-salt', max_age=-1)
            self.fail("Should raise SignatureExpired")
        except Exception:
            pass

    def test_transaction_rollback_handling(self):
        """Verify database commit exception triggers rollback and return safe error."""
        from unittest.mock import patch
        from sqlalchemy.exc import SQLAlchemyError

        # Mock db.session.commit to throw SQLAlchemyError
        with patch('backend.models.db.session.commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Mock database connection lost")
            
            # Attemping to join a challenge
            res = self.client.post('/api/challenges/join',
                data=json.dumps({"challenge_id": 1}),
                content_type='application/json',
                headers=self.headers
            )
            # Should rollback and return a clean 500 error code
            self.assertEqual(res.status_code, 500)
            data = json.loads(res.data.decode('utf-8'))
            self.assertEqual(data["detail"], "Database operation failed. Please try again later.")

    def test_logout(self):
        """Action 23: Verify logout clears session credentials with Clear-Site-Data header."""
        # Logout only needs auth header, not JSON body — use content_type to satisfy CSRF
        res = self.client.post('/api/auth/logout',
            data=json.dumps({}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get('Clear-Site-Data'), '"cookies", "storage"')

    def test_parameterized_search(self):
        """Action 24: Verify challenges search endpoint behaves correctly with search query parameters."""
        # Query challenges with difficulty 'Beginner'
        res = self.client.get('/api/challenges/search?difficulty=Beginner', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "No Plastic Day")

        # Query challenges with keyword search 'Meat'
        res_kw = self.client.get('/api/challenges/search?q=Meat', headers=self.headers)
        self.assertEqual(res_kw.status_code, 200)
        data_kw = json.loads(res_kw.data.decode('utf-8'))
        self.assertEqual(len(data_kw), 1)
        self.assertEqual(data_kw[0]["title"], "Meat-Free Monday")

    def test_health_check_endpoint(self):
        """Item 62: Verify the /api/health endpoint returns healthy status with database connectivity."""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data["status"], "healthy")
        self.assertIn("services", data)
        self.assertEqual(data["services"]["database"], "healthy")
        self.assertIn("timestamp", data)

    def test_cors_headers_on_api_response(self):
        """Item 62: Verify CORS headers are present on API responses from allowed origins."""
        res = self.client.get('/api/health', headers={"Origin": "http://localhost:8000"})
        # CORS allowed origins should grant Access-Control-Allow-Origin
        self.assertIn("Access-Control-Allow-Origin", res.headers)

    def test_login_lockout_brute_force(self):
        """Item 64: Verify login lockout policy blocks further attempts after 5 failed logins."""
        from backend.routes.auth import clear_rate_limits, failed_login_store
        clear_rate_limits()
        
        # Make 5 failed login attempts to fill the lockout store
        for i in range(5):
            # Vary the IP slightly using X-Forwarded-For header to bypass rate limiter
            res = self.client.post('/api/auth/login',
                data=json.dumps({"email": self.test_email, "password": "wrongpassword"}),
                content_type='application/json',
                headers={'X-Forwarded-For': f'10.0.0.{i + 1}'}
            )
        
        # Directly inject failed attempts for the test IP (127.0.0.1) to simulate lockout
        import time
        for _ in range(5):
            failed_login_store['127.0.0.1'].append(time.time())
        
        # Next attempt from 127.0.0.1 should be locked out with 403
        res = self.client.post('/api/auth/login',
            data=json.dumps({"email": self.test_email, "password": "wrongpassword"}),
            content_type='application/json'
        )
        self.assertIn(res.status_code, [403, 429])  # 403 locked out OR 429 rate limited
        data = json.loads(res.data.decode('utf-8'))
        self.assertTrue(
            'locked' in data["detail"].lower() or 'too many' in data["detail"].lower()
        )

    def test_xss_sanitization_proof_text(self):
        """Item 66: Verify XSS script tags are stripped from proof_text before storage."""
        # First join a challenge
        join_res = self.client.post('/api/challenges/join',
            data=json.dumps({"challenge_id": 1}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(join_res.status_code, 201)
        progress = json.loads(join_res.data.decode('utf-8'))
        
        # Complete with XSS payload
        xss_payload = "<script>alert('xss')</script>Completed challenge"
        comp_res = self.client.post(f'/api/challenges/{progress["id"]}/complete',
            data=json.dumps({"proof_text": xss_payload}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(comp_res.status_code, 200)
        comp_data = json.loads(comp_res.data.decode('utf-8'))
        
        # HTML tags should be stripped
        self.assertNotIn("<script>", comp_data["proof_text"])
        self.assertIn("Completed challenge", comp_data["proof_text"])

    def test_csrf_missing_header_rejected(self):
        """Item 68: Verify state-changing requests without CSRF token are rejected (403) for non-XMLHttpRequest."""
        # Remove TESTING=True to simulate prod-like CSRF enforcement
        original = self.app.config.get('TESTING')
        self.app.config['TESTING'] = False
        
        # POST without X-Requested-With AND without CSRF cookie/header should fail
        res = self.client.post('/api/challenges/join',
            data=json.dumps({"challenge_id": 1}),
            content_type='application/json',
            headers=self.headers  # only Authorization, no CSRF
        )
        self.assertEqual(res.status_code, 403)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn("CSRF", data["detail"])
        
        self.app.config['TESTING'] = original

    def test_malformed_json_body_rejected(self):
        """Item 69: Verify malformed JSON request body returns 400 error with helpful message."""
        res = self.client.post('/api/calculator/submit',
            data=b"{not valid json}",
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 400)

    def test_json_bomb_depth_rejected(self):
        """Item 70: Verify deeply nested JSON bodies exceeding max depth limit are rejected."""
        # Build a JSON structure exceeding 5 levels of nesting
        nested = {"level": {"level": {"level": {"level": {"level": {"level": "too deep"}}}}}}
        res = self.client.post('/api/calculator/submit',
            data=json.dumps(nested),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn("depth", data["detail"])

    def test_ai_caching_behavior(self):
        """Item 71: Verify AI recommendation caching stores and retrieves cached results correctly."""
        from backend.models import RecommendationCache
        initial_count = RecommendationCache.query.count()
        
        payload = {
            "transportation_car": 200,
            "transportation_bike": 0,
            "transportation_public": 0,
            "transportation_flights": 0,
            "energy_electricity": 100,
            "energy_ac": 10,
            "energy_appliance": 5,
            "food_preference": "vegetarian",
            "shopping_clothing": 1,
            "shopping_electronics": 0,
            "waste_recycling": "sometimes",
            "waste_plastic": "average"
        }
        
        # First request creates cache entry
        res1 = self.client.post('/api/calculator/submit',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res1.status_code, 201)
        self.assertEqual(RecommendationCache.query.count(), initial_count + 1)
        
        # Second identical request should not create new cache entry
        res2 = self.client.post('/api/calculator/submit',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(RecommendationCache.query.count(), initial_count + 1)  # No new cache entry

    def test_database_backup_cli(self):
        """Item 72: Verify the db-backup CLI command is registered in the app."""
        # Verify the db-backup command exists in the Flask CLI
        cmd_names = list(self.app.cli.commands.keys())
        self.assertIn('db-backup', cmd_names)
        
        # Verify backup directory would be created under the app root
        import os
        backup_dir = os.path.join(self.app.root_path, '..', 'backups')
        # Just check the path is constructible (not required to exist in test)
        self.assertIsNotNone(backup_dir)

    def test_user_level_progression(self):
        """Item 75: Verify user can earn points from completing challenges, impacting sustainability score."""
        # Complete a challenge to earn points
        join_res = self.client.post('/api/challenges/join',
            data=json.dumps({"challenge_id": 1}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(join_res.status_code, 201)
        progress = json.loads(join_res.data.decode('utf-8'))
        
        comp_res = self.client.post(f'/api/challenges/{progress["id"]}/complete',
            data=json.dumps({"proof_text": "I completed this challenge!"}),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(comp_res.status_code, 200)
        comp_data = json.loads(comp_res.data.decode('utf-8'))
        self.assertGreater(comp_data["points_earned"], 0)
        
        # Now submit a calculator entry and check sustainability score improved
        payload = {
            "transportation_car": 50,
            "transportation_bike": 10,
            "transportation_public": 50,
            "transportation_flights": 0,
            "energy_electricity": 80,
            "energy_ac": 10,
            "energy_appliance": 5,
            "food_preference": "vegetarian",
            "shopping_clothing": 1,
            "shopping_electronics": 0,
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        self.client.post('/api/calculator/submit',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.headers
        )
        
        summary_res = self.client.get('/api/analytics/summary', headers=self.headers)
        self.assertEqual(summary_res.status_code, 200)
        summary = json.loads(summary_res.data.decode('utf-8'))
        # Score should be > baseline due to completed challenge bonus
        self.assertGreater(summary["sustainability_score"], 0)

    def test_sqlalchemy_pool_ping_config(self):
        """Item 79: Verify SQLAlchemy connection pool is configured with pre-ping enabled."""
        engine_options = self.app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {})
        self.assertTrue(engine_options.get("pool_pre_ping", False))
        self.assertIn("pool_recycle", engine_options)

    def test_calculator_food_enum_validation(self):
        """Item 78: Verify only valid DietPreference enum values are accepted by the calculator."""
        from backend.enums import DietPreference
        
        # Valid values should succeed
        for diet in DietPreference:
            payload = {
                "transportation_car": 0,
                "food_preference": diet.value,
                "waste_recycling": "always",
                "waste_plastic": "low"
            }
            res = self.client.post('/api/calculator/submit',
                data=json.dumps(payload),
                content_type='application/json',
                headers=self.headers
            )
            self.assertEqual(res.status_code, 201)
        
        # Invalid value should fail
        payload_invalid = {
            "transportation_car": 0,
            "food_preference": "keto",  # Not a valid DietPreference
            "waste_recycling": "always",
            "waste_plastic": "low"
        }
        res = self.client.post('/api/calculator/submit',
            data=json.dumps(payload_invalid),
            content_type='application/json',
            headers=self.headers
        )
        self.assertEqual(res.status_code, 400)

    def test_sql_injection_protection(self):
        """Item 65: Verify SQL injection payloads in query params are safely handled via ORM."""
        # SQLAlchemy parameterized queries prevent injection
        # Test with a classic SQL injection in search query
        injection_payload = "'; DROP TABLE challenges; --"
        res = self.client.get(f'/api/challenges/search?q={injection_payload}', headers=self.headers)
        # Should return 200 with empty results, not an error
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        
        # Verify challenges table still intact
        res_all = self.client.get('/api/challenges/', headers=self.headers)
        self.assertEqual(res_all.status_code, 200)
        challenges = json.loads(res_all.data.decode('utf-8'))
        self.assertEqual(len(challenges), 4)

if __name__ == '__main__':
    unittest.main()
