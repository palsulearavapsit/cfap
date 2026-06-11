import sys
import subprocess

def run_lint_and_format():
    """Helper script to run black/isort formatting checks on backend packages (Item 10)."""
    print("Starting EcoTrack code linter and formatting checker...")
    try:
        # Perform checking validation checks on Python directories
        subprocess.run(["black", "--check", "backend", "tests"], check=True)
        subprocess.run(["isort", "--check-only", "backend", "tests"], check=True)
        print("All code style checking passed successfully.")
        sys.exit(0)
    except FileNotFoundError:
        print("[NOTICE] Code style tools 'black' or 'isort' are not installed on the system path.")
        print("Skipping code formatter linter checks.")
        sys.exit(0)
    except subprocess.CalledProcessError as err:
        print(f"[ERROR] Lint styling checks failed: {err}")
        sys.exit(1)

if __name__ == '__main__':
    run_lint_and_format()
