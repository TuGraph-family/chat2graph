from memfuse.llm import OpenAI
from memfuse import MemFuse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Initialize MemFuse with a user context
memfuse = MemFuse()
memory = memfuse.init(user="alice")

# Create OpenAI client with memory
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    memory=memory
)

# Display memory information
print(f"Using memory for conversation: {memory}")

# --- OpenAI Example ---
print("\n--- OpenAI Example ---")
response = client.chat.completions.create(
    model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-5-mini"),
    messages=[{"role": "user", "content": "I'm working on a project about space exploration. Can you tell me something interesting about Mars?"}],
)

print(response.choices[0].message.content)

# Test follow-up to verify memory is working
print("\n--- OpenAI Follow-up Question ---")
followup_response = client.chat.completions.create(
    model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-5-nano"),
    messages=[{"role": "user", "content": "What would be the biggest challenges for humans living on that planet?"}],
)

print(followup_response.choices[0].message.content)
