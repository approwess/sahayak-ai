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
    should_generate_visuals,
    extract_visual_requirements,
    generate_visual_content
)

def create_workflow():
    graph = StateGraph(AgentState)
    
    # Existing nodes
    graph.add_node("classifier", determine_class_type)
    graph.add_node("single_professor", generate_single_grade_lesson)
    graph.add_node("multigrade_professor", generate_multigrade_lesson)
    
    # New visual generation nodes
    graph.add_node("extract_requirements", extract_visual_requirements)
    graph.add_node("generate_visuals", generate_visual_content)
    
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
    
    # Updated conditional routing for visual generation - use "__end__" instead of "END"
    graph.add_conditional_edges(
        "single_professor",
        should_generate_visuals,
        {
            "generate_visuals": "extract_requirements",
            "END": "__end__"  # Changed from "END" to "__end__"
        }
    )
    
    graph.add_conditional_edges(
        "multigrade_professor", 
        should_generate_visuals,
        {
            "generate_visuals": "extract_requirements",
            "END": "__end__"  # Changed from "END" to "__end__"
        }
    )
    
    # Visual workflow edges
    graph.add_edge("extract_requirements", "generate_visuals")
    graph.add_edge("generate_visuals", END)  # This connects to the END node
    
    return graph.compile()

workflow = create_workflow()