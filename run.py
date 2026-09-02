from app import create_app
from app.extensions import db

app = create_app()

if __name__ == "__main__":
    # create_all() is fine for initial development. Once the schema
    # stabilizes, switch to Flask-Migrate (Alembic) for real migrations —
    # we'll do that when we add the ML-related columns/tables in later steps.
    with app.app_context():
        db.create_all()
        
    import os
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    app.run(host=host, debug=True)
