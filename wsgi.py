from app import app, init_db

# Initialize/update tables when the web service starts.
# The target MySQL database must already exist and the configured user
# must have permission to create/alter the application's tables.
try:
    init_db()
except Exception as exc:
    # Keep the app importable so deployment logs show the database error.
    print(f"Database initialization warning: {exc}")
