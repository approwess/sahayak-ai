from .lesson import lesson_bp
from .combined_assessment_routes import combined_assessment_bp

def register_blueprints(app):
    app.register_blueprint(lesson_bp)
    app.register_blueprint(combined_assessment_bp)