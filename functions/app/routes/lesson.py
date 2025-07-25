from flask import Blueprint, jsonify, request
from langchain_core.messages import HumanMessage
from app.workflows.langgraph_workflow import workflow

lesson_bp = Blueprint('lesson', __name__)

@lesson_bp.route('/')
def home():
    return jsonify({
        "message": "Professor Agent API is running",
        "endpoints": {
            "generate_lesson": "/api/generate-lesson [POST]",
            "health": "/api/health [GET]"
        }
    })

@lesson_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Professor Agent API",
        "version": "1.0.0"
    })

@lesson_bp.route('/api/generate-lesson', methods=['POST'])
def generate_lesson():
    try:
        data = request.get_json()
        subject = data.get('subject', '')
        grades = data.get('grades', '')
        topic = data.get('topic', '')
        special_needs = data.get('special_needs', 'Standard differentiation')
        user_message = data.get('message', 'Generate a lesson plan')

        if not all([subject, grades, topic]):
            return jsonify({"error": "Missing required fields"}), 400

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "lesson_plan": "",
            "subject": subject,
            "grades": grades,
            "topic": topic,
            "special_needs": special_needs
        }

        result = workflow.invoke(initial_state)

        return jsonify({
            "success": True,
            "lesson_plan": result["lesson_plan"],
            "metadata": {
                "subject": subject,
                "grades": grades,
                "topic": topic,
                "special_needs": special_needs
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lesson_bp.route('/api/generate-lesson-simple', methods=['POST'])
def generate_lesson_simple():
    try:
        data = request.get_json()
        message = data.get('message', 'Generate a basic lesson plan')

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "lesson_plan": "",
            "subject": "General",
            "grades": "Mixed",
            "topic": "General Learning",
            "special_needs": "Standard differentiation"
        }

        result = workflow.invoke(initial_state)

        return jsonify({
            "success": True,
            "lesson_plan": result["lesson_plan"]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500