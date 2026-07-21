from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils import TransportProtocol

ORCHESTRATE_SKILL = AgentSkill(
    id="orchestrate",
    name="Orchestrator",
    description=(
        "I accept a complex task, decompose it, delegate it to specialized agents, and return the result. "
        "I dont do the work myself - I conduct it."
    ),
    tags=["orchestrator", "conduct", "decompose"],
    examples=[
        "find a python developer with sql and book an interview for 2026-09-01 at 15:00",
        "find a candidate skilled in react and schedule a call next Monday at noon",
        "search for a devops engineer and set up an interview",
    ],
)

ORCHESTRATOR_CARD = AgentCard(
    name="Orchestrate recruiting workflow",
    description="I accept a complex task, decompose it, delegate it to specialized agents, and return the result.",
    version="0.1.0",
    supported_interfaces=[
        AgentInterface(
            url="http://localhost:11000/", protocol_binding=TransportProtocol.JSONRPC
        )
    ],
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[ORCHESTRATE_SKILL],
)
