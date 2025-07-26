from langchain_core.messages import BaseMessage
from typing import Annotated, Sequence, TypedDict, Literal
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from app.services.resource_finder import ResourceFinder
from typing import TypedDict, Optional, List, Dict
from jinja2 import Template
import os

load_dotenv()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    lesson_plan: str
    subject: str
    grades: str
    topic: str
    medium: str
    special_needs: str
    class_type: Literal["single", "multigrade"]
    lesson_plan: Optional[str]

    generate_visuals: Optional[bool]
    image_requirements: Optional[List[Dict]]
    generated_images: Optional[Dict[str, str]]
    visual_document_path: Optional[str]
    visual_generation_errors: Optional[List[str]]
    image_style: Optional[str]
    document_format: Optional[str]

def determine_class_type(state: AgentState):
    """Determine if class is single or multigrade based on grades input"""
    grades = state.get('grades', '')
    
    # Count number of grades mentioned
    grade_count = len([g.strip() for g in grades.split(',') if g.strip()])
    
    if grade_count > 1:
        return {"class_type": "multigrade"}
    else:
        return {"class_type": "single"}

def generate_multigrade_lesson(state: AgentState):
    """Generate lesson plan for multiple grade"""
    # last_message = state['messages'][-1].content

    grades = state.get('grades', '1')
    medium = state.get('medium', 'Hindi')  # Add medium to your AgentState
    topic = state.get('topic', 'General Learning')
    subject = state.get('subject', 'General')
    grade_list = [g.strip() for g in grades.split(",") if g.strip()]

    resource_finder = ResourceFinder()

    matching_resources = resource_finder.find_links_by_criteria(
        grades=grades,
        medium=medium,
        subject=subject,
        topic=topic
    )

    print(f"🔍 Found {len(matching_resources)} matching resources for:")

    resources_text = ""
    if matching_resources:
        resources_text = "\n\nRelevant Educational Resources:\n"
        for resource in matching_resources:
            resources_text += f"For Grade {resource['grade']} - {resource['medium']} medium chapters use this link for balbharti textbook {resource['link']} \n"
            # for link in resource['links']:
            #     resources_text += f"  • {link['title']}: {link['url']} ({link['type']})\n"
    prompt = ""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'multigrade_lesson_prompt.md')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            raw_prompt = f.read()

        template = Template(raw_prompt)
        rendered_prompt = template.render(
            grades=grade_list,
            subject=subject,
            topic=topic,
            medium=medium,
            resources_text=resources_text,
            learning_levels=[]
        )
        prompt = f"<pre>{rendered_prompt}</pre>"

        # print("prompt" + prompt)
    except Exception as e:
        print("error" + str(e))
    
    response = llm.invoke(prompt)
    return {
        "lesson_plan": response.content,
        "messages": state['messages']
    }

def generate_single_grade_lesson(state: AgentState):
    """Generate lesson plan for multigrade classroom"""
    last_message = state['messages'][-1].content
    
    prompt = f"""
    Act as an expert Professor Agent for multigrade classroom lesson planning.
    
    Subject: {state.get('subject', 'General')}
    Grade Levels: {state.get('grades', 'Mixed grades')}
    Topic: {state.get('topic', 'General Learning')}
    Special Needs: {state.get('special_needs', 'Standard differentiation')}
    
    Request: {last_message}
    
    Generate a comprehensive one-week lesson plan for a MULTIGRADE classroom that includes:
    1. Tiered learning objectives for each grade level
    2. Flexible grouping strategies (same-grade, mixed-grade, ability-based)
    3. Differentiated daily activities with multiple entry points
    4. Scaffolded assessments appropriate for each grade
    5. Materials that can be adapted across grade levels
    6. Independent work stations for different abilities
    7. Peer tutoring and collaboration opportunities
    8. Management strategies for teaching multiple grades simultaneously
    
    Emphasize differentiation, flexible grouping, and efficient classroom management.
    Format as a structured, teacher-ready outline with clear grade-specific sections.
    """
    
    response = llm.invoke(prompt)
    return {
        "lesson_plan": response.content,
        "messages": state['messages']
    }

# Route condition function
def should_use_multigrade(state: AgentState) -> str:
    """Determine which path to take based on class type"""
    if state.get("class_type") == "multigrade":
        return "multigrade_professor"
    else:
        return "single_professor"
