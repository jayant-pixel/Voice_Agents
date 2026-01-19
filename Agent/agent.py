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
    noise_cancellation,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Custom TTS & KB Manager
from chatterbox_plugin.chatterbox_tts import ChatterboxTTS
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
# OVERLAY TOOLS - NEW SPEC
# -------------------------

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
        value: The main value to display (e.g., "310°C")
        label: Label for the value (e.g., "Zone 3")
        context: Material/machine info (e.g., "Material: ETFE")
        source: Document reference (e.g., "TPL-TD-28")
        range: Acceptable range (e.g., "290°C - 330°C")
        tolerance: Tolerance value (e.g., "±20°C")
    
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


@llm.function_tool
async def show_quick_lookup(
    title: str,
    wire_size: str,
    values_json: str,
    context: str = "",
    source: str = "",
    adjacent_json: str = ""
) -> str:
    """
    Display a quick lookup result with die/nozzle specs.
    Use for tooling questions like "What die for X wire?".
    
    Args:
        title: Header title (e.g., "Die & Nozzle Selection")
        wire_size: Wire size range (e.g., "0.3-0.35mm")
        values_json: JSON object of values. Example: {"Die ID": "9 or 10", "Nozzle OD": "4.5", "Nozzle ID": "0.8 or 1"}
        context: Additional context (e.g., "Wire Size: 0.35mm")
        source: Document reference (e.g., "DDR Chart-3, Row 3")
        adjacent_json: JSON array of context. Example: ["0.25-0.3mm: Same configuration", "0.35-0.4mm: Die 10"]
    
    Returns:
        Confirmation message
    """
    try:
        values = json.loads(values_json)
        adjacent = json.loads(adjacent_json) if adjacent_json else []
        
        data = {
            "wire_size": wire_size,
            "values": values,
            "adjacent": adjacent
        }
        
        success = await send_overlay(
            layout_type="quick-lookup",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Quick lookup displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in quick lookup: {e}")
        return "Error: Invalid data format"
    except Exception as e:
        logger.error(f"Quick lookup overlay error: {e}")
        return f"Error displaying lookup: {str(e)}"


@llm.function_tool
async def show_range_display(
    title: str,
    target: str,
    minimum: str,
    maximum: str,
    context: str = "",
    source: str = "",
    tolerance: str = "",
    notes_json: str = ""
) -> str:
    """
    Display a range/specification with target value.
    Use for questions about acceptable ranges and tolerances.
    
    Args:
        title: Header title (e.g., "Water Cooling Temperature")
        target: Target value (e.g., "40°C")
        minimum: Minimum acceptable (e.g., "30°C")
        maximum: Maximum acceptable (e.g., "50°C")
        context: Material/machine info (e.g., "Material: ETFE | Machine: ROSENDAHL")
        source: Document reference (e.g., "TPL-TD-28")
        tolerance: Tolerance spec (e.g., "±10°C")
        notes_json: JSON array of notes. Example: ["Gap to Hot Water Zone: 0.5 - 1.5 meters"]
    
    Returns:
        Confirmation message
    """
    try:
        notes = json.loads(notes_json) if notes_json else []
        
        data = {
            "target": target,
            "minimum": minimum,
            "maximum": maximum,
            "tolerance": tolerance,
            "notes": notes
        }
        
        success = await send_overlay(
            layout_type="range-display",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Range display shown on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in range display: {e}")
        return "Error: Invalid data format"
    except Exception as e:
        logger.error(f"Range display overlay error: {e}")
        return f"Error displaying range: {str(e)}"


@llm.function_tool
async def show_multi_parameter(
    title: str,
    parameters_json: str,
    context: str = "",
    source: str = "",
    note: str = ""
) -> str:
    """
    Display multiple related parameters together.
    Use when showing 2-3 related settings (e.g., water temp AND gap distance).
    
    Args:
        title: Header title (e.g., "Water System Settings")
        parameters_json: JSON array of parameters. Example:
            [{"name": "Water Cooling Temperature", "target": "40°C", "range": "30-50°C", "tolerance": "±10°C"},
             {"name": "Gap Distance", "range": "0.5 - 1.5 meters"}]
        context: Material/machine info (e.g., "Material: ETFE | ROSENDAHL")
        source: Document reference (e.g., "TPL-TD-28")
        note: Important note (e.g., "Water circulation must be ON during extrusion")
    
    Returns:
        Confirmation message
    """
    try:
        parameters = json.loads(parameters_json)
        
        data = {
            "parameters": parameters[:4],  # Max 4 parameters
            "note": note
        }
        
        success = await send_overlay(
            layout_type="multi-parameter",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Multi-parameter display shown on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in multi-parameter: {e}")
        return "Error: Invalid data format"
    except Exception as e:
        logger.error(f"Multi-parameter overlay error: {e}")
        return f"Error displaying parameters: {str(e)}"


@llm.function_tool
async def show_parameter_grid(
    title: str,
    zones_json: str,
    context: str = "",
    source: str = "",
    auxiliary_json: str = "",
    notes_json: str = ""
) -> str:
    """
    Display temperature zones in a grid layout (2-3 columns).
    Use for showing all temperature zones for a material/machine.
    
    Args:
        title: Header title (e.g., "ETFE Temperature Profile")
        zones_json: JSON array of zones. Example:
            [{"name": "Z1", "value": "280°C", "range": "260-300"},
             {"name": "Z2", "value": "290°C", "range": "270-310"}]
        context: Machine info (e.g., "Machine: ROSENDAHL")
        source: Document reference (e.g., "TPL-TD-28, Page 1")
        auxiliary_json: JSON array of auxiliary settings. Example: ["Water Cooling: 40°C (±10°C)", "Tolerance: ±20°C"]
        notes_json: JSON array of notes. Example: ["Gap Distance: 0.5-1.5 meters"]
    
    Returns:
        Confirmation message
    """
    try:
        zones = json.loads(zones_json)
        auxiliary = json.loads(auxiliary_json) if auxiliary_json else []
        notes = json.loads(notes_json) if notes_json else []
        
        data = {
            "zones": zones[:9],  # Max 9 zones (3x3 grid)
            "auxiliary": auxiliary[:6],
            "notes": notes[:3]
        }
        
        success = await send_overlay(
            layout_type="parameter-grid",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Temperature grid displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in parameter grid: {e}")
        return "Error: Invalid data format"
    except Exception as e:
        logger.error(f"Parameter grid overlay error: {e}")
        return f"Error displaying grid: {str(e)}"


@llm.function_tool
async def show_comparison_table(
    title: str,
    columns_json: str,
    rows_json: str,
    context: str = "",
    source: str = "",
    analysis: str = "",
    additional_json: str = ""
) -> str:
    """
    Display a comparison table for materials or parameters.
    Use when comparing two or more materials/settings.
    
    Args:
        title: Header title (e.g., "Temperature Comparison")
        columns_json: JSON array of column headers. Example: ["Zone", "ETFE", "FEP", "Status"]
        rows_json: JSON array of row objects. Example:
            [{"Zone": "Z1", "ETFE": "280°C", "FEP": "280°C", "Status": "Same ✓"},
             {"Zone": "Z2", "ETFE": "290°C", "FEP": "290°C", "Status": "Same ✓"}]
        context: Context info (e.g., "ETFE vs FEP | Machine: ROSENDAHL")
        source: Document reference (e.g., "TPL-TD-28")
        analysis: Analysis text (e.g., "All temperature parameters are identical.")
        additional_json: JSON array of notes. Example: ["ETFE: 40°C (±10°C)", "FEP: 40°C (±10°C) ✓ Same"]
    
    Returns:
        Confirmation message
    """
    try:
        columns = json.loads(columns_json)
        rows = json.loads(rows_json)
        additional = json.loads(additional_json) if additional_json else []
        
        data = {
            "columns": columns[:5],  # Max 5 columns
            "rows": rows[:10],  # Max 10 rows
            "analysis": analysis,
            "additional": additional[:3]
        }
        
        success = await send_overlay(
            layout_type="comparison-table",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Comparison table displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in comparison table: {e}")
        return "Error: Invalid data format"
    except Exception as e:
        logger.error(f"Comparison table overlay error: {e}")
        return f"Error displaying comparison: {str(e)}"


@llm.function_tool
async def show_alert_information(
    title: str,
    warning: str,
    context: str = "",
    source: str = "",
    donts_json: str = "",
    dos_json: str = "",
    reference: str = ""
) -> str:
    """
    Display a safety/warning alert with critical information.
    Use for material-specific warnings, safety limits, or restrictions.
    
    Args:
        title: Header title (e.g., "Material-Specific Requirements")
        warning: Main warning message (e.g., "DO NOT USE WATER COOLING")
        context: Material info (e.g., "Material: PFA")
        source: Document reference (e.g., "Inner Extrusion WI, Note 9")
        donts_json: JSON array of don'ts. Example: ["Water circulation must be OFF", "Gap distance does not apply"]
        dos_json: JSON array of dos. Example: ["Temperature: 320-390°C (higher)", "Pre-heater: 80-100%"]
        reference: Reference quote (e.g., "For PFA insulation don't use water")
    
    Returns:
        Confirmation message
    """
    try:
        donts = json.loads(donts_json) if donts_json else []
        dos = json.loads(dos_json) if dos_json else []
        
        data = {
            "warning": warning,
            "donts": donts[:5],
            "dos": dos[:5],
            "reference": reference
        }
        
        success = await send_overlay(
            layout_type="alert-information",
            title=title,
            context=context,
            source=source,
            data=data
        )
        
        return "Alert displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in alert: {e}")
        return "Error: Invalid data format"
    except Exception as e:
        logger.error(f"Alert overlay error: {e}")
        return f"Error displaying alert: {str(e)}"

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
        # Load system prompt from file
        prompt_path = Path(__file__).parent / "thermopads_voice_agent_prompt.md"
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                full_instructions = f.read()
        else:
            # Fallback to persona-based instructions
            full_instructions = f"NAME: {NAME}\n\nCORE INSTRUCTIONS:\n{INSTRUCTIONS}\n\n--- SYSTEM GUIDELINES ---\n{SYSTEM_GUIDELINES}"
        
        super().__init__(
            instructions=full_instructions,
            tools=[
                knowledge_lookup,
                show_single_value,
                show_quick_lookup,
                show_range_display,
                show_multi_parameter,
                show_parameter_grid,
                show_comparison_table,
                show_alert_information,
                hide_overlay,
                end_call,
            ],
        )

    async def on_enter(self):
        await self.session.generate_reply(
            instructions=GREETING if GREETING else "Good morning. I am your Line Support Assistant. Tell me, which machine line are you working on?",
            allow_interruptions=True,
        )

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