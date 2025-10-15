import pytest
from karigar.agents.intake_agent import IntakeAgent
from karigar.memory.sql_memory import init_db


def test_intake_agent_extracts_bricks_without_llm():
    init_db()
    agent = IntakeAgent(llm=None)
    state = {
        "messages": [{"role": "user", "content": "I need 50 bricks in Mumbai"}],
        "status": "new"
    }

    result = agent.process(state)

    assert result["status"] == "intake_complete"
    material_request = result["material_request"]
    assert material_request["material"] == "bricks"
    assert material_request["quantity"] == 50.0
    assert material_request["location"].lower() == "mumbai"