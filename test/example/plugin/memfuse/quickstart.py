import os

from dotenv import load_dotenv
from memfuse import MemFuse  # type: ignore
from memfuse.llm import OpenAI  # type: ignore

load_dotenv(override=True)

# initialize memfuse with a user context
memfuse = MemFuse()
memory = memfuse.init(user="alice")

# create openai client with memory
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    memory=memory
)

# display memory information
print(f"Using memory for conversation: {memory}")

# --- OpenAI Example ---
print("\n--- OpenAI Example ---")
response = client.chat.completions.create(
    model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-5-mini"),
    messages=[{"role": "user", "content": "I'm working on a project about space exploration. Can you tell me something interesting about Mars?"}],  # noqa: E501
)

print(response.choices[0].message.content)

# test follow-up to verify memory is working
print("\n--- OpenAI Follow-up Question ---")
followup_response = client.chat.completions.create(
    model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-5-nano"),
    messages=[
        {
            "role": "user",
            "content": "What would be the biggest challenges for humans living on that planet?",
        }
    ],  # noqa: E501
)

print(followup_response.choices[0].message.content)
