"""
Centralized HTTP error handlers for Campus_Sync.
Registered on the Flask app via register_error_handlers().
"""

from flask import render_template, jsonify, request


def wants_json(req) -> bool:
    """Return True if the client prefers a JSON response."""
    best = req.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json"


def register_error_handlers(app):
    """Attach all HTTP error handlers to the Flask app."""

    @app.errorhandler(400)
    def bad_request(e):
        if wants_json(request):
            return jsonify(error="Bad Request", message=str(e)), 400
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        if wants_json(request):
            return jsonify(error="Forbidden", message=str(e)), 403
        return render_template("errors/403.html", error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        if wants_json(request):
            return jsonify(error="Not Found", message=str(e)), 404
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if wants_json(request):
            return jsonify(error="Internal Server Error", message=str(e)), 500
        return render_template("errors/500.html", error=e), 500
