import os
import json
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
    get_job_context,
)

from livekit.plugins import (
    deepgram,
    openai,
    silero,
    simli,
    cartesia,
    noise_cancellation,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel

# KB Manager
from KB_pipeline.kb_search import kb_searcher as kb_manager

# -------------------------
# ENV & LOGGING
# -------------------------
load_dotenv()
logger = logging.getLogger("thermopads-supervisor")

# -------------------------
# CONFIG & PERSONA LOADING
# -------------------------
def load_persona():
    persona_path = Path(__file__).parent / "persona.yaml"
    if not persona_path.exists():
        raise FileNotFoundError(f"CRITICAL: {persona_path} not found. Agent requires a persona configuration.")
    
    with open(persona_path, "r", encoding="utf-8") as f:
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
# SESSION CONTEXT
# -------------------------
_session_context = {
    "machine_id": None,
    "product_variant": None,
    "compound_type": None,
}

# -------------------------
# OVERLAY HELPER FUNCTIONS
# -------------------------

async def send_overlay(layout_type: str, title: str, data: dict, context: str = "", source: str = ""):
    """Helper function to send overlay to frontend"""
    try:
        room = get_job_context().room
        participant_identity = next(iter(room.remote_participants.keys()), None)
        
        if not participant_identity:
            logger.warning("No participant connected for overlay display")
            return False
        
        payload = json.dumps({
            "layoutType": layout_type,
            "title": title,
            "context": context,
            "source": source,
            "data": data
        })
        
        await room.local_participant.perform_rpc(
            destination_identity=participant_identity,
            method="showOverlay",
            payload=payload,
            response_timeout=5.0,
        )
        
        logger.info(f"Overlay sent: {layout_type} - {title}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send overlay: {e}")
        return False

# -------------------------
# KNOWLEDGE BASE TOOL
# -------------------------

@llm.function_tool
async def knowledge_lookup(
    query: str,
    context_type: str = "general"
) -> str:
    """
    Search the Thermopads manufacturing knowledge base for technical information.
    
    Use this tool to find:
    - Temperature settings and profiles (TPL/TD/28 series)
    - Die and nozzle specifications (DDR Chart-3)
    - Work instructions and procedures (TPL/WI/P/15)
    - Quality control standards and tolerances
    - Safety protocols and requirements
    - Material specifications and properties
    - Troubleshooting guides
    
    Args:
        query: The technical question or topic to search for. Be specific.
               Examples: "ETFE temperature zones for ROSENDAHL TPL/M/60",
                        "Die selection for 0.35mm wire 0.32mm coating",
                        "Strip force adjustment procedure"
        context_type: Type of information needed. Options:
                     - "temperature": Temperature settings and zones
                     - "tooling": Die, nozzle, tooling specifications
                     - "procedure": Work instructions, setup steps
                     - "quality": Quality specs, tolerances, measurements
                     - "safety": Safety protocols, limits, PPE requirements
                     - "troubleshooting": Problem diagnosis and solutions
                     - "general": General search (default)
    
    Returns:
        Relevant technical information with document citations.
    """
    try:
        enhanced_query = f"[{context_type}] {query}" if context_type != "general" else query
        
        result = await kb_manager.query(enhanced_query, include_images=False)
        
        if not result.text:
            return f"No information found for query: {query}. Please rephrase or ask for related information."
        
        response = result.text
        if result.sources:
            sources_str = ", ".join(result.sources[:3])
            response += f"\n\nReference: {sources_str}"
        
        return response
        
    except Exception as e:
        logger.error(f"Knowledge lookup error: {e}")
        return f"Error searching knowledge base: {str(e)}"

# -------------------------
# SESSION CONTEXT TOOL
# -------------------------

@llm.function_tool
async def set_machine_context(
    machine_id: str,
    product_variant: str = "",
    compound_type: str = ""
) -> str:
    """
    Store machine and product context for the session.
    Use this when operator mentions their machine, product, or compound.
    
    Args:
        machine_id: Machine identifier (e.g., "Machine 3", "Rosendahl Line 1")
        product_variant: Product variant being produced (e.g., "25mm heating cable")
        compound_type: Compound being used (e.g., "ETFE", "PFA", "PA11")
    
    Returns:
        Confirmation of stored context
    """
    global _session_context
    _session_context["machine_id"] = machine_id
    if product_variant:
        _session_context["product_variant"] = product_variant
    if compound_type:
        _session_context["compound_type"] = compound_type
    
    response = f"Context set: Machine {machine_id}"
    if product_variant:
        response += f", variant {product_variant}"
    if compound_type:
        response += f", compound {compound_type}"
    
    logger.info(f"Session context updated: {_session_context}")
    return response

# -------------------------
# THERMOPADS OVERLAY TOOLS
# -------------------------

@llm.function_tool
async def show_ddr_table(
    wire_size: str,
    die_id: str,
    nozzle_od: str,
    nozzle_id: str,
    thickness: str,
    source_doc: str = "Chart-3"
) -> str:
    """
    Display the DDR table with the matching row highlighted.
    Use this for die/nozzle/wire size queries - this is the Trust Moment visual.
    The data comes from knowledge_lookup - call that first to get the values.
    
    Args:
        wire_size: Wire size range (e.g., "0.3-0.35")
        die_id: Die ID value from KB (e.g., "9 or 10")
        nozzle_od: Nozzle outer diameter from KB (e.g., "4.5")
        nozzle_id: Nozzle inner diameter from KB (e.g., "0.8 or 1")
        thickness: Insulation thickness from KB (e.g., "0.32")
        source_doc: Source document reference
    
    Returns:
        Confirmation message
    """
    try:
        # Display the specific values retrieved from KB
        data = {
            "columns": ["Parameter", "Value"],
            "rows": [
                {"Parameter": "Wire Size", "Value": wire_size},
                {"Parameter": "Die ID", "Value": die_id},
                {"Parameter": "Nozzle OD", "Value": nozzle_od},
                {"Parameter": "Nozzle ID", "Value": nozzle_id},
                {"Parameter": "Thickness", "Value": f"{thickness} mm"},
            ],
            "analysis": f"DDR settings for wire size {wire_size}mm as per {source_doc}"
        }
        
        success = await send_overlay(
            layout_type="comparison-table",
            title="DDR Settings from Chart-3",
            data=data,
            context=f"Wire Size: {wire_size}mm",
            source=f"{source_doc}, Issue/Rev 03/005"
        )
        
        if success:
            return f"DDR table displayed. For wire size {wire_size}, use Die ID {die_id}, Nozzle OD {nozzle_od}, Nozzle ID {nozzle_id}, thickness {thickness}mm."
        else:
            return f"Failed to show table. For wire size {wire_size}, use Die ID {die_id}, Nozzle OD {nozzle_od}, Nozzle ID {nozzle_id}, thickness {thickness}mm as per Chart-3."
        
    except Exception as e:
        logger.error(f"DDR table overlay error: {e}")
        return f"Error displaying DDR table: {str(e)}"


@llm.function_tool
async def show_temperature_profile(
    compound: str,
    z1_temp: str,
    z2_temp: str,
    z3_temp: str,
    z4_temp: str,
    die_temp: str,
    water_temp: str = "40",
    tolerance: str = "plus or minus 20 degrees Celsius",
    source_doc: str = "TPL/TD/28"
) -> str:
    """
    Display temperature profile with all zones for a specific compound.
    Use this when operator asks about temperature settings for a material.
    The temperature values should come from knowledge_lookup first.
    
    Args:
        compound: Compound type (e.g., "PFA", "ETFE", "PA11")
        z1_temp: Zone 1 temperature from KB (e.g., "320")
        z2_temp: Zone 2 temperature from KB (e.g., "350")
        z3_temp: Zone 3 temperature from KB (e.g., "365")
        z4_temp: Zone 4 temperature from KB (e.g., "370")
        die_temp: Die temperature from KB (e.g., "390")
        water_temp: Water cooling temperature from KB (e.g., "40")
        tolerance: Temperature tolerance from KB
        source_doc: Source document reference
    
    Returns:
        Confirmation message
    """
    try:
        data = {
            "zones": [
                {"name": "Z1", "value": f"{z1_temp} C"},
                {"name": "Z2", "value": f"{z2_temp} C"},
                {"name": "Z3", "value": f"{z3_temp} C"},
                {"name": "Z4", "value": f"{z4_temp} C"},
                {"name": "Die", "value": f"{die_temp} C"},
            ],
            "auxiliary": [
                f"Water Cooling: {water_temp} C (plus or minus 10 C)",
                f"Tolerance: {tolerance} for all zones"
            ],
            "notes": []
        }
        
        # Add PFA-specific note about water cooling
        if compound.upper() == "PFA":
            data["notes"].append("WARNING: PFA - Do NOT use water cooling during extrusion")
        
        success = await send_overlay(
            layout_type="parameter-grid",
            title=f"{compound.upper()} Temperature Profile",
            data=data,
            context=f"Compound: {compound.upper()}",
            source=f"{source_doc}, Section TPL/TD/28"
        )
        
        if success:
            return f"{compound.upper()} temperature profile displayed on screen."
        else:
            return f"For {compound.upper()}: Z1={z1_temp}C, Z2={z2_temp}C, Z3={z3_temp}C, Z4={z4_temp}C, Die={die_temp}C. Water temp {water_temp}C. Tolerance {tolerance}."
        
    except Exception as e:
        logger.error(f"Temperature profile overlay error: {e}")
        return f"Error displaying temperature profile: {str(e)}"


@llm.function_tool
async def show_safety_alert(
    warning: str,
    dos_json: str = "",
    donts_json: str = "",
    reference: str = "TPL/WI/P/15"
) -> str:
    """
    Display a safety alert with do's and don'ts from work instructions.
    Use this for safety-related queries, spark testing, PPE requirements, etc.
    The content should come from knowledge_lookup first.
    
    Args:
        warning: Main warning message (e.g., "Spark tester must be ON during production")
        dos_json: JSON array of do's. Example: ["Check spark tester ON", "Use standard tools"]
        donts_json: JSON array of don'ts. Example: ["Don't produce without spark test", "Don't use sharp blades"]
        reference: Document reference (e.g., "TPL/WI/P/15, Section 5")
    
    Returns:
        Confirmation message
    """
    try:
        dos = json.loads(dos_json) if dos_json else []
        donts = json.loads(donts_json) if donts_json else []
        
        data = {
            "warning": warning,
            "dos": dos[:5],
            "donts": donts[:5],
            "reference": reference
        }
        
        success = await send_overlay(
            layout_type="alert-information",
            title="Safety Alert",
            data=data,
            context="Work Instruction Safety Guidelines",
            source=reference
        )
        
        if success:
            return "Safety alert displayed on screen."
        else:
            return f"IMPORTANT: {warning}. Please refer to {reference} for complete safety guidelines."
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in safety alert: {e}")
        return "Error: Invalid data format for safety alert"
    except Exception as e:
        logger.error(f"Safety alert overlay error: {e}")
        return f"Error displaying safety alert: {str(e)}"


@llm.function_tool
async def show_single_value(
    title: str,
    value: str,
    label: str,
    context: str = "",
    source: str = "",
    range: str = "",
    tolerance: str = ""
) -> str:
    """
    Display a single prominent value (temperature, measurement, etc).
    Use when answering questions about ONE specific parameter.
    
    Args:
        title: Header title (e.g., "Z3 Temperature")
        value: The main value to display (e.g., "310 degrees Celsius")
        label: Label for the value (e.g., "Zone 3")
        context: Material/machine info (e.g., "Material: ETFE")
        source: Document reference (e.g., "TPL-TD-28")
        range: Acceptable range (e.g., "290 to 330 degrees Celsius")
        tolerance: Tolerance value (e.g., "plus or minus 20 degrees Celsius")
    
    Returns:
        Confirmation message
    """
    try:
        data = {
            "value": value,
            "label": label,
            "range": range,
            "tolerance": tolerance
        }
        
        success = await send_overlay(
            layout_type="single-value",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Single value displayed on screen" if success else "Failed to display overlay"
        
    except Exception as e:
        logger.error(f"Single value overlay error: {e}")
        return f"Error displaying value: {str(e)}"

# -------------------------
# UTILITY TOOLS
# -------------------------

@llm.function_tool
async def hide_overlay() -> str:
    """
    Hide/dismiss the current UI overlay card.
    Use this when the user is done viewing information or asks to close the overlay.
    
    Returns:
        Confirmation that overlay was hidden
    """
    try:
        room = get_job_context().room
        participant_identity = next(iter(room.remote_participants.keys()), None)
        
        if not participant_identity:
            return "No user connected"
        
        await room.local_participant.perform_rpc(
            destination_identity=participant_identity,
            method="hideOverlay",
            payload="{}",
            response_timeout=5.0,
        )
        
        logger.info("Overlay hidden")
        return "Overlay hidden"
        
    except Exception as e:
        logger.error(f"Failed to hide overlay: {e}")
        return f"Failed to hide overlay: {str(e)}"

@llm.function_tool
async def end_call() -> str:
    """
    End the conversation and disconnect the session.
    Use this when the user says goodbye, thanks and leaves, or the interaction is completed.
    
    Returns:
        Confirmation that session ended
    """
    global _current_room
    if _current_room:
        try:
            await _current_room.disconnect()
            logger.info("Session ended by agent")
            return "Session ended. Thank you for using Thermopads Line Support."
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return "Error ending session."
    return "No active session."

# -------------------------
# AGENT CLASS
# -------------------------
_current_room = None

class ThermopadsSupervisor(Agent):
    def __init__(self):
        # Use instructions from persona.yaml
        full_instructions = f"NAME: {NAME}\n\nCORE INSTRUCTIONS:\n{INSTRUCTIONS}\n\n--- SYSTEM GUIDELINES ---\n{SYSTEM_GUIDELINES}"
        
        super().__init__(
            instructions=full_instructions,
            tools=[
                # Knowledge Base
                knowledge_lookup,
                # Session Context
                set_machine_context,
                # Thermopads-Specific Overlays
                show_ddr_table,
                show_temperature_profile,
                show_safety_alert,
                # Generic Overlays
                show_single_value,
                # Utility
                hide_overlay,
                end_call,
            ],
        )

    async def on_enter(self):
        # Use say() for instant greeting - no LLM processing needed
        greeting_text = GREETING if GREETING else "Good morning. I am Cara, your Line Support Assistant. Tell me, which machine line are you working on today?"
        await self.session.say(greeting_text, allow_interruptions=True)

# -------------------------
# SERVER & MAIN
# -------------------------
server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="thermopads-supervisor")
async def entrypoint(ctx: JobContext):
    global _current_room
    _current_room = ctx.room

    # Avatar (Simli) - from .env
    simli_api_key = os.getenv("SIMLI_API_KEY")
    simli_face_id = os.getenv("SIMLI_FACE_ID")

    # Cartesia TTS - from .env
    cartesia_api_key = os.getenv("CARTESIA_API_KEY")
    cartesia_model = os.getenv("CARTESIA_MODEL", "sonic-2")
    cartesia_voice = os.getenv("CARTESIA_VOICE")
    cartesia_language = os.getenv("CARTESIA_LANGUAGE", "en")

    if not simli_api_key or not simli_face_id:
        logger.error("SIMLI_API_KEY or SIMLI_FACE_ID missing")
        return

    if not cartesia_api_key:
        logger.error("CARTESIA_API_KEY missing")
        return

    avatar = simli.AvatarSession(
        simli_config=simli.SimliConfig(api_key=simli_api_key, face_id=simli_face_id),
    )

    # Session Config
    session = AgentSession(
        stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.4),
        llm=openai.LLM(model="gpt-4.1-mini-2025-04-14"),
        tts=cartesia.TTS(
            api_key=cartesia_api_key,
            model=cartesia_model,
            voice=cartesia_voice,
            language=cartesia_language,
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
        agent=ThermopadsSupervisor(),
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
