import os
import logging
import yaml
from pathlib import Path
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
    metrics,
    MetricsCollectedEvent,
    llm,
)

from livekit.plugins import (
    deepgram,
    openai,
    silero,
    simli,
    noise_cancellation,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Custom TTS & KB Manager
from chatterbox_plugin.chatterbox_tts import ChatterboxTTS
from kb_manager import kb_manager

# -------------------------
# ENV & LOGGING
# -------------------------
load_dotenv()
logger = logging.getLogger("digital-employee")

# -------------------------
# CONFIG & PERSONA LOADING
# -------------------------
def load_persona():
    persona_path = Path(__file__).parent / "persona.yaml"
    if not persona_path.exists():
        raise FileNotFoundError(f"CRITICAL: {persona_path} not found. Agent requires a persona configuration.")
    
    with open(persona_path, "r") as f:
        config = yaml.safe_load(f)
    
    role_key = os.getenv("AGENT_ROLE", config.get("active_role"))
    if not role_key:
        raise ValueError("AGENT_ROLE or active_role in persona.yaml must be defined.")

    role_data = config.get("roles", {}).get(role_key)
    if not role_data:
        raise ValueError(f"Role '{role_key}' not found in persona.yaml")
    
    system_guidelines = config.get("system_guidelines", "")
    
    return (
        role_data["name"],
        role_data["greeting"],
        role_data["instructions"],
        system_guidelines
    )

NAME, GREETING, INSTRUCTIONS, SYSTEM_GUIDELINES = load_persona()

# -------------------------
# TOOLS (Generic Template)
# -------------------------

@llm.function_tool
async def knowledge_lookup(query: str) -> str:
    """Search the company knowledge base for information, manuals, or media links."""
    return await kb_manager.query(query)

# --- HOW TO DEFINE A NEW TOOL ---
# To add a custom tool (e.g., for Sales or Training):
# 1. Define an async function with @llm.function_tool decorator.
# 2. Add it to the 'tools' list in the DigitalEmployee class below.
# Example:
# @llm.function_tool
# async def check_availability(product_id: str) -> str:
#     """Checks if a product is in stock."""
#     return "In stock and ready to ship!"

@llm.function_tool
async def end_call() -> str:
    """End the conversation and disconnect. Use this when the user says goodbye or the interaction is finished."""
    global _current_room
    if _current_room:
        try:
            await _current_room.disconnect()
            return "Session ended."
        except Exception:
            return "Error ending session."
    return "No active session."

# -------------------------
# AGENT CLASS
# -------------------------
_current_room = None

class DigitalEmployee(Agent):
    def __init__(self):
        super().__init__(
            instructions=f"NAME: {NAME}\n\nCORE INSTRUCTIONS:\n{INSTRUCTIONS}\n\n--- SYSTEM GUIDELINES ---\n{SYSTEM_GUIDELINES}",
            tools=[knowledge_lookup, end_call],
        )


    async def on_enter(self):
        await self.session.generate_reply(
            instructions=GREETING,
            allow_interruptions=True,
        )

# -------------------------
# SERVER & MAIN
# -------------------------
server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="surens-avatar")
async def entrypoint(ctx: JobContext):
    global _current_room
    _current_room = ctx.room

    # Avatar (Simli)
    simli_api_key = os.getenv("SIMLI_API_KEY")
    simli_face_id = os.getenv("SIMLI_FACE_ID")

    if not simli_api_key or not simli_face_id:
        logger.error("SIMLI_API_KEY or SIMLI_FACE_ID missing")
        return

    avatar = simli.AvatarSession(
        simli_config=simli.SimliConfig(api_key=simli_api_key, face_id=simli_face_id),
    )

    # Session Config
    session = AgentSession(
        stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.4),
        llm=openai.LLM(model="gpt-4.1-mini-2025-04-14"),
        tts=ChatterboxTTS(
            api_url="https://jayant--chatterbox-tts-web-app.modal.run",
            voice="anaya_en_female",
            language="en",
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    
    usage_collector = metrics.UsageCollector()
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        usage_collector.collect(ev.metrics)

    ctx.add_shutdown_callback(lambda: logger.info(f"Usage Summary: {usage_collector.get_summary()}"))

    # Connect components
    await avatar.start(session, room=ctx.room)
    await session.start(
        agent=DigitalEmployee(),
        room=ctx.room,
        record=True,
        room_options=room_io.RoomOptions(
            video_input=True,
            audio_input=room_io.AudioInputOptions(noise_cancellation=noise_cancellation.BVC()),
            delete_room_on_close=True,
        ),
    )

if __name__ == "__main__":
    cli.run_app(server)
