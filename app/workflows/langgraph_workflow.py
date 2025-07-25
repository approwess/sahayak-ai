from langgraph.graph import StateGraph
from app.services.lesson_generator import (determine_class_type,
    generate_single_grade_lesson, 
    generate_multigrade_lesson,
    should_use_multigrade,
    AgentState)

def create_workflow():
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("classifier", determine_class_type)
    graph.add_node("single_professor", generate_single_grade_lesson)
    graph.add_node("multigrade_professor", generate_multigrade_lesson)
    
    # Set entry point
    graph.set_entry_point("classifier")
    
    # Add conditional routing
    graph.add_conditional_edges(
        "classifier",
        should_use_multigrade,
        {
            "single_professor": "single_professor",
            "multigrade_professor": "multigrade_professor"
        }
    )
    
    # Set finish points
    graph.set_finish_point("single_professor")
    graph.set_finish_point("multigrade_professor")
    
    return graph.compile()

workflow = create_workflow()
