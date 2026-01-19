# Voice AI Agent

The backend Python agent that powers the voice AI assistant.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Add knowledge base documents
# Put files in kb_data/ folder

# 4. Ingest documents
python KB_pipeline/ingest.py

# 5. Run agent
python agent.py start
```

## Folder Structure

```
Agent/
├── agent.py              # Main agent logic & tools
├── persona.yaml          # Agent personality & roles
├── requirements.txt      # Python dependencies
│
├── KB_pipeline/          # 🧠 Knowledge Base System
│   ├── kb_manager.py     # Core RAG logic
│   ├── ingest.py         # Ingestion CLI
│   ├── test_kb.py        # Testing CLI
│   ├── kb_data/          # YOUR DOCUMENTS (put files here)
│   ├── kb_store/         # Auto-generated index
│   └── README.md         # Full Manual
│
├── chatterbox_plugin/    # Custom TTS plugin
└── docs/                 # General docs
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys (OPENAI_API_KEY, LIVEKIT_*, etc.) |
| `persona.yaml` | Agent name, greeting, instructions, roles |
| `livekit.toml` | LiveKit connection settings |

## CLI Tools

```bash
# Ingest documents
python KB_pipeline/ingest.py

# Force re-ingest
python KB_pipeline/ingest.py --force

# View KB stats
python KB_pipeline/ingest.py --stats

# Test a query
python KB_pipeline/test_kb.py "your question"

# Interactive testing
python KB_pipeline/test_kb.py
```

## Agent Tools

The agent has these built-in tools:

| Tool | Purpose |
|------|---------|
| `knowledge_lookup` | Search KB for answers |
| `show_overlay` | Display UI card to user |
| `hide_overlay` | Dismiss UI card |
| `end_call` | End the conversation |

## Adding Custom Tools

```python
# In agent.py

@llm.function_tool
async def my_custom_tool(param: str) -> str:
    """Tool description for the LLM."""
    # Your logic here
    return "Result"

# Add to DigitalEmployee class:
class DigitalEmployee(Agent):
    def __init__(self):
        super().__init__(
            instructions=...,
            tools=[knowledge_lookup, my_custom_tool, ...]  # Add here
        )
```

## Customizing the Agent

### Change Personality
Edit `persona.yaml`:
```yaml
roles:
  your_role:
    name: "Agent Name"
    greeting: "Hello! How can I help?"
    instructions: |
      Your detailed instructions here...
```

### Add New Role
1. Add role in `persona.yaml`
2. Set `active_role: your_role` or use env `AGENT_ROLE=your_role`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `LIVEKIT_URL` | ✅ | LiveKit server URL |
| `LIVEKIT_API_KEY` | ✅ | LiveKit API key |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit API secret |
| `SIMLI_API_KEY` | Optional | For avatar video |
| `DEEPGRAM_API_KEY` | Optional | For speech-to-text |
| `AGENT_ROLE` | Optional | Override active role |

## Running in Production

```bash
# Development
python agent.py dev

# Production (with Docker)
docker build -t voice-agent .
docker run -d --env-file .env voice-agent
```
