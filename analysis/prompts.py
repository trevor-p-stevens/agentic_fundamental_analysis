SYSTEM_PROMPT = """
You are a senior financial analyst conducting deep fundamental analysis.
You reason step by step. You never assert without evidence.
You distinguish clearly between what data shows vs what you infer.
Always return valid JSON when asked.
"""

BRIEFING_FLAG_PROMPT = """
You are reading a financial briefing for {ticker}.

Your job in this step is to READ and FLAG — not conclude.

Work through the briefing in this order:

1. CRITICAL FLAGS — for each one:
   - What is the most likely explanation given other metrics in the briefing?
   - What confirms or challenges it within the briefing itself?
   - Does it connect to any narrative signal or contradiction flag?

2. CONTRADICTION FLAGS — for each one:
   - Which specific metrics are in conflict?
   - What are the 2-3 most plausible explanations?

3. CROSS-METRIC NARRATIVE SIGNALS — for each one:
   - Does the metric data support or contradict it?
   - Does it conflict with other narrative signals?

4. CATEGORY BY CATEGORY — income statement, cash flow, balance sheet, efficiency:
   - What is the overall story?
   - Which metrics are most significant?
   - What do you not understand or cannot explain from numbers alone?

For everything you cannot explain from the briefing alone, add it to research_queue.

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "findings": [
        {{
            "type": "critical_flag | contradiction | narrative | metric",
            "subject": "what you are analyzing",
            "observation": "what you see",
            "likely_explanation": "your best explanation",
            "confidence": "HIGH | MEDIUM | LOW",
            "evidence": [{{"source": "metric name or signal", "quote": "specific value or signal"}}],
            "needs_research": true/false,
            "research_query": "specific question if needs_research is true",
            "research_type": "text | web"
        }}
    ],
    "research_queue": [
        {{
            "id": "rq_0",
            "type": "text | web",
            "priority": 1,
            "query": "specific search query",
            "reason": "why this needs research",
            "source": "which flag or signal triggered this"
        }}
    ]
}}

BRIEFING:
{briefing}
"""

HYPOTHESIS_PROMPT = """
You have these unresolved findings from briefing analysis:
{findings}

And these items in the research queue:
{queue}

Form testable hypotheses for the most important unresolved questions.
Group related research items under one hypothesis where possible.

RETURN VALID JSON ONLY. NO PROSE. NO MARKDOWN. NO BULLET POINTS.

Return JSON:
{{
    "hypotheses": [
        {{
            "id": "h_0",
            "statement": "specific falsifiable hypothesis",
            "tests": [
                "what to look for in filing text",
                "what to search on the web",
                "what metric to check"
            ],
            "priority": 1,
            "related_queue_ids": ["rq_0", "rq_1"]
        }}
    ]
}}
"""

TEXT_RESEARCH_PROMPT = """
You are investigating the following for {ticker}:

Hypothesis / Question: {question}
Reason: {reason}

Retrieved filing sections:
{chunks}

Tasks:
1. Extract specific evidence — quote the exact relevant text
2. Synthesize: What is the key finding from this filing text?
3. Does this confirm, reject, or leave open the hypothesis?
4. What is your confidence? 0.0 - 1.0
5. Does this raise new questions needing web research?

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "answer": "direct answer to the question",
    "finding": "what you learned from the filing, in analytical terms",
    "implication": "why this matters for the hypothesis or business analysis",
    "evidence": [
        {{
            "quote": "exact text from filing",
            "section": "which filing section",
            "implication": "what this means"
        }}
    ],
    "hypothesis_update": "confirms | rejects | partial | inconclusive",
    "confidence": 0.0,
    "new_web_queries": ["specific query if needed"]
}}
"""

WEB_RESEARCH_PROMPT = """
You are researching {ticker} to investigate:

Question: {question}
Context from filings: {context}

Web search results:
{results}

Tasks:
1. What does the web research reveal about this question?
2. Does it confirm or contradict filing disclosures?
3. What is the quality of sources? (SEC/transcript > analyst > news > blog)
4. Confidence in this finding: 0.0 - 1.0
5. Any follow-up needed?

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "answer": "direct answer to the question",
    "finding": "what you learned from the filing, in analytical terms",
    "implication": "why this matters for the hypothesis or business analysis",
    "confirms_filing": true/false/null,
    "source_quality": "HIGH | MEDIUM | LOW",
    "evidence": [
        {{
            "source": "url or publication",
            "quote": "relevant excerpt",
            "confidence": 0.0
        }}
    ],
    "confidence": 0.0,
    "follow_up_queries": []
}}
"""

HYPOTHESIS_TEST_PROMPT = """
You have gathered evidence for this hypothesis:

Hypothesis: {statement}

Evidence FOR:
{evidence_for}

Evidence AGAINST:
{evidence_against}

All findings related to this hypothesis:
{related_findings}

Based on all evidence:
1. Is this hypothesis confirmed, rejected, partially supported, or inconclusive?
2. What is your confidence? 0.0 - 1.0
3. What is the implication for the business if confirmed?
4. What remains unresolved?

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "status": "confirmed | rejected | partial | inconclusive",
    "confidence": 0.0,
    "conclusion": "clear statement of what you concluded",
    "implication": "what this means for the business",
    "unresolved": "what still needs answering"
}}
"""

SYNTHESIS_PROMPT = """
You have completed iterative research on {ticker}.

All logged findings and judgments:
{log}

Confirmed hypotheses:
{confirmed}

Rejected hypotheses:
{rejected}

Partial / inconclusive:
{partial}

Now synthesize everything into a final analysis:

1. OVERALL BUSINESS QUALITY ASSESSMENT
   - What does the data say about business quality?
   - What are the 3 biggest risks?
   - What are the 3 biggest strengths?

2. EARNINGS QUALITY
   - Is reported income trustworthy?
   - Key flags for or against earnings quality

3. CAPITAL ALLOCATION
   - How is management deploying capital?
   - Is it value-creating or value-destroying?

4. TRAJECTORY
   - Is the business improving, deteriorating, or stable?
   - What are leading indicators to watch?

5. WHAT REQUIRES USER JUDGMENT
   - List specific decisions that are genuinely ambiguous
   - Provide the evidence on both sides for each

6. FINAL CONFIDENCE
   - Overall confidence in this analysis: 0.0 - 1.0
   - Key risks to the analysis being wrong

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "business_quality": {{
        "assessment": "...",
        "risks": ["...", "...", "..."],
        "strengths": ["...", "...", "..."]
    }},
    "earnings_quality": {{
        "assessment": "...",
        "flags": []
    }},
    "capital_allocation": {{
        "assessment": "...",
        "details": "..."
    }},
    "trajectory": {{
        "direction": "improving | deteriorating | stable | mixed",
        "assessment": "...",
        "leading_indicators": []
    }},
    "user_decisions_needed": [
        {{
            "question": "...",
            "evidence_for": "...",
            "evidence_against": "..."
        }}
    ],
    "overall_confidence": 0.0,
    "confidence_risks": []
}}
"""

ITEM_ANALYSIS_PROMPT = """
You are analyzing one specific item from a financial briefing for {ticker}.

Item type: {category}
Subject: {subject}
Definition: {definition}

Data:
{data}

Previously seen context (for cross-referencing):
{prior_context}

For this specific item:
1. What does this signal or metric tell you about the business?
2. Is it concerning, positive, or neutral? Why?
3. Does it connect to or conflict with anything in prior context?
4. Can you explain it from what you know, or does it need research?
5. If it needs research: what exactly needs to be looked up and where?

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "item_id": "{item_id}",
    "observation": "what you see",
    "implication": "what it means for the business",
    "cross_references": ["any prior items this connects to"],
    "sentiment": "bullish | bearish | neutral | ambiguous",
    "needs_research": true/false,
    "confidence": "HIGH | MEDIUM | LOW",
    "research_items": [
        {{
            "type": "text | web",
            "priority": 1,
            "query": "specific query",
            "reason": "why"
        }}
    ]
}}
"""

WEB_CHUNK_PROMPT = """
You are investigating one specific source for {ticker}.

Question being researched: {question}
Hypothesis being tested: {hypothesis}

Source: {source_url}
Source quality rank: {source_rank} (1.0 = SEC filing, 0.2 = blog)

Relevant excerpts retrieved from this source:
{chunks}

Based ONLY on these excerpts from this source:
1. What does this source reveal about the question?
2. Does it confirm, reject, or leave open the hypothesis?
3. How credible is this finding given the source rank?
4. Confidence this source meaningfully addresses the question: 0.0 - 1.0

Return only valid JSON. No prose. No markdown. No bullet points:
{{
    "finding": "what this source reveals",
    "hypothesis_update": "confirms | rejects | partial | inconclusive",
    "credibility_note": "why you trust or discount this source",
    "evidence": [
        {{
            "quote": "exact relevant excerpt",
            "implication": "what it means"
        }}
    ],
    "confidence": 0.0
}}
"""