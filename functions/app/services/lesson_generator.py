from langchain_core.messages import BaseMessage
from typing import Annotated, Sequence, TypedDict, Literal
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    lesson_plan: str
    subject: str
    grades: str
    topic: str
    special_needs: str
    class_type: Literal["single", "multigrade"]

def determine_class_type(state: AgentState):
    """Determine if class is single or multigrade based on grades input"""
    grades = state.get('grades', '')
    
    # Count number of grades mentioned
    grade_count = len([g.strip() for g in grades.split(',') if g.strip()])
    
    if grade_count > 1:
        return {"class_type": "multigrade"}
    else:
        return {"class_type": "single"}

def generate_single_grade_lesson(state: AgentState):
    """Generate lesson plan for single grade"""
    last_message = state['messages'][-1].content
    
    prompt = f"""
    Act as an expert Professor Agent for single-grade classroom lesson planning.
    
    Subject: {state.get('subject', 'General')}
    Grade Level: {state.get('grades', 'Grade 1')}
    Topic: {state.get('topic', 'General Learning')}
    Special Needs: {state.get('special_needs', 'Standard differentiation')}
    
    Request: {last_message}
    
    Generate a comprehensive one-week lesson plan for a SINGLE GRADE classroom that includes:
    1. Clear, grade-appropriate learning objectives
    2. Daily activities sequenced for optimal learning
    3. Assessment strategies aligned to grade level
    4. Materials and resources needed
    5. Extension activities for advanced learners
    6. Support strategies for struggling students
    
    Focus on depth rather than differentiation across grades.
    Format as a structured, teacher-ready outline.
    """
    
    response = llm.invoke(prompt)
    return {
        "lesson_plan": response.content,
        "messages": state['messages']
    }

def generate_multigrade_lesson(state: AgentState):
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
