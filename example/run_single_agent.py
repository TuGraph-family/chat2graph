import asyncio

from app.agent.adpter.agent_adpter_factory import (
    AgentAdapterFactory,
    AgentFrameworkName,
)
from app.agent.adpter.dbgpt_agent_adapter import DBGPTAgentAdapter
from app.memory.message import AgentMessage


async def main():
    """Main function to demonstrate agent factory usage."""
    agent_adapter = await AgentAdapterFactory.create(
        agent_type=AgentFrameworkName.DBGPT
    )
    assert isinstance(agent_adapter, DBGPTAgentAdapter)

    if agent_adapter:
        message = AgentMessage(
            msg_id="1",
            sender_id="user_123",
            receiver_id="agent_456",
            status="pending",
            content="Hello, I am Alice.",
            timestamp="2024-01-01",
        )

        response = await agent_adapter.receive_message(message)
        assert response

        message = AgentMessage(
            msg_id="2",
            sender_id="agent_456",
            receiver_id="user_123",
            status="pending",
            content="What is my name?",
            timestamp="2024-01-01",
        )

        response = await agent_adapter.receive_message(message)
        assert response


if __name__ == "__main__":
    asyncio.run(main())
