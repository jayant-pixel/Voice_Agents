import os
import json
import logging
import yaml
import base64
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

async def send_overlay(overlay_type: str, title: str, data: dict, subtitle: str = "", source: str = ""):
    """Helper function to send overlay to frontend"""
    try:
        room = get_job_context().room
        participant_identity = next(iter(room.remote_participants.keys()), None)
        
        if not participant_identity:
            logger.warning("No participant connected for overlay display")
            return False
        
        payload = json.dumps({
            "type": overlay_type,
            "title": title,
            "subtitle": subtitle,
            "source": source,
            "data": data
        })
        
        await room.local_participant.perform_rpc(
            destination_identity=participant_identity,
            method="showOverlay",
            payload=payload,
            response_timeout=5.0,
        )
        
        logger.info(f"Overlay sent: {overlay_type} - {title}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send overlay: {e}")
        return False

def should_show_overlay(data_points: int, has_table: bool = False, has_steps: bool = False) -> bool:
    """Determine if overlay should be shown based on complexity"""
    if data_points >= 5:
        return True
    if has_table and data_points >= 3:
        return True
    if has_steps and data_points >= 3:
        return True
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
        
    Important: 
    - Always cite document references in your response (e.g., "As per TPL/TD/28...")
    - For complex data (5+ values, tables, procedures), consider using show_overlay tool
    - For temperature profiles with 6+ zones, use show_temperature_profile tool instead
    """
    try:
        # Add context type to query for better retrieval
        enhanced_query = f"[{context_type}] {query}" if context_type != "general" else query
        
        result = await kb_manager.query(enhanced_query, include_images=False)
        
        if not result.text:
            return f"No information found for query: {query}. Please rephrase or ask for related information."
        
        # Format response with sources
        response = result.text
        if result.sources:
            sources_str = ", ".join(result.sources[:3])  # Limit to top 3 sources
            response += f"\n\nReference: {sources_str}"
        
        return response
        
    except Exception as e:
        logger.error(f"Knowledge lookup error: {e}")
        return f"Error searching knowledge base: {str(e)}"

# -------------------------
# SPECIALIZED OVERLAY TOOLS
# -------------------------

@llm.function_tool
async def show_temperature_profile(
    material: str,
    machine: str,
    zones_json: str
) -> str:
    """
    Display temperature profile overlay for machine setup.
    Use this when providing temperature settings with 6+ zones.
    
    Args:
        material: Material type (e.g., "ETFE", "FEP", "PFA", "PVC")
        machine: Machine identifier (e.g., "ROSENDAHL TPL/M/60", "WINDSOR TPL/M/43")
        zones_json: JSON string of zone temperatures. Example:
               {"barrel": {"Z1": "280C", "Z2": "290C"}, "head": {"H1": "350C"}, "tolerance": "±20C"}
    
    Returns:
        Confirmation that overlay was displayed
    """
    try:
        zones = json.loads(zones_json)
        
        # Flatten zones into rows for table display
        rows = []
        
        # Barrel zones
        if "barrel" in zones:
            for zone, temp in zones["barrel"].items():
                rows.append({"zone": zone, "temperature": temp, "section": "Barrel"})
        
        # Head zones
        if "head" in zones:
            for zone, temp in zones["head"].items():
                rows.append({"zone": zone, "temperature": temp, "section": "Head"})
        
        # Auxiliary parameters
        aux_text = []
        if "auxiliary" in zones:
            for param, value in zones["auxiliary"].items():
                aux_text.append(f"• {param}: {value}")
        
        # Notes
        notes = []
        if "tolerance" in zones:
            notes.append(f"⚠️ Tolerance: {zones['tolerance']} on all zones")
        if "heating_time" in zones:
            notes.append(f"⏱ Heating time: {zones['heating_time']}")
        
        data = {
            "rows": rows[:8],  # Max 8 rows per spec
            "auxiliary": "\n".join(aux_text[:6]),  # Max 6 aux items
            "notes": "\n".join(notes[:3])  # Max 3 notes
        }
        
        success = await send_overlay(
            overlay_type="temperature-profile",
            title=f"{material} Temperature Profile",
            subtitle=f"Machine: {machine}",
            source="TPL/TD/28 Rev 08/02",
            data=data
        )
        
        return "Temperature profile displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid zones JSON: {e}")
        return f"Error: Invalid zones format"
    except Exception as e:
        logger.error(f"Temperature profile overlay error: {e}")
        return f"Error displaying temperature profile: {str(e)}"

@llm.function_tool
async def show_corrective_action(
    issue: str,
    steps_json: str,
    safety_limits_json: str = ""
) -> str:
    """
    Display step-by-step corrective action procedure.
    Use this when providing multi-step troubleshooting solutions (3+ steps).
    
    Args:
        issue: Description of the issue being corrected (e.g., "Screw Speed Mismatch")
        steps_json: JSON array of steps. Example: [{"number": 1, "action": "Reduce speed", "details": ["From 31 to 28 RPM"]}]
        safety_limits_json: Optional JSON object of limits. Example: {"Screw Speed": "25-35 RPM"}
    
    Returns:
        Confirmation that overlay was displayed
    """
    try:
        steps = json.loads(steps_json)
        safety_limits = json.loads(safety_limits_json) if safety_limits_json else None
        
        # Format steps (max 4)
        formatted_steps = []
        for step in steps[:4]:
            formatted_steps.append({
                "number": step.get("number", len(formatted_steps) + 1),
                "action": step.get("action", ""),
                "details": step.get("details", [])[:4]  # Max 4 details per step
            })
        
        # Format safety limits (single line with separators)
        safety_text = ""
        if safety_limits:
            safety_items = [f"{k}: {v}" for k, v in list(safety_limits.items())[:4]]
            safety_text = " | ".join(safety_items)
        
        data = {
            "steps": formatted_steps,
            "safety_limits": safety_text
        }
        
        success = await send_overlay(
            overlay_type="corrective-action",
            title="Corrective Action Plan",
            subtitle=f"Issue: {issue}",
            source="Process Control SOP",
            data=data
        )
        
        return "Corrective action plan displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in corrective action: {e}")
        return f"Error: Invalid step format"
    except Exception as e:
        logger.error(f"Corrective action overlay error: {e}")
        return f"Error displaying corrective action: {str(e)}"

@llm.function_tool
async def show_quality_verification(
    parameter: str,
    target: str,
    tolerance: str,
    measurements_json: str
) -> str:
    """
    Display quality verification results with pass/fail status.
    Use this when operator provides multiple measurement readings (3+ points).
    
    Args:
        parameter: What was measured (e.g., "Output Dimension", "Strip Force")
        target: Target value (e.g., "0.95mm", "40C")
        tolerance: Tolerance specification (e.g., "±0.02mm", "±10C")
        measurements_json: JSON array of measurements. Example: [{"point": "Point 1", "reading": "0.94mm", "status": "pass"}]
    
    Returns:
        Confirmation that overlay was displayed with pass/fail verdict
    """
    try:
        import re
        measurements = json.loads(measurements_json)
        
        # Calculate acceptable range
        target_match = re.search(r'([\d.]+)', target)
        tolerance_match = re.search(r'±([\d.]+)', tolerance)
        
        range_text = ""
        if target_match and tolerance_match:
            target_val = float(target_match.group(1))
            tol_val = float(tolerance_match.group(1))
            unit = target.replace(target_match.group(1), "").strip()
            lower = target_val - tol_val
            upper = target_val + tol_val
            range_text = f"{lower:.2f} - {upper:.2f}{unit}"
        
        # Determine overall verdict
        all_pass = all(m.get("status") == "pass" for m in measurements)
        verdict = "ALL WITHIN SPECIFICATION" if all_pass else "OUT OF SPECIFICATION"
        verdict_icon = "✅" if all_pass else "❌"
        
        # Calculate statistics if numeric
        try:
            readings = [float(re.search(r'([\d.]+)', m["reading"]).group(1)) for m in measurements]
            avg = sum(readings) / len(readings)
            range_val = max(readings) - min(readings)
            stats_text = f"Average: {avg:.2f} | Range: {range_val:.2f}"
        except:
            stats_text = ""
        
        data = {
            "spec": f"Target: {target} | Tolerance: {tolerance}",
            "range": f"Acceptable Range: {range_text}",
            "measurements": measurements[:5],  # Max 5 measurements
            "statistics": stats_text,
            "verdict": verdict,
            "verdict_icon": verdict_icon
        }
        
        success = await send_overlay(
            overlay_type="quality-verification",
            title="Quality Verification",
            subtitle=f"Parameter: {parameter}",
            source="Quality Control SOP QC-001",
            data=data
        )
        
        return f"Quality verification displayed: {verdict}" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid measurements JSON: {e}")
        return f"Error: Invalid measurements format"
    except Exception as e:
        logger.error(f"Quality verification overlay error: {e}")
        return f"Error displaying quality verification: {str(e)}"

@llm.function_tool
async def show_documentation_reminder(
    session_type: str,
    auto_captured_json: str,
    manual_required_json: str
) -> str:
    """
    Display documentation checklist reminder.
    Use this to remind operator what needs to be logged in production records.
    
    Args:
        session_type: Type of session (e.g., "Troubleshooting", "Setup", "Quality Check")
        auto_captured_json: JSON object of captured data. Example: {"Machine": "Extruder 2", "Action": "Speed adjusted"}
        manual_required_json: JSON array of manual items. Example: ["Operator signature", "Supervisor approval"]
    
    Returns:
        Confirmation that overlay was displayed
    """
    try:
        auto_captured = json.loads(auto_captured_json)
        manual_required = json.loads(manual_required_json)
        
        # Format auto-captured (max 8 items)
        auto_items = []
        for key, value in list(auto_captured.items())[:8]:
            auto_items.append({"label": key, "value": value})
        
        # Manual items (max 5)
        manual_items = manual_required[:5]
        
        data = {
            "auto_captured": auto_items,
            "manual_required": manual_items,
            "location_digital": "Main HMI → Production Tab → Current Run",
            "location_paper": "Paper form at Supervisor desk",
            "deadline": "Complete before shift handover"
        }
        
        success = await send_overlay(
            overlay_type="documentation-checklist",
            title="Documentation Required",
            subtitle=f"Session: {session_type}",
            source="SOP-DOC-001",
            data=data
        )
        
        return "Documentation reminder displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in documentation reminder: {e}")
        return f"Error: Invalid data format"
    except Exception as e:
        logger.error(f"Documentation overlay error: {e}")
        return f"Error displaying documentation reminder: {str(e)}"

@llm.function_tool
async def show_knowledge_summary(
    problem: str,
    root_cause: str,
    solution: str,
    key_learnings_json: str,
    quick_reference_json: str = ""
) -> str:
    """
    Display learning summary at end of troubleshooting session.
    Use this to provide educational recap for knowledge transfer.
    
    Args:
        problem: Problem statement (1-2 sentences, max 120 chars)
        root_cause: Root cause explanation (1-2 sentences, max 120 chars)
        solution: Solution applied (1-2 sentences, max 120 chars)
        key_learnings_json: JSON array of learnings. Example: [{"title": "Speed", "lesson": "Maintain ratio"}]
        quick_reference_json: Optional JSON array of tips. Example: ["Oversize? Check screw speed"]
    
    Returns:
        Confirmation that overlay was displayed
    """
    try:
        key_learnings = json.loads(key_learnings_json)
        quick_reference = json.loads(quick_reference_json) if quick_reference_json else None
        
        # Format learnings (max 3, 2 lines each)
        formatted_learnings = []
        for i, learning in enumerate(key_learnings[:3], 1):
            formatted_learnings.append({
                "number": f"{i}️⃣",
                "title": learning.get("title", "")[:30],  # Max 30 chars for title
                "lesson": learning.get("lesson", "")[:120]  # Max 120 chars
            })
        
        # Quick reference (max 3 lines)
        ref_text = "\n".join(quick_reference[:3]) if quick_reference else ""
        
        data = {
            "problem": problem[:120],
            "root_cause": root_cause[:120],
            "solution": solution[:120],
            "learnings": formatted_learnings,
            "quick_reference": ref_text
        }
        
        success = await send_overlay(
            overlay_type="knowledge-summary",
            title="Session Learning Summary",
            subtitle="Key Takeaways",
            source="Process Control Guide",
            data=data
        )
        
        return "Knowledge summary displayed on screen" if success else "Failed to display overlay"
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in knowledge summary: {e}")
        return f"Error: Invalid data format"
    except Exception as e:
        logger.error(f"Knowledge summary overlay error: {e}")
        return f"Error displaying knowledge summary: {str(e)}"

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
                show_temperature_profile,
                show_corrective_action,
                show_quality_verification,
                show_documentation_reminder,
                show_knowledge_summary,
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