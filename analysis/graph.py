from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from functools import partial
from .state import AnalysisState
from .nodes.briefing  import briefing_analysis_node, hypothesis_node
from .nodes.research  import text_research_node, web_research_node
from .nodes.hypothesis import hypothesis_evaluation_node
from .nodes.synthesis  import synthesis_node
from .ingest import get_chroma_client
from typing import Literal

def should_continue(state: AnalysisState) -> Literal["research", "synthesize"]:
    """
    Decide whether to continue another research iteration or stop and synthesize.

    The workflow exits to synthesis when:
    - there are no pending research queue items,
    - the max iteration cap is reached,
    - recent confidence is very low (diminishing returns),
    - or only low-priority follow-ups remain.

    Returns:
      "research" to run another text/web research cycle,
      "synthesize" to finalize conclusions.
    """
    pending = [q for q in state["research_queue"] if q["status"] == "pending"]

    if not pending:
        return "synthesize"
    if state["iteration"] >= 6:
        return "synthesize"

    # Stop if last 6 log entries are all low confidence — diminishing returns
    recent = state["log"][-6:]
    if len(recent) >= 6:
        avg_conf = sum(
            float(l["confidence"]) if isinstance(l["confidence"], (int, float)) else 0
            for l in recent
        ) / 6
        if avg_conf < 0.25:
            return "synthesize"

    # Stop if only low-priority items remain
    if all(q["priority"] >= 4 for q in pending):
        return "synthesize"

    return "research"


def increment_iteration(state: AnalysisState) -> dict:
    """
    Increment the loop counter after each research-evaluation cycle.

    Returns a partial state update with iteration advanced by 1.
    """
    return {"iteration": state["iteration"] + 1}


def build_graph(chroma_path: str = "./chroma_db"):
    """
    Construct and compile the LangGraph analysis pipeline.

    Pipeline flow:
    briefing -> hypothesis formation -> text research -> web research
    -> hypothesis evaluation -> iteration increment -> (loop or synthesis).

    Research nodes use a module-level Chroma collection and the compiled
    graph uses an in-memory checkpointer for run state persistence.

    Args:
      chroma_path: Filesystem path to the persistent Chroma database (unused; collection is instantiated in research.py).

    Returns:
      Compiled LangGraph application ready to invoke/stream.
    """
    graph = StateGraph(AnalysisState)

    graph.add_node("briefing_analysis",      briefing_analysis_node)
    graph.add_node("hypothesis_formation",   hypothesis_node)
    graph.add_node("text_research",          text_research_node)
    graph.add_node("web_research",           web_research_node)
    graph.add_node("hypothesis_evaluation",  hypothesis_evaluation_node)
    graph.add_node("increment_iteration",    increment_iteration)
    graph.add_node("synthesis",              synthesis_node)

    # Entry
    graph.set_entry_point("briefing_analysis")

    # Linear start
    graph.add_edge("briefing_analysis",    "hypothesis_formation")
    graph.add_edge("hypothesis_formation", "text_research")
    graph.add_edge("text_research",        "web_research")
    graph.add_edge("web_research",         "hypothesis_evaluation")
    graph.add_edge("hypothesis_evaluation","increment_iteration")

    # Loop or exit
    graph.add_conditional_edges(
        "increment_iteration",
        should_continue,
        {
            "research":   "text_research",   # loop back
            "synthesize": "synthesis",
        }
    )

    graph.add_edge("synthesis", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)