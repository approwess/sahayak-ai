from flask import Blueprint, request, jsonify
from datetime import datetime
import os

# Import your assessment services (you'll need to create these files)
try:
    from app.services.combined_assessment import CombinedAssessmentGenerator
    combined_generator = CombinedAssessmentGenerator()
except ImportError as e:
    print(f"[WARNING] Could not import CombinedAssessmentGenerator: {e}")
    combined_generator = None

combined_assessment_bp = Blueprint('combined_assessment', __name__)

@combined_assessment_bp.route('/api/assessment/questionnaire/std1-2', methods=['POST'])
def create_questionnaire_std1_2():
    """Generate complete assessment questionnaire for Std 1-2"""
    if not combined_generator:
        return jsonify({
            "success": False,
            "error": "Assessment generator not available. Check your Google API key and dependencies."
        }), 500
        
    try:
        data = request.get_json()
        language = data.get('language', 'Hindi')
        student_name = data.get('student_name', '')
        class_section = data.get('class_section', '')
        
        # Check if Google API key is available
        if not os.getenv("GOOGLE_API_KEY"):
            return jsonify({
                "success": False,
                "error": "Google API key not configured"
            }), 500
        
        questionnaire = combined_generator.create_assessment_questionnaire_std1_2(
            language, student_name, class_section
        )
        
        if questionnaire:
            questionnaire['assessment_info']['generated_at'] = datetime.now().isoformat()
            
            return jsonify({
                "success": True,
                "questionnaire": questionnaire,
                "grade_level": "1-2",
                "metadata": {
                    "language": language,
                    "total_sections": len(questionnaire.get("sections", [])),
                    "estimated_time": "45-60 minutes"
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate questionnaire"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@combined_assessment_bp.route('/api/assessment/health', methods=['GET'])
def assessment_health():
    """Health check for assessment service"""
    return jsonify({
        "service": "Combined Assessment API",
        "status": "healthy" if combined_generator else "degraded",
        "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "timestamp": datetime.now().isoformat()
    })