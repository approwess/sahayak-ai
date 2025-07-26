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
    generate_resources
)

def create_workflow():
    graph = StateGraph(AgentState)
    
    # Existing nodes
    graph.add_node("classifier", determine_class_type)
    graph.add_node("single_professor", generate_single_grade_lesson)
    graph.add_node("multigrade_professor", generate_multigrade_lesson)
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
    
    # Visual workflow edges
    # graph.add_edge("extract_requirements", "generate_visuals")
    graph.add_edge("generate_resources", END)  # This connects to the END node
    
    return graph.compile()

workflow = create_workflow()