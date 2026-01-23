# Thermopads Voice Agent – Overview

## Quick Reference

| Component | Technology | Config |
|-----------|-----------|--------|
| **LLM** | OpenAI `gpt-4.1-mini-2025-04-14` | - |
| **STT** | Deepgram `flux-general-en` | VAD: Silero |
| **TTS** | Cartesia | .env: `CARTESIA_*` |
| **Avatar** | Simli | .env: `SIMLI_*` |
| **Turn Detection** | MultilingualModel | - |

---

## System Prompt (source: `Agent/persona.yaml`)

**Role:** Cara - Thermopads Line Support Assistant  
**Company:** Thermopads Pvt. Ltd., Hyderabad (ISO 9001/14001/45001 certified)

**Greeting:** (Instant via `session.say()`)
> "Good morning. I am Cara, your Line Support Assistant. Tell me, which machine line are you working on today?"

### Core Behavior
- Safety-first: Verify safe ranges before any parameter change
- KB-first: Always search knowledge base before answering
- Voice-friendly: Plain text only, no markdown, spell out numbers
- Respectful: Indian industrial English ("as per", "tell me", "sir")

---

## Tools Exposed to LLM

All functions in `Agent/agent.py`:

### Knowledge Base
| Tool | Purpose |
|------|---------|
| `knowledge_lookup(query, context_type)` | Search KB for technical info |
| `set_machine_context(machine_id, product_variant, compound_type)` | Store session context |

### Thermopads-Specific Overlays
| Tool | Layout Type | Purpose |
|------|-------------|---------|
| `show_ddr_table(wire_size, die_id, nozzle_od, nozzle_id, thickness)` | `comparison-table` | Chart-3 DDR lookup |
| `show_temperature_profile(compound, z1-z4, die_temp, water_temp)` | `parameter-grid` | TPL/TD/28 zones |
| `show_safety_alert(warning, dos_json, donts_json, reference)` | `alert-information` | TPL/WI/P/15 safety |
| `show_single_value(title, value, label, range, tolerance)` | `single-value` | Single parameter |

### Utility
| Tool | Purpose |
|------|---------|
| `hide_overlay()` | Dismiss current overlay |
| `end_call()` | Disconnect session |

---

## Overlay Layouts (source: `components/ManufacturingOverlay.tsx`)

**4 Active Layouts:**

### 1. `single-value` (350px)
```
┌──────────────────────────────────┐
│ Z3 Temperature          [Source] │
├──────────────────────────────────┤
│         310°C                    │
│         Zone 3                   │
│  Range: 290-330°C                │
│  Tolerance: ±20°C                │
└──────────────────────────────────┘
```

### 2. `parameter-grid` (550px) - Temperature Profile
```
┌──────────────────────────────────────────┐
│ ETFE Temperature Profile       [TPL/TD/28]│
├──────────────────────────────────────────┤
│  Z1      │   Z2      │   Z3              │
│ 280°C    │  290°C    │  300°C            │
├──────────────────────────────────────────┤
│  Z4      │   Die                         │
│ 310°C    │  320°C                        │
├──────────────────────────────────────────┤
│ Auxiliary Settings:                      │
│ • Water Cooling: 40°C (±10°C)           │
│ • Tolerance: ±20°C for all zones        │
└──────────────────────────────────────────┘
```

### 3. `alert-information` (500px) - Safety Alert
```
┌──────────────────────────────────────────┐
│ ⚠️ Safety Alert           [TPL/WI/P/15]  │
├──────────────────────────────────────────┤
│ 🚫 Spark tester must be ON during prod   │
│                                          │
│ DON'Ts:                                  │
│ ❌ Don't produce without spark test      │
│ ❌ Don't use sharp blades for cleaning   │
│                                          │
│ DO's:                                    │
│ ✅ Check spark tester ON during prod     │
│ ✅ Use only standard tools               │
└──────────────────────────────────────────┘
```

### 4. `comparison-table` (650px) - DDR Table
```
┌──────────────────────────────────────────────────┐
│ DDR Settings from Chart-3          [Chart-3]     │
├──────────────────────────────────────────────────┤
│ Parameter      │ Value                           │
├────────────────┼─────────────────────────────────│
│ Wire Size      │ 0.3-0.35                        │
│ Die ID         │ 9 or 10                         │
│ Nozzle OD      │ 4.5                             │
│ Nozzle ID      │ 0.8 or 1                        │
│ Thickness      │ 0.32 mm                         │
├──────────────────────────────────────────────────┤
│ 💡 DDR settings for wire size 0.3-0.35mm        │
└──────────────────────────────────────────────────┘
```

---

## RPC Communication

**Overlay Display:**
```json
{
  "layoutType": "parameter-grid",
  "title": "ETFE Temperature Profile",
  "context": "Compound: ETFE",
  "source": "TPL/TD/28",
  "data": { ... }
}
```

**Methods:**
- `showOverlay` - Display overlay card
- `hideOverlay` - Dismiss overlay card

**Timeout:** 5 seconds

---

## Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SIMLI_API_KEY=...
SIMLI_FACE_ID=...
CARTESIA_API_KEY=...

# Optional (with defaults)
CARTESIA_MODEL=sonic-2
CARTESIA_VOICE=<your-voice-id>
CARTESIA_LANGUAGE=en
```

---

## Tool Selection Rules

| Query Type | Tool | Layout |
|------------|------|--------|
| Single value ("What's Z3 temp?") | `show_single_value` | single-value |
| Die/nozzle lookup ("Die for 0.35mm?") | `show_ddr_table` | comparison-table |
| Temperature zones ("ETFE temps?") | `show_temperature_profile` | parameter-grid |
| Safety warning ("Spark test rules?") | `show_safety_alert` | alert-information |
| Simple 1-3 values | Verbal only | N/A |

---

## KB Documents Available

| Document | Content |
|----------|---------|
| **Chart-3** | DDR table - die/nozzle combinations by wire size |
| **TPL/TD/28** | Temperature profiles by compound (ETFE, PFA, PA11, etc.) |
| **TPL/WI/P/15** | Inner extrusion procedures, setup, safety do's/don'ts |
| **Troubleshooting** | Root causes and solutions for common issues |

---

## Safety Rules (Non-Negotiable)

- Spark tester ON at 6-7 kV AC during production
- Water cooling ON during extrusion (except PFA)
- Never suggest changes >5°C temperature or >2 m/min speed at once
- Wait 2-5 minutes after adjustment before next change

---

## File Structure

```
Agent/
├── agent.py           # Main agent logic, tools, session config
├── persona.yaml       # System prompt and role configuration
├── KB_pipeline/       # Knowledge base search
│   ├── kb_search.py   # Hybrid search (BM25 + embeddings)
│   └── kb_store/      # Indexed documents
└── docs/
    └── agent_overview.md  # This file

components/
└── ManufacturingOverlay.tsx  # Overlay UI component
```

---

**Last Updated:** January 2026
