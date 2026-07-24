from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils import TransportProtocol

AGENT_ID = "11111111-1111-1111-1111-111111111111"

SEARCH_SKILL = AgentSkill(
    id="search_candidates",
    name="Candidate search",
    description=(
        "I search the database for candidates based on technical skills—"
        "including those with at least one match. "
        "I rank them by number of matches, and if there are ties, by experience. "
        "I don't schedule calls, contact candidates, or book calendar appointments. "
        "I return a sorted list; empty if there are no matches."
    ),
    tags=["hr", "recruiting", "search"],
    examples=[
        "find 3 python developers with kubernetes experience",
        "find people who know Go and Java",
        "i need a DevOps engineer with Docker experience",
    ],
)

AGENT_CARD = AgentCard(
    name="HR Recruiter",
    description="HR agent that finds candidates in the company database.",
    version="0.1.0",
    supported_interfaces=[
        AgentInterface(
            url="http://localhost:9999/", protocol_binding=TransportProtocol.JSONRPC
        )
    ],
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[SEARCH_SKILL],
)
