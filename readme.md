<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Sahayak - AI Lesson Plan Generator Project

## Project Overview

An AI-powered lesson plan generator built with Flask that creates educational content with visual resources using Google's Gemini 2.5 Pro and Vertex AI image generation.

## Architecture

```
Sahayak/
├── functions/
│   ├── main.py                 # Firebase Functions entry point
│   ├── requirements.txt        # Python dependencies
│   ├── config.py              # Configuration management
│   └── app/
│       ├── __init__.py
│       ├── routes/
│       │   └── lesson.py      # Flask routes (reference)
│       ├── services/
│       │   ├── lesson_generator.py
│       │   ├── visual_document_generator.py
│       │   └── visual_workflow_nodes.py
│       ├── workflows/
│       │   └── langgraph_workflow.py
│       ├── data/
│       │   └── textbook_links.json
│       └── prompts/
│           └── generate_lesson_plan_resources.md
├── firebase.json
├── .firebaserc
└── .env
```


## Key Components

### 1. Firebase Functions Entry Point (`functions/run.py`)

```python
from app import create_app

import os
print("[DEBUG] CWD:", os.getcwd())

print("[DEBUG] calling create_app()")  # Add this to verify
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    port = int(os.environ.get('PORT', 8081))
    
    # Listen on all interfaces (0.0.0.0) not just localhost
    app.run(host='0.0.0.0', port=port, debug=True)
```


### 2. Configuration Management (`functions/config.py`)

```python
# config.py
import os
from pathlib import Path

class Config:
    # Existing configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'XXXXXXXXXXXXXXX')
    GOOGLE_CLOUD_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'XXXXXXXXXXXXX')
    
    # Flask Configuration
    # SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    @staticmethod
    def setup_google_credentials():
        """Setup Google Cloud credentials for the Flask application"""
        # Check if running in Firebase Cloud Functions environment
        if (os.getenv('FUNCTION_NAME') or 
            os.getenv('FUNCTION_TARGET') or 
            os.getenv('FUNCTIONS_EMULATOR') or
            'GAE_APPLICATION' in os.environ):
            print("✅ Running in cloud environment - using default credentials")
            return True
            
        # Only set up credentials file for local development
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            print("✅ Google Cloud credentials already configured")
            return True
        
        # Get the project root directory (where config.py is located)
        project_root = Path(__file__).parent
        credentials_file = "<project_file>.json"
        
        # Search for credentials file in common locations
        credential_paths = [
            project_root / credentials_file,                    # Same directory as config.py
            project_root.parent / credentials_file,             # Parent directory
            project_root / "credentials" / credentials_file,    # credentials folder
            project_root / "keys" / credentials_file,           # keys folder
        ]
        
        for path in credential_paths:
            if path.exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path.absolute())
                print(f"Google Cloud credentials configured: {path.absolute()}")
                return True
        
        print(f"⚠️ Google Cloud credentials file '{credentials_file}' not found")
        print("Consider using 'gcloud auth application-default login' instead")
        return False
    
    @staticmethod
    def validate_config():
        """Validate that all required configuration is present"""
        required_vars = {
            'GOOGLE_API_KEY': Config.GOOGLE_API_KEY,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        print("All required configuration variables are set")
        return True

# Initialize credentials when the config module is imported
Config.setup_google_credentials()
```


### 3. LangGraph Workflow (`functions/app/workflows/langgraph_workflow.py`)

```python
# app/workflows/langgraph_workflow.py
from langgraph.graph import StateGraph, END
from app.services.lesson_generator import (
    determine_class_type,
    generate_single_grade_lesson, 
    generate_multigrade_lesson,
    should_use_multigrade,
    AgentState
)
from app.services.visual_workflow_nodes import (
    generate_resources,
    generate_visual_content
)

def create_workflow():
    graph = StateGraph(AgentState)
    
    # Existing nodes
    graph.add_node("classifier", determine_class_type)
    graph.add_node("single_professor", generate_single_grade_lesson)
    graph.add_node("multigrade_professor", generate_multigrade_lesson)
    graph.add_node("generate_visuals", generate_visual_content)
    graph.add_node("generate_resources", generate_resources)
    
    # Set entry point
    graph.set_entry_point("classifier")
    
    # Existing conditional routing
    graph.add_conditional_edges(
        "classifier",
        should_use_multigrade,
        {
            "single_professor": "single_professor",
            "multigrade_professor": "multigrade_professor"
        }
    )

    graph.add_edge("single_professor", "generate_resources")
    graph.add_edge("multigrade_professor", "generate_resources")
    graph.add_edge("generate_resources", "generate_visuals")
    graph.add_edge("generate_visuals", END)  # This connects to the END node
    
    return graph.compile()

workflow = create_workflow()
```


### 4. Agent State Definition

```python
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    lesson_plan: str
    subject: str
    grades: str
    topic: str
    medium: str
    special_needs: str
    generate_visuals: bool
    resources: list
    lesson_plan_with_resource_mapping: str
    visual_generation_errors: list
    generated_images: dict
    visual_document_path: str
    image_style: str
    document_format: str
```


### 5. Visual Document Generator (`functions/app/services/visual_document_generator.py`)

```python
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import base64
import hashlib
import os

from google.cloud import aiplatform, storage
from docx import Document
from docx.shared import Inches
from langchain_google_genai import ChatGoogleGenerativeAI

@dataclass
class ImageRequirement:
    section: str
    description: str
    prompt: str
    image_path: Optional[str] = None

def normalize_section_key(title: str) -> str:
    """Normalize section titles for consistent key matching"""
    import re
    key = title.strip().lower()
    key = re.sub(r'[^a-z0-9]+', '_', key)
    return key.strip('_')

class VisualDocumentGenerator:
    def __init__(self, gemini_api_key: str, project_id: str, location: str = "us-central1"):
        self.gemini_api_key = gemini_api_key
        self.project_id = project_id
        self.location = location
        
        # Initialize Vertex AI for image generation
        aiplatform.init(project=project_id, location=location)
        self.prediction_client = aiplatform.gapic.PredictionServiceClient()
        self.image_endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/imagen-3.0-generate-002"
        
        # Initialize Gemini 2.5 Pro for text processing
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=gemini_api_key
        )
    
    def generate_image(self, prompt: str, section_name: str) -> Optional[str]:
        """Generate image using Vertex AI and upload to Google Cloud Storage"""
        try:
            # Vertex AI image generation
            instances = [{"prompt": prompt}]
            parameters = {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "safetyFilterLevel": "block_some",
                "personGeneration": "allow_adult"
            }
            
            response = self.prediction_client.predict(
                endpoint=self.image_endpoint,
                instances=instances,
                parameters=parameters
            )
            
            # Upload to Google Cloud Storage
            storage_client = storage.Client(project=self.project_id)
            bucket_name = "<bucket_name>"
            bucket = storage_client.bucket(bucket_name)
            
            for prediction in response.predictions:
                if "bytesBase64Encoded" in prediction:
                    image_bytes = base64.b64decode(prediction["bytesBase64Encoded"])
                    
                    import time
                    timestamp = int(time.time())
                    filename_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                    blob_name = f"lesson-images/{normalize_section_key(section_name)}_{filename_hash}_{timestamp}.png"
                    
                    blob = bucket.blob(blob_name)
                    blob.upload_from_string(image_bytes, content_type='image/png')
                    
                    public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
                    return public_url
            
            return None
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None
```


### 6. Resource Generation (`functions/app/services/visual_workflow_nodes.py`)

```python
def generate_resources(state: AgentState) -> AgentState:
    """Generate lesson resources with proper error handling"""
    # Always initialize resources to prevent KeyError
    state["resources"] = []
    state["lesson_plan_with_resource_mapping"] = state.get("lesson_plan", "")
    
    if not state.get("lesson_plan"):
        state["visual_generation_errors"] = ["No lesson plan available for resource generation"]
        return state
    
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'generate_lesson_plan_resources.md')
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            raw_prompt = f.read()

        template = Template(raw_prompt)
        rendered_prompt = template.render(lesson_plan=state.get("lesson_plan"))
        
        response = llm.invoke(rendered_prompt)
        
        # Parse JSON response
        content = response.content.strip()
        if content.startswith("```
            content = content[7:-3].strip()
            
        lesson_data = json.loads(content)
        
        state["resources"] = lesson_data.get("resource_list", [])
        state["lesson_plan_with_resource_mapping"] = lesson_data.get("lesson_plan", state.get("lesson_plan", ""))
        
    except Exception as e:
        print(f"Error generating resources: {str(e)}")
        state["visual_generation_errors"] = [f"Error generating resources: {str(e)}"]

    return state
```


### 7. Flask Routes Reference (`functions/app/routes/lesson.py`)

```python
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
        translation = data.get('translation', '')

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
            "visual_generation_errors": [],
            "translation": translation
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
                "resources": result["resources"],
                "translation": translation
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
```


## Dependencies (`functions/requirements.txt`)

```
functions-framework==3.*
google-cloud-aiplatform
google-cloud-storage
langchain-google-genai
langchain-core
python-docx
python-dotenv
jinja2
flask
```


### Environment Variables (`.env`)

```
GOOGLE_API_KEY=your_gemini_api_key_here
GCP_PROJECT_ID=<project_id>
GOOGLE_CLOUD_LOCATION=<region_name>
GEMINI_MODEL=gemini-2.5-pro
GCS_BUCKET_NAME=<bucket_name>
```


### Testing Endpoints

```
# Generate visual lesson
curl -X POST {{LOCAL_URL}}/api/generate-visual-lesson \
  -H "Content-Type: application/json" \
  -d '{"subject": "Maths", "grades": "1,2", "topic": "Reading Pictutes", "medium": "English"}'
```


## Key Features

1. **Multi-grade Lesson Planning** - Supports both single and multi-grade lesson generation
2. **Visual Content Generation** - Creates educational images using Vertex AI Imagen
3. **Resource Integration** - Generates comprehensive resource lists with detailed specifications
4. **Document Creation** - Produces downloadable Word documents with integrated visuals
5. **Google Cloud Storage** - Stores generated images with public access URLs

## Authentication \& Security

- Uses Google Cloud Application Default Credentials for Vertex AI
- API key authentication for Gemini 2.5 Pro
- CORS headers for web browser compatibility
- File security checks for downloads
- Uniform Bucket-Level Access for Google Cloud Storage


## Troubleshooting

### Common Issues

- **Billing Account Disabled**: Ensure Google Cloud billing is active
- **Uniform Bucket-Level Access**: Remove ACL operations from storage code
- **Missing Resources KeyError**: Always initialize state fields in workflow nodes
- **JSON Parsing Errors**: Handle different LLM response formats gracefully

This project demonstrates a complete AI-powered educational content generation system with modern cloud architecture and best practices for scalability and security.