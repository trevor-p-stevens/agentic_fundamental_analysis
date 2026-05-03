from typing import TypedDict, Annotated, Literal
import operator
from dataclasses import dataclass, field

@dataclass
class ResearchItem:
    id:            str
    type:          Literal["text", "web"]
    priority:      int
    query:         str
    reason:        str
    source:        str        # which signal/flag triggered this
    status:        str = "pending"
    attempts:      int = 0
    hypothesis_id: str = ""

@dataclass  
class Evidence:
    type:       Literal["metric", "text", "web"]
    source:     str
    quote:      str
    confidence: float

@dataclass
class Hypothesis:
    id:            str
    statement:     str
    tests:         list[str]
    status:        str = "open"   # open | confirmed | rejected | partial
    evidence_for:  list[dict] = field(default_factory=list)
    evidence_against: list[dict] = field(default_factory=list)
    confidence:    float = 0.0

@dataclass
class LogEntry:
    node:       str
    type:       Literal["finding", "judgment", "anomaly", "hypothesis", "research"]
    content:    str
    evidence:   list[dict]
    confidence: float
    timestamp:  str

class AnalysisState(TypedDict):
    ticker:          str
    briefing_items: list[dict]    # serialized BriefingItems — replaces briefing string

    # Working state
    research_queue:  list[dict]   # serialized ResearchItems
    hypotheses:      list[dict]   # serialized Hypotheses
    iteration:       int

    # URL deduplication — persists across all iterations
    seen_urls:       list[str]

    # Append-only logs — everything the user can see
    log: Annotated[list[dict], operator.add]

    # Node outputs
    flagged_items:       list[dict]   # from briefing analysis
    retrieved_chunks:    list[dict]   # from vector DB
    web_results:         list[dict]   # from web search
    hypothesis_results:  list[dict]   # confirmed/rejected hypotheses

    # Final
    conclusion:      dict
    done:            bool