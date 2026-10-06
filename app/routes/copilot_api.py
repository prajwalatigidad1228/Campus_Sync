"""
Campus_Sync – AI Copilot Chat API Blueprint (Phase 5)

Routes:
  POST /api/copilot/chat  – Authenticated, role-aware RAG AI chat
  POST /api/copilot/clear – Reset active session conversation history
"""

from flask import Blueprint, request, jsonify, session
from flask_login import current_user

from app.auth.decorators import login_required
from app.ai.copilot_engine import CopilotEngine

copilot_api_bp = Blueprint("copilot_api", __name__, url_prefix="/api/copilot")


@copilot_api_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    """
    Primary conversational endpoint for AI College Copilot.
    Strictly verifies authentication and passes current_user to CopilotEngine.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Message content cannot be empty."}), 400

    # Retrieve existing session history if none provided in request payload
    if not history:
        history = session.get("copilot_history", [])

    # Process query through role authorization, tools, and RAG
    result = CopilotEngine.chat(user=current_user, query=message, history=history)

    # Persist updated session history (capped at last 10 turns)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result["response"]})
    session["copilot_history"] = history[-10:]

    return jsonify({
        "status": "success",
        "response": result["response"],
        "source": result.get("source"),
        "is_denied": result.get("is_denied", False),
    }), 200


@copilot_api_bp.route("/clear", methods=["POST"])
@login_required
def clear_chat():
    """Clear conversational memory stored in the active session."""
    session.pop("copilot_history", None)
    return jsonify({"status": "success", "message": "Chat history cleared."}), 200
