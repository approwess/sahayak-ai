from langchain_core.messages import BaseMessage
from typing import Annotated, Sequence, TypedDict, Literal
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from app.services.resource_finder import ResourceFinder
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
    
    prompt = f"""
    I am a teacher handling a multigrade classroom. Please generate a structured, integrated lesson plan based on the following inputs:

    Core Input:

    Grades: {grades}

    Chapter: {topic}

    Subject: {subject}

    Board: {state.get('board', 'Maharashtra State Board')}

    Medium: {medium}

    Student Learning Levels: {state.get('learning_levels', [])}

    Instructions for Lesson Plan Generation:

    1. Determine Paired Grade-Level Topics from Official Textbooks:

    * First, analyze the core concept of the provided Starting Grade & Topic.
    * Based on the Starting Grade, find the corresponding chapter titles for the other grade(s) from the official textbook index (e.g., 'Balbharati Mathematics textbook index'). The pairing will follow this logic:
    * If a Grade 1 topic is provided, find the progressive skill in the Grade 2 textbook.
    * If a Grade 2 topic is provided, find the foundational skill in the Grade 1 textbook.
    * If a Grade 3 topic is provided, find the progressive skills in BOTH the Grade 4 and Grade 5 textbooks.
    * If a Grade 4 topic is provided, find the related skills in BOTH the Grade 3 and Grade 5 textbooks.
    * If a Grade 5 topic is provided, find the related skills in BOTH the Grade 3 and Grade 4 textbooks.
    * You must use the exact chapter titles from the textbook index for all topics.

    {resources_text}

    2. Identify a Common Theme: Based on the paired topics (two or three grades), identify a single, unifying theme for the lesson.

    3. Create Differentiated Objectives: Write separate, clear learning objectives for what students in each grade level should be able to do by the end of the lesson.

    4. Structure the Lesson Procedure (40 minutes): The plan must follow this specific four-part structure:

    * Combined Hook: An initial activity that engages all grades together under the common theme.

    * Shared Introduction: A core teaching segment that introduces the concepts sequentially, building from the simplest to the most complex.

    * Differentiated Group Activities: Design distinct activities for each grade level.

    * Shared Wrap-up and Evaluation: A concluding activity to quickly assess all grades on their respective objectives.

    5. Keep it Practical: Ensure the materials needed are simple and the activities are suitable for a standard classroom environment.

    6. Differentiated Targeted Activities (Mandatory):

    * Based on the provided student learning levels, design distinct 10-minute activities for Beginner, Intermediate, and Advanced groups.

    * Key Principle: For the Beginner group, ensure activities teach one concept at a time. For the Advanced group, the activity should challenge them to combine concepts creatively
    """

    print(prompt)
    
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
