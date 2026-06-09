import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.models import db, Challenge

def create_app(config_class=Config):
    # Set static_folder to serve the frontend directory directly
    # Set static_url_path to "" so frontend resources are served at the root (e.g. /css/style.css)
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    app.config.from_object(config_class)

    # Enable CORS for cross-origin local testing
    CORS(app)

    # Initialize Database
    db.init_app(app)

    # Register blueprints with /api prefix to match frontend paths
    from backend.routes.calculator import calculator_bp
    from backend.routes.challenges import challenges_bp
    from backend.routes.analytics import analytics_bp
    from backend.routes.recommendations import recommendations_bp

    app.register_blueprint(calculator_bp, url_prefix='/api/calculator')
    app.register_blueprint(challenges_bp, url_prefix='/api/challenges')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')

    # Serve index.html at root
    @app.route('/')
    def serve_index():
        return app.send_static_file('index.html')

    # Catch-all route to serve index.html for SPA client-side routing
    @app.errorhandler(404)
    def page_not_found(e):
        # Check if the requested path starts with /api
        # If it does, return a JSON 404, not the HTML index
        if request.path.startswith('/api'):
            return jsonify({"detail": "Not found"}), 404
        return app.send_static_file('index.html')

    # Seed Database on startup
    with app.app_context():
        try:
            # Automatically ensure MySQL database exists before creating tables
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
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
                    print(f"Database '{db_name}' ensured successfully.")
                except Exception as e:
                    print(f"[WARNING] Could not automatically create MySQL database: {e}")

            db.create_all()
            # Seed default challenges if empty
            if Challenge.query.count() == 0:
                challenges = [
                    Challenge(id=1, title="No Plastic Day", description="Avoid single-use plastics for an entire day.", difficulty="Beginner", points=50),
                    Challenge(id=2, title="Meat-Free Monday", description="Eat only plant-based meals today.", difficulty="Intermediate", points=100),
                    Challenge(id=3, title="Public Transport Week", description="Commute using only public transit or active transit (walk/bike) for 5 days.", difficulty="Advanced", points=250),
                    Challenge(id=4, title="Zero Waste Weekend", description="Generate absolutely zero landfill waste from Friday night to Monday morning.", difficulty="Expert", points=500)
                ]
                try:
                    db.session.bulk_save_objects(challenges)
                    db.session.commit()
                    print("Seeded default challenges successfully.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error seeding challenges: {e}")
        except Exception as db_init_err:
            print(f"[ERROR] Database creation/seeding failed at startup: {db_init_err}")

    return app
