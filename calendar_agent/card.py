from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from a2a.utils import TransportProtocol


AGENT_ID = "22222222-2222-2222-2222-222222222222"

BOOK_SKILLS = AgentSkill(
    id="book_interview",
    name="Book interview",
    description=(
        "I am booking interviews with candidates for available slots. "
        "I use the candidate ID to search the database. "
        "I don't look for candidates. "
        "I don't talk to candidates. "
        "I don't write to candidates. "
        "I return a message (like page) telling me whether the slot was booked successfully. "
    ),
    tags=["calendar", "book", "interviews", "scheduling"],
    examples=[
        "book an interview for candidate cf7ca699 on 2026-08-15 at 14:00",
        "schedule a meeting with candidate X tomorrow at 10am",
    ],
)

AGENT_CARD = AgentCard(
    name="Calendar",
    description="Calendar agent who books candidate slots",
    version="0.1.0",
    supported_interfaces=[
        AgentInterface(
            url="http://localhost:10000/", protocol_binding=TransportProtocol.JSONRPC
        )
    ],
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[BOOK_SKILLS],
)
