from backend.app import create_app

# Instantiate the Flask application
app = create_app()

if __name__ == '__main__':
    print("\n[INFO] Starting EcoTrack AI Flask Server on http://127.0.0.1:8000 ...")
    print("[INFO] Serves both backend API endpoints and frontend static files.")
    print("[INFO] Press Ctrl+C to stop the server cleanly.\n")
    app.run(host='127.0.0.1', port=8000, debug=True)
