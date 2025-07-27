# app/services/visual_workflow_nodes.py
from app.services.visual_document_generator import VisualDocumentGenerator
from app.services.lesson_generator import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from jinja2 import Template
import re
import os
import json

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def should_generate_visuals(state: AgentState) -> str:
    """Determine if visual document should be generated"""
    generate_visuals = state.get("generate_visuals", False)
    print(f"should_generate_visuals called: generate_visuals = {generate_visuals}")
    
    if generate_visuals:
        return "generate_visuals"
    else:
        return "END"
    
def process_lesson_plan(state: AgentState) -> str:
    base_url = "https://storage.googleapis.com/edu-resources/"
    resources = state.get("resources", [])
    for resource in resources:
        resource_type = resource.get('type')
        unique_id = resource.get('unique_id')
        
        if resource_type == 'image':
            extension = '.jpg'
        elif resource_type == 'audio':
            extension = '.wav'
        elif resource_type == 'video':
            extension = '.mp4'
        else:
            extension = '' # Default for unknown types
            
        resource['url'] = f"{base_url}{unique_id}{extension}"

    id_to_url_map = {resource['unique_id']: resource['url'] for resource in resources}
    lesson_plan_text = state.get("lesson_plan_with_resource_mapping", "")
    for unique_id, url in id_to_url_map.items():
        placeholder = f"[Resource: {unique_id}]"
        lesson_plan_text = lesson_plan_text.replace(placeholder, url)
    state['lesson_plan'] = lesson_plan_text
    return state

def generate_resources(state: AgentState) -> AgentState:
    if not state.get("lesson_plan"):
        state["visual_generation_errors"] = ["No lesson plan available for visual generation"]
        return state
    
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'generate_lesson_plan_resources.md')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            raw_prompt = f.read()

        template = Template(raw_prompt)
        rendered_prompt = template.render(
            lesson_plan=state.get("lesson_plan")
        )
        prompt = f"<pre>{rendered_prompt}</pre>"
        # print(prompt)

        response = llm.invoke(prompt)
        # print(response.content)
        # outer = json.loads(response.content)
        # inner_content_raw = outer['content']

        if response.content.startswith("```json"):
            inner_content_raw = response.content
            inner_content_raw = inner_content_raw.strip("```json").strip("```").strip()
        lesson_data = json.loads(inner_content_raw)
        # print(lesson_data)
        
        state["resources"] = lesson_data['resource_list']
        state["lesson_plan_with_resource_mapping"] = lesson_data['lesson_plan']
    except Exception as e:
        print(str(e))

    return state

def generate_content(state: AgentState) -> AgentState:
    generator = VisualDocumentGenerator(os.getenv("GOOGLE_API_KEY"),
            project_id=os.getenv("GCP_PROJECT_ID"))
    resources = generator.generate_content(state["resources"])
    state["resources"] = resources
    return state

def extract_visual_requirements(state: AgentState) -> AgentState:
    """Extract image requirements from lesson plan"""
    print("=== extract_visual_requirements function called ===")
    
    if not state.get("lesson_plan"):
        state["visual_generation_errors"] = ["No lesson plan available for visual generation"]
        return state
    
    try:
        generator = VisualDocumentGenerator(os.getenv("GOOGLE_API_KEY"),
            project_id=os.getenv("GCP_PROJECT_ID"))
        requirements = generator.extract_image_requirements(state["lesson_plan"])
        
        if not requirements:
            print("No specific requirements found, adding default educational visuals...")
            # Enhanced default requirements
            default_requirements = [
                {
                    "section": "Lesson Introduction", 
                    "description": "teacher presenting lesson to engaged students in bright classroom", 
                    "prompt": "friendly teacher showing educational materials to young students in a colorful classroom, cartoon illustration style"
                },
                {
                    "section": "Learning Activity", 
                    "description": "children participating in educational activity with visual materials", 
                    "prompt": "happy children working together with educational pictures and materials, bright colors, learning environment"
                },
                {
                    "section": "Practice Exercise", 
                    "description": "students completing practice work with visual aids", 
                    "prompt": "young students writing and using visual learning aids, educational worksheet, encouraging classroom scene"
                }
            ]
            state["image_requirements"] = default_requirements
        else:
            state["image_requirements"] = [
                {
                    "section": req.section,
                    "description": req.description,
                    "prompt": req.prompt
                }
                for req in requirements
            ]
        
        print(f"Found {len(state['image_requirements'])} image requirements")
        
    except Exception as e:
        error_msg = f"Error extracting requirements: {str(e)}"
        print(error_msg)
        state["visual_generation_errors"] = [error_msg]
        
        # Provide fallback even on error
        state["image_requirements"] = [{
            "section": "General Lesson", 
            "description": "educational classroom scene with teacher and students", 
            "prompt": "bright educational classroom with teacher and young students learning together"
        }]
    
    return state

def normalize_section_key(title):
    key = title.strip().lower()
    key = re.sub(r'[^a-z0-9]+', '_', key)
    return key.strip('_')

def generate_visual_content(state: AgentState) -> AgentState:
    """Generate images and create visual document"""
    if not state.get("image_requirements"):
        state["visual_generation_errors"] = ["No image requirements found"]
        return state
    
    try:
        generator = VisualDocumentGenerator(os.getenv("GOOGLE_API_KEY"),
            os.getenv("GCP_PROJECT_ID"))
        generated_images = {}
        
        print(f"Generating images for {len(state['image_requirements'])} requirements...")
        
        # Generate images for each requirement
        max_images = 3
        for i, req in enumerate(state["image_requirements"]):
            print(f"Generating image for: {req['section']}")
            if i >= max_images:
                break
            image_path = generator.generate_image(req["prompt"], req["section"])
            if image_path:
                # section_key = req["section"].replace(' ', '_').lower()
                section_key = normalize_section_key(req["section"])
                generated_images[section_key] = image_path
                print(f"Generated image: {image_path}")
            else:
                print(f"Failed to generate image for: {req['section']}")
        
        state["generated_images"] = generated_images
        print(generated_images)
        
        # Create visual document
        if generated_images:
            doc_path = generator.create_visual_document(
                state["lesson_plan"], 
                generated_images
            )
            state["visual_document_path"] = doc_path
            print(f"Created visual document: {doc_path}")
        
    except Exception as e:
        state["visual_generation_errors"] = [f"Error generating visuals: {str(e)}"]
        print(f"Error in generate_visual_content: {str(e)}")
    
    return state