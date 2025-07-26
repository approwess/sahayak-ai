# app/services/visual_workflow_nodes.py
from app.services.visual_document_generator import VisualDocumentGenerator
from app.services.lesson_generator import AgentState
from dotenv import load_dotenv
import re
import os

load_dotenv()

def should_generate_visuals(state: AgentState) -> str:
    """Determine if visual document should be generated"""
    generate_visuals = state.get("generate_visuals", False)
    print(f"should_generate_visuals called: generate_visuals = {generate_visuals}")
    
    if generate_visuals:
        return "generate_visuals"
    else:
        return "END"

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