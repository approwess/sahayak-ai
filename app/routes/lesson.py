from flask import Blueprint, jsonify, request, send_file
from langchain_core.messages import HumanMessage
from app.workflows.langgraph_workflow import workflow
import os
from pathlib import Path

lesson_bp = Blueprint('lesson', __name__)

@lesson_bp.route('/')
def home():
    return jsonify({
        "message": "Professor Agent API is running",
        "endpoints": {
            "generate_lesson": "/api/generate-lesson [POST]",
            "generate_visual_lesson": "/api/generate-visual-lesson [POST]",
            "download_visual_lesson": "/api/download-visual-lesson/<filename> [GET]",
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
        medium = data.get('medium', '')
        special_needs = data.get('special_needs', 'Standard differentiation')
        user_message = data.get('message', 'Generate a lesson plan')

        if not all([subject, grades, topic, medium]):
            return jsonify({"error": "Missing required fields"}), 400

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "lesson_plan": "",
            "subject": subject,
            "grades": grades,
            "topic": topic,
            "medium": medium,
            "special_needs": special_needs,
            "generate_visuals": False  # Standard lesson without visuals
        }

        result = workflow.invoke(initial_state)

        return jsonify({
            "success": True,
            "lesson_plan": result["lesson_plan"],
            "metadata": {
                "subject": subject,
                "grades": grades,
                "topic": topic,
                "medium": medium,
                "special_needs": special_needs,
                "resources": result["resources"],
                "lesson_plan_with_resource_mapping": result["lesson_plan_with_resource_mapping"]
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lesson_bp.route('/api/generate-visual-lesson', methods=['POST'])
def generate_visual_lesson():
    """Generate lesson plan with visual content and downloadable document"""
    try:
        data = request.get_json()
        subject = data.get('subject', '')
        grades = data.get('grades', '')
        topic = data.get('topic', '')
        medium = data.get('medium', '')
        special_needs = data.get('special_needs', 'Standard differentiation')
        user_message = data.get('message', 'Generate a lesson plan with visual materials')
        
        # Visual generation options
        include_images = data.get('include_images', True)
        image_style = data.get('image_style', 'cartoon')  # cartoon, realistic, simple
        document_format = data.get('document_format', 'docx')  # docx, pdf

        if not all([subject, grades, topic, medium]):
            return jsonify({"error": "Missing required fields"}), 400

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "lesson_plan": "",
            "subject": subject,
            "grades": grades,
            "topic": topic,
            "medium": medium,
            "special_needs": special_needs,
            "generate_visuals": True,  # Enable visual generation
            "image_style": image_style,
            "document_format": document_format,
            "visual_generation_errors": []
        }

        result = workflow.invoke(initial_state)

        # Prepare response
        response_data = {
            "success": True,
            "lesson_plan": result["lesson_plan"],
            "metadata": {
                "subject": subject,
                "grades": grades,
                "topic": topic,
                "medium": medium,
                "special_needs": special_needs,
                "visual_content_generated": bool(result.get("visual_document_path")),
                "lesson_plan_with_resource_mapping": result["lesson_plan_with_resource_mapping"],
                "resources": result["resources"]
            }
        }

        # Add visual content information if generated
        if result.get("visual_document_path"):
            document_filename = os.path.basename(result["visual_document_path"])
            response_data["visual_document"] = {
                "filename": document_filename,
                "download_url": f"/api/download-visual-lesson/{document_filename}",
                "images_generated": len(result.get("generated_images", {})),
                "sections_with_visuals": list(result.get("generated_images", {}).keys())
            }

        # Add any visual generation errors
        if result.get("visual_generation_errors"):
            response_data["visual_warnings"] = result["visual_generation_errors"]

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lesson_bp.route('/api/download-visual-lesson/<filename>', methods=['GET'])
def download_visual_lesson(filename):
    """Download the generated visual lesson document"""
    try:
        # Security check - only allow downloading from our generated files
        safe_filename = os.path.basename(filename)
        file_path = Path(safe_filename)
        
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        # Determine mimetype based on extension
        if filename.endswith('.docx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        else:
            mimetype = 'application/octet-stream'
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lesson_bp.route('/api/generate-lesson-simple', methods=['POST'])
def generate_lesson_simple():
    try:
        data = request.get_json()
        message = data.get('message', 'Generate a basic lesson plan')
        include_visuals = data.get('include_visuals', False)

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "lesson_plan": "",
            "subject": "General",
            "grades": "Mixed",
            "topic": "General Learning",
            "special_needs": "Standard differentiation",
            "generate_visuals": include_visuals
        }

        result = workflow.invoke(initial_state)

        response_data = {
            "success": True,
            "lesson_plan": result["lesson_plan"]
        }

        # Add visual document info if generated
        if include_visuals and result.get("visual_document_path"):
            document_filename = os.path.basename(result["visual_document_path"])
            response_data["visual_document"] = {
                "filename": document_filename,
                "download_url": f"/api/download-visual-lesson/{document_filename}"
            }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@lesson_bp.route('/api/lesson-templates', methods=['GET'])
def get_lesson_templates():
    """Get available lesson plan templates with visual content suggestions"""
    templates = {
        "elementary": {
            "subjects": ["Math", "Science", "English", "Social Studies"],
            "suggested_visuals": ["Activity illustrations", "Character drawings", "Step-by-step diagrams"],
            "image_style": "cartoon"
        },
        "middle_school": {
            "subjects": ["Mathematics", "Science", "Language Arts", "History", "Geography"],
            "suggested_visuals": ["Concept diagrams", "Historical illustrations", "Scientific processes"],
            "image_style": "simple"
        },
        "high_school": {
            "subjects": ["Advanced Mathematics", "Physics", "Chemistry", "Literature", "World History"],
            "suggested_visuals": ["Complex diagrams", "Timeline graphics", "Process flows"],  
            "image_style": "realistic"
        }
    }
    
    return jsonify({
        "success": True,
        "templates": templates,
        "visual_options": {
            "image_styles": ["cartoon", "simple", "realistic"],
            "document_formats": ["docx", "pdf"],
            "visual_types": ["illustrations", "diagrams", "characters", "scenes"]
        }
    })