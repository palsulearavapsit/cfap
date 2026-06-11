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

    # Configure CORS for specific local development origins only
    CORS(app, origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5000", "http://127.0.0.1:5000"])

    # Cap maximum allowed request body size to 2MB to prevent memory exhaustion DoS
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

    # Initialize Database
    db.init_app(app)
    
    # Enforce SQLite foreign key constraints dynamically on connection
    if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite'):
        from sqlalchemy import event
        with app.app_context():
            @event.listens_for(db.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    # Generate a cryptographically secure fallback secret key if unset
    if not app.config.get('SECRET_KEY') or app.config.get('SECRET_KEY') == 'your_cryptographic_secret_session_key':
        import secrets
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY was unconfigured or default. Generated a secure random fallback key.")

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

    # Global handler for JSON validation and custom ValidationError exceptions
    from werkzeug.exceptions import BadRequest
    from backend.exceptions import ValidationError

    @app.errorhandler(BadRequest)
    def handle_bad_request(e: BadRequest) -> Response:
        return jsonify({"detail": "Malformed request body. Please provide a valid JSON payload."}), 400

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError) -> Response:
        return jsonify({"detail": e.message}), e.status_code

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
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'

        # Static assets cache headers to maximize performance (Item 28)
        if request.path.startswith('/css/') or request.path.startswith('/js/') or request.path.endswith('.html'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'

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
            
            # Delegate seeding to the seeding module
            from backend.services.seeding import seed_challenges
            seed_challenges()
        except Exception as db_init_err:
            app.logger.critical(f"Database creation/seeding failed at startup: {db_init_err}")

    @app.cli.command("db-backup")
    def db_backup() -> None:
        """Backup all user carbon footprint history to a JSON file using streaming write optimizations."""
        import json
        from datetime import datetime
        from backend.models import User, CarbonEntry, ChallengeProgress, Recommendation
        
        backup_dir = os.path.join(app.root_path, "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")
        
        try:
            with open(backup_file, "w") as f:
                f.write("{\n")
                
                # 1. Stream Users
                f.write('  "users": [\n')
                users = User.query.all()
                for idx, u in enumerate(users):
                    user_data = {
                        "id": u.id,
                        "email": u.email,
                        "password_hash": u.password_hash,
                        "created_at": u.created_at.isoformat()
                    }
                    f.write("    " + json.dumps(user_data))
                    if idx < len(users) - 1:
                        f.write(",\n")
                    else:
                        f.write("\n")
                f.write("  ],\n")
                
                # 2. Stream Carbon Entries
                f.write('  "carbon_entries": [\n')
                entries = CarbonEntry.query.all()
                for idx, e in enumerate(entries):
                    entry_data = {
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
                    }
                    f.write("    " + json.dumps(entry_data))
                    if idx < len(entries) - 1:
                        f.write(",\n")
                    else:
                        f.write("\n")
                f.write("  ],\n")
                
                # 3. Stream Challenge Progress
                f.write('  "challenge_progress": [\n')
                progresses = ChallengeProgress.query.all()
                for idx, p in enumerate(progresses):
                    prog_data = {
                        "id": p.id,
                        "user_id": p.user_id,
                        "challenge_id": p.challenge_id,
                        "start_date": p.start_date.isoformat(),
                        "end_date": p.end_date.isoformat(),
                        "completion_status": p.completion_status,
                        "points_earned": p.points_earned,
                        "proof_text": p.proof_text
                    }
                    f.write("    " + json.dumps(prog_data))
                    if idx < len(progresses) - 1:
                        f.write(",\n")
                    else:
                        f.write("\n")
                f.write("  ],\n")
                
                # 4. Stream Recommendations
                f.write('  "recommendations": [\n')
                recs = Recommendation.query.all()
                for idx, r in enumerate(recs):
                    rec_data = {
                        "id": r.id,
                        "user_id": r.user_id,
                        "title": r.title,
                        "description": r.description,
                        "difficulty": r.difficulty,
                        "expected_reduction": r.expected_reduction,
                        "estimated_savings": r.estimated_savings,
                        "is_completed": r.is_completed,
                        "created_at": r.created_at.isoformat()
                    }
                    f.write("    " + json.dumps(rec_data))
                    if idx < len(recs) - 1:
                        f.write(",\n")
                    else:
                        f.write("\n")
                f.write("  ]\n")
                
                f.write("}\n")
            app.logger.info(f"Database backed up successfully to: {backup_file}")
        except Exception as err:
            app.logger.error(f"Failed to stream database backup: {str(err)}", exc_info=True)

    return app
