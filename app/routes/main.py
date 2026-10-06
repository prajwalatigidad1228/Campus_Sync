"""
Main / public routes for Campus_Sync.
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page – placeholder until the UI phase."""
    return render_template("index.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")
