import os
import logging
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from backend.models import db, Challenge
from typing import Any, Optional

def create_app(config_class: Optional[Any] = None) -> Flask:
    """Application factory for EcoTrack AI Flask web application."""
    if config_class is None:
        from backend.config import config_by_name
        env: str = os.getenv("FLASK_ENV", "development")
        config_class = config_by_name.get(env, config_by_name["development"])
    elif isinstance(config_class, str):
        from backend.config import config_by_name
        config_class = config_by_name.get(config_class, config_by_name["development"])

    # Set static_folder to serve the frontend directory directly
    # Set static_url_path to "" so frontend resources are served at the root (e.g. /css/style.css)
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    app.config.from_object(config_class)

    # Action 1: Standardized Centralized Logger configuration
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    app.logger.info("Initializing EcoTrack AI Web Application Factory...")

    # Enable CORS for cross-origin local testing
    CORS(app)

    # Initialize Database
    db.init_app(app)
    from flask_migrate import Migrate
    migrate = Migrate()
    migrate.init_app(app, db)

    # Register blueprints with /api prefix to match frontend paths
    from backend.routes.calculator import calculator_bp
    from backend.routes.challenges import challenges_bp
    from backend.routes.analytics import analytics_bp
    from backend.routes.recommendations import recommendations_bp
    from backend.routes.auth import auth_bp

    app.register_blueprint(calculator_bp, url_prefix='/api/calculator')
    app.register_blueprint(challenges_bp, url_prefix='/api/challenges')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Serve index.html at root
    @app.route('/')
    def serve_index() -> Response:
        return app.send_static_file('index.html')

    # Catch-all route to serve index.html for SPA client-side routing
    @app.errorhandler(404)
    def page_not_found(e: Any) -> Response:
        # Check if the requested path starts with /api
        # If it does, return a JSON 404, not the HTML index
        if request.path.startswith('/api'):
            return jsonify({"detail": "Not found"}), 404
        return app.send_static_file('index.html')

    # Action 5: Global Request CSRF Validation Hook
    @app.before_request
    def validate_csrf() -> Optional[Response]:
        """Intercepts writing state-changing API endpoints, validating secure custom header."""
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            if request.path.startswith('/api') and not app.config.get('TESTING'):
                if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                    app.logger.warning(f"Rejected state-changing request to {request.path} due to missing secure CSRF header.")
                    return jsonify({"detail": "CSRF validation failed. Missing secure header."}), 403
        return None

    # Action 4: Global Response Security Headers Hook
    @app.after_request
    def add_security_headers(response: Response) -> Response:
        """Injects recommended secure HTTP response headers to harden the application."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' cdn.jsdelivr.net; "
            "style-src 'self' fonts.googleapis.com; "
            "font-src fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
        return response

    # Seed Database on startup
    with app.app_context():
        try:
            # Automatically ensure MySQL database exists before creating tables
            db_uri: Optional[str] = app.config.get('SQLALCHEMY_DATABASE_URI')
            if db_uri and db_uri.startswith('mysql'):
                try:
                    server_uri, db_name = db_uri.rsplit('/', 1)
                    if '?' in db_name:
                        db_name = db_name.split('?', 1)[0]
                    
                    from sqlalchemy import create_engine, text
                    temp_engine = create_engine(server_uri)
                    with temp_engine.connect() as conn:
                        # Automatically commit the transaction for database creation
                        conn.execution_options(isolation_level="AUTOCOMMIT")
                        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
                    temp_engine.dispose()
                    app.logger.info(f"Database '{db_name}' ensured successfully.")
                except Exception as mysql_err:
                    app.logger.warning(f"Could not automatically create MySQL database: {mysql_err}")

            db.create_all()
            
            # Action 9: Seeding check optimization (uses LIMIT 1 check instead of scanning full table counts)
            if Challenge.query.first() is None:
                challenges = [
                    Challenge(
                        id=1,
                        title="No Plastic Day",
                        description="Avoid single-use plastics for an entire day.\n\nRules & Habits:\n1. Carry a reusable water bottle instead of buying bottled beverages.\n2. Bring a reusable cloth tote bag for shopping.\n3. Refuse plastic straws, cutlery, and containers.",
                        difficulty="Beginner",
                        points=50
                    ),
                    Challenge(
                        id=2,
                        title="Meat-Free Monday",
                        description="Eat only plant-based meals today.\n\nRules & Habits:\n1. Exclude all meat, poultry, and fish from all meals.\n2. Experiment with dairy-free alternatives like oat or soy milk.\n3. Build satisfying meals around grains, legumes, and fresh vegetables.",
                        difficulty="Intermediate",
                        points=100
                    ),
                    Challenge(
                        id=3,
                        title="Public Transport Week",
                        description="Commute using only public transit or active transit (walk/bike) for 5 days.\n\nRules & Habits:\n1. Leave your car at home for your daily commutes.\n2. Walk, run, bicycle, or ride buses, subways, or light rails.\n3. Combine errands to minimize extra trips.",
                        difficulty="Advanced",
                        points=250
                    ),
                    Challenge(
                        id=4,
                        title="Zero Waste Weekend",
                        description="Generate absolutely zero landfill waste from Friday night to Monday morning.\n\nRules & Habits:\n1. Avoid buying goods packaged in non-recyclable materials.\n2. Compost all food scraps and organic waste.\n3. Maximize sorting for standard paper, metal, and glass recycling.",
                        difficulty="Expert",
                        points=500
                    )
                ]
                try:
                    db.session.bulk_save_objects(challenges)
                    db.session.commit()
                    app.logger.info("Seeded default challenges successfully.")
                except Exception as seed_err:
                    db.session.rollback()
                    app.logger.error(f"Error seeding challenges: {seed_err}")
        except Exception as db_init_err:
            app.logger.critical(f"Database creation/seeding failed at startup: {db_init_err}")

    @app.cli.command("db-backup")
    def db_backup() -> None:
        """Backup all user carbon footprint history to a JSON file."""
        import json
        from datetime import datetime
        from backend.models import User, CarbonEntry, ChallengeProgress, Recommendation
        
        backup_dir = os.path.join(app.root_path, "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")
        
        data = {
            "users": [],
            "carbon_entries": [],
            "challenge_progress": [],
            "recommendations": []
        }
        
        for u in User.query.all():
            data["users"].append({
                "id": u.id,
                "email": u.email,
                "password_hash": u.password_hash,
                "created_at": u.created_at.isoformat()
            })
            
        for e in CarbonEntry.query.all():
            data["carbon_entries"].append({
                "id": e.id,
                "user_id": e.user_id,
                "transportation_car": e.transportation_car,
                "transportation_bike": e.transportation_bike,
                "transportation_public": e.transportation_public,
                "transportation_flights": e.transportation_flights,
                "energy_electricity": e.energy_electricity,
                "energy_ac": e.energy_ac,
                "energy_appliance": e.energy_appliance,
                "food_preference": e.food_preference,
                "shopping_clothing": e.shopping_clothing,
                "shopping_electronics": e.shopping_electronics,
                "waste_recycling": e.waste_recycling,
                "waste_plastic": e.waste_plastic,
                "total_emissions": e.total_emissions,
                "created_at": e.created_at.isoformat()
            })
            
        for p in ChallengeProgress.query.all():
            data["challenge_progress"].append({
                "id": p.id,
                "user_id": p.user_id,
                "challenge_id": p.challenge_id,
                "start_date": p.start_date.isoformat(),
                "end_date": p.end_date.isoformat(),
                "completion_status": p.completion_status,
                "points_earned": p.points_earned,
                "proof_text": p.proof_text
            })
            
        for r in Recommendation.query.all():
            data["recommendations"].append({
                "id": r.id,
                "user_id": r.user_id,
                "title": r.title,
                "description": r.description,
                "difficulty": r.difficulty,
                "expected_reduction": r.expected_reduction,
                "estimated_savings": r.estimated_savings,
                "is_completed": r.is_completed,
                "created_at": r.created_at.isoformat()
            })
            
        with open(backup_file, "w") as f:
            json.dump(data, f, indent=2)
            
        app.logger.info(f"Database backed up successfully to: {backup_file}")

    return app
