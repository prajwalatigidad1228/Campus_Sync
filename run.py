"""
Campus_Sync – Application Entry Point
Run this file to start the development server:   python run.py
Seed demo data:                                  flask seed
"""

import os
import click
from dotenv import load_dotenv

load_dotenv()

from app import create_app

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)


# ── CLI command: flask seed ────────────────────────────────────────────────
@app.cli.command("seed")
def seed_command():
    """Seed the database with demo data (development only)."""
    from app.services.seeder import seed_all
    with app.app_context():
        seed_all()


if __name__ == "__main__":
    host  = os.getenv("FLASK_HOST",  "127.0.0.1")
    port  = int(os.getenv("FLASK_PORT",  5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    print(f"\n{'=' * 55}")
    print(f"  Campus_Sync  –  College Management + AI Copilot")
    print(f"  URL      : http://{host}:{port}")
    print(f"  Env      : {config_name}")
    print(f"  Login    : http://{host}:{port}/auth/login")
    print(f"  Health   : http://{host}:{port}/api/health")
    print(f"  Seed DB  : flask seed")
    print(f"{'=' * 55}\n")

    app.run(host=host, port=port, debug=debug)
