# 📘 AI Agent Overlay System - Developer Guide
## Template Documentation for Building Voice + UI Applications

> **Purpose:** This is a complete reference guide for development teams building AI voice agents with visual overlays. Use this document when creating agents for any domain: Finance, Retail, Healthcare, Manufacturing, or any custom scenario.

---

## 📁 Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [File Structure Template](#3-file-structure-template)
4. [Data Flow](#4-data-flow)
5. [Python Agent Configuration](#5-python-agent-configuration)
6. [RPC Bridge Setup](#6-rpc-bridge-setup)
7. [Overlay Component Design](#7-overlay-component-design)
8. [Planning Your Overlays](#8-planning-your-overlays)
9. [Styling Guidelines](#9-styling-guidelines)
10. [Testing Checklist](#10-testing-checklist)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Introduction

### What is the Overlay System?

The overlay system allows an AI voice agent to display visual information on the user's screen during a conversation. While the agent speaks, it can also show:
- Data tables
- Step-by-step instructions
- Charts and metrics
- Confirmation dialogs
- Any structured information

### When to Use Overlays

| Good Use Cases | Avoid Using For |
|----------------|-----------------|
| Complex data with 5+ items | Simple yes/no confirmations |
| Tables, charts, comparisons | Information that fits in 1-2 sentences |
| Step-by-step procedures | Quick facts |
| Multi-field forms | Single values |
| Visual verification needed | Transient information |

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Voice Agent | Python + LiveKit Agents | Handle voice interaction, LLM, TTS |
| Communication | LiveKit RPC | Send data from agent to UI |
| UI Display | React + TypeScript | Render visual overlays |
| Styling | Tailwind CSS | Style components |

---

## 2. Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Overlay Component                          │   │
│  │  • Receives overlay data                                      │   │
│  │  • Renders based on type                                      │   │
│  │  • Handles styling and interactions                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ Props (overlay data)
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                         RPC BRIDGE                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Room Component                             │   │
│  │  • Registers RPC methods                                      │   │
│  │  • Receives calls from Python                                 │   │
│  │  • Manages overlay state                                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ RPC Call ("showOverlay")
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                       LIVEKIT SERVER                                 │
│                    (Routes messages)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ RPC Call
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                        PYTHON AGENT                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Tool Functions                             │   │
│  │  • Defined with @llm.function_tool                           │   │
│  │  • Called by LLM during conversation                         │   │
│  │  • Sends overlay via send_overlay()                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. File Structure Template

```
your-project/
│
├── Agent/
│   ├── agent.py              # Main agent file
│   │   ├── send_overlay()    # Helper function to send overlays
│   │   ├── @llm.function_tool # Tool definitions
│   │   └── YourAgent class   # Agent with tools list
│   │
│   └── .env                  # API keys and configuration
│
├── components/
│   ├── RoomComponent.tsx     # RPC bridge - registers methods
│   └── OverlayComponent.tsx  # UI rendering - all overlay types
│
└── app/
    └── page.tsx              # Main page with LiveKitRoom
```

### File Responsibilities

| File | Modify When | Contains |
|------|-------------|----------|
| `agent.py` | Adding new tools | Tool definitions, send_overlay helper |
| `RoomComponent.tsx` | Adding new RPC methods | RPC registration, state management |
| `OverlayComponent.tsx` | Adding new overlay types or styling | Interface, switch cases, UI components |

---

## 4. Data Flow

### Complete Data Journey

```
Step 1: User speaks
        ↓
Step 2: Speech → Text (STT)
        ↓
Step 3: Text → LLM processes
        ↓
Step 4: LLM calls tool function
        ↓
Step 5: Tool creates data payload
        ↓
Step 6: send_overlay() creates JSON
        ↓
Step 7: perform_rpc() sends to frontend
        ↓
Step 8: RPC handler receives payload
        ↓
Step 9: setOverlay() updates React state
        ↓
Step 10: Component re-renders with data
        ↓
Step 11: User sees overlay on screen
```

### Data Payload Structure

Every overlay uses this structure:

```json
{
    "type": "your-overlay-type",
    "title": "Card Title",
    "subtitle": "Optional subtitle",
    "source": "Optional footer reference",
    "data": {
        // Type-specific data goes here
        // Structure depends on overlay type
    }
}
```

---

## 5. Python Agent Configuration

### 5.1 send_overlay() Helper Function

Place this function in your agent file. It handles all RPC communication:

```python
import json
import logging
from livekit.agents import get_job_context

logger = logging.getLogger("your-agent-name")

async def send_overlay(
    overlay_type: str,
    title: str,
    data: dict,
    subtitle: str = "",
    source: str = ""
) -> bool:
    """
    Send overlay data to frontend via RPC.
    
    Parameters:
        overlay_type: Identifier matching switch case in TSX.
                      Examples: "data-table", "step-guide", "alert-card"
        
        title: Main heading (max 50 chars recommended).
        
        data: Dictionary with type-specific content.
              Will be JSON serialized.
        
        subtitle: Optional secondary heading.
        
        source: Optional footer citation.
    
    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        room = get_job_context().room
        participant = next(iter(room.remote_participants.keys()), None)
        
        if not participant:
            logger.warning("No participant connected")
            return False
        
        payload = json.dumps({
            "type": overlay_type,
            "title": title,
            "subtitle": subtitle,
            "source": source,
            "data": data
        })
        
        await room.local_participant.perform_rpc(
            destination_identity=participant,
            method="showOverlay",
            payload=payload,
            response_timeout=5.0,
        )
        
        logger.info(f"Overlay sent: {overlay_type}")
        return True
        
    except Exception as e:
        logger.error(f"Overlay error: {e}")
        return False


async def hide_overlay() -> bool:
    """Hide the currently displayed overlay."""
    try:
        room = get_job_context().room
        participant = next(iter(room.remote_participants.keys()), None)
        
        if not participant:
            return False
        
        await room.local_participant.perform_rpc(
            destination_identity=participant,
            method="hideOverlay",
            payload="{}",
            response_timeout=5.0,
        )
        return True
        
    except Exception as e:
        logger.error(f"Hide overlay error: {e}")
        return False
```

### 5.2 Tool Definition Template

```python
from livekit.agents import llm

@llm.function_tool
async def your_tool_name(
    # Parameters - ONLY these types allowed:
    text_param: str,           # Text
    number_param: int,         # Whole number
    decimal_param: float,      # Decimal
    flag_param: bool,          # True/False
    optional_param: str = "",  # Optional with default
    complex_json: str = ""     # For dict/list data
) -> str:
    """
    Brief description of what this tool does.
    
    When to use:
    - Situation 1
    - Situation 2
    
    Args:
        text_param: Description and example
        number_param: Description and example
        complex_json: JSON string. Example: {"key": "value"}
    
    Returns:
        Confirmation message for the LLM
    """
    try:
        # Parse JSON parameters
        complex_data = json.loads(complex_json) if complex_json else {}
        
        # Build overlay data
        overlay_data = {
            "field1": text_param,
            "field2": number_param,
            "items": complex_data.get("items", [])
        }
        
        # Send to frontend
        success = await send_overlay(
            overlay_type="your-type",
            title=f"Title: {text_param}",
            subtitle="Subtitle here",
            source="Reference",
            data=overlay_data
        )
        
        return "Displayed successfully" if success else "Display failed"
        
    except json.JSONDecodeError:
        return "Error: Invalid JSON"
    except Exception as e:
        return f"Error: {e}"
```

### 5.3 Parameter Type Rules

**CRITICAL:** OpenAI function calling rejects complex types.

| Type | Allowed | Solution |
|------|---------|----------|
| `str` | ✅ | Direct use |
| `int` | ✅ | Direct use |
| `float` | ✅ | Direct use |
| `bool` | ✅ | Direct use |
| `dict` | ❌ | Use `str` + `json.loads()` |
| `list` | ❌ | Use `str` + `json.loads()` |
| `Any` | ❌ | Use `str` + `json.loads()` |

**Pattern for complex data:**

```python
# Define parameter as string
async def tool(data_json: str = "{}") -> str:
    # Parse inside function
    data = json.loads(data_json)
```

### 5.4 Registering Tools with Agent

```python
from livekit.agents import Agent

class YourAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="Your agent instructions...",
            tools=[
                tool_1,
                tool_2,
                your_new_tool,  # Add new tools here
            ],
        )
    
    async def on_enter(self):
        # Greeting when conversation starts
        await self.session.generate_reply(
            instructions="Greet the user",
            allow_interruptions=True,
        )
```

---

## 6. RPC Bridge Setup

### 6.1 Room Component Template

```tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRoomContext } from "@livekit/components-react";
import { RpcInvocationData } from "livekit-client";
import { OverlayComponent, OverlayData } from "./OverlayComponent";

export function RoomComponent() {
    const room = useRoomContext();
    const [overlay, setOverlay] = useState<OverlayData | null>(null);

    // RPC Registration
    useEffect(() => {
        if (!room) return;

        const handleShowOverlay = async (data: RpcInvocationData) => {
            try {
                const parsed = JSON.parse(data.payload) as OverlayData;
                setOverlay(parsed);
                return JSON.stringify({ success: true });
            } catch (error) {
                console.error("Overlay parse error:", error);
                return JSON.stringify({ success: false });
            }
        };

        const handleHideOverlay = async () => {
            setOverlay(null);
            return JSON.stringify({ success: true });
        };

        room.registerRpcMethod("showOverlay", handleShowOverlay);
        room.registerRpcMethod("hideOverlay", handleHideOverlay);

        return () => {
            room.unregisterRpcMethod("showOverlay");
            room.unregisterRpcMethod("hideOverlay");
        };
    }, [room]);

    const handleDismiss = useCallback(() => {
        setOverlay(null);
    }, []);

    return (
        <div className="relative w-full h-[100dvh]">
            
            {/* Your main content here */}
            
            {/* Overlay positioned on right side */}
            <div className="absolute inset-0 z-30 flex items-center justify-end p-6 pointer-events-none">
                <div className="pointer-events-auto max-w-md w-full">
                    <OverlayComponent 
                        overlay={overlay}
                        onDismiss={handleDismiss}
                    />
                </div>
            </div>
            
        </div>
    );
}
```

### 6.2 Overlay Positioning Options

| Position | CSS Classes |
|----------|-------------|
| Right center (default) | `flex items-center justify-end p-6` |
| Right top | `flex items-start justify-end p-6` |
| Right bottom | `flex items-end justify-end p-6` |
| Left center | `flex items-center justify-start p-6` |
| Center | `flex items-center justify-center p-6` |
| Full width bottom | `flex items-end justify-center p-6` then `w-full max-w-4xl` on overlay |

---

## 7. Overlay Component Design

### 7.1 Data Interface

```tsx
export interface OverlayData {
    type: string;  // Add your types as union: 'type-a' | 'type-b' | ...
    title: string;
    subtitle?: string;
    source?: string;
    data: Record<string, unknown>;
}

interface OverlayProps {
    overlay: OverlayData | null;
    onDismiss: () => void;
}
```

### 7.2 Main Container Template

```tsx
export function OverlayComponent({ overlay, onDismiss }: OverlayProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (overlay) {
            requestAnimationFrame(() => setIsVisible(true));
        } else {
            setIsVisible(false);
        }
    }, [overlay]);

    if (!overlay) return null;

    const handleDismiss = () => {
        setIsVisible(false);
        setTimeout(onDismiss, 300);
    };

    return (
        <div 
            className={`
                fixed top-1/2 right-8 -translate-y-1/2
                w-[750px] max-w-[90vw] max-h-[600px]
                bg-white border-2 border-black
                shadow-[6px_6px_0px_0px_#000]
                flex flex-col overflow-hidden
                transition-all duration-300 ease-out
                ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'}
            `}
            style={{ fontFamily: 'monospace, "Courier New", Courier' }}
        >
            {/* Header - Uses CSS variable for accent color */}
            <div 
                className="text-black px-6 py-3 border-b-2 border-black"
                style={{ backgroundColor: 'var(--pink-accent, #FF0055)' }}
            >
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="text-lg font-bold tracking-wide uppercase">
                            {overlay.title}
                        </h3>
                        {overlay.subtitle && (
                            <p className="text-sm mt-0.5 opacity-80">{overlay.subtitle}</p>
                        )}
                    </div>
                    <button 
                        onClick={handleDismiss} 
                        className="ml-4 w-7 h-7 bg-black text-white font-bold"
                    >
                        ×
                    </button>
                </div>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto flex-1 bg-gray-50" style={{ maxHeight: '440px' }}>
                {renderContent(overlay)}
            </div>

            {/* Footer */}
            {overlay.source && (
                <div className="px-6 py-3 border-t-2 border-black bg-white">
                    <p className="text-xs text-black uppercase tracking-wide">
                        <span className="font-bold">Reference:</span> {overlay.source}
                    </p>
                </div>
            )}
        </div>
    );
}
```

### 7.3 Content Router

```tsx
function renderContent(overlay: OverlayData) {
    switch (overlay.type) {
        case 'data-table':
            return <DataTableContent data={overlay.data} />;
        
        case 'step-guide':
            return <StepGuideContent data={overlay.data} />;
        
        case 'alert-card':
            return <AlertCardContent data={overlay.data} />;
        
        // Add more cases as needed
        
        default:
            return <pre>{JSON.stringify(overlay.data, null, 2)}</pre>;
    }
}
```

### 7.4 Content Component Template

```tsx
interface ContentProps {
    data: Record<string, unknown>;
}

function YourContentComponent({ data }: ContentProps) {
    // 1. Extract and cast data
    const title = (data.title as string) || '';
    const items = (data.items as Array<{ key: string; value: string }>) || [];
    const note = (data.note as string) || '';

    // 2. Render UI
    return (
        <div className="space-y-4">
            {/* Add your UI elements */}
        </div>
    );
}
```

---

## 8. Planning Your Overlays

### 8.1 Planning Template

Before coding, define each overlay:

```markdown
## Overlay: [Name]

### Purpose
What information does this overlay display?
When should the agent show this?

### Data Structure
{
    "field1": "string description",
    "field2": "number description",
    "items": [
        { "name": "string", "value": "string" }
    ]
}

### UI Layout
- Header: [title pattern]
- Sections:
  1. [Section name] - [description]
  2. [Section name] - [description]
- Footer: [source pattern]

### Example
{
    "type": "your-type",
    "title": "Example Title",
    "data": {
        "field1": "Example value",
        "items": [{"name": "Item 1", "value": "100"}]
    }
}
```

### 8.2 Domain-Specific Examples

**Finance:**
- Account Summary (balance, transactions, alerts)
- Investment Portfolio (holdings, performance)
- Payment Confirmation (amount, recipient, status)

**Retail:**
- Product Comparison (features, prices, ratings)
- Order Status (items, tracking, delivery)
- Inventory Check (stock levels, locations)

**Healthcare:**
- Appointment Summary (date, doctor, location)
- Medication Schedule (drugs, dosage, times)
- Test Results (values, normal ranges, flags)

---

## 9. Styling Guidelines

### 9.1 Global Theme (CSS Variables)

The overlay system uses CSS variables defined in `globals.css` for consistent theming:

```css
:root {
  --pink-accent: #FF0055;       /* Primary accent color */
  --border-color: #000;          /* Black borders */
  --bg-color: #fff;              /* White backgrounds */
  --font-sans: monospace, system-ui, sans-serif;
}
```

**Key Design Principles:**
- **Industrial/Brutalist aesthetic** - Sharp corners, solid black borders
- **Monospace typography** - Technical, machine-like appearance
- **Solid black box-shadows** - `6px 6px 0px 0px #000` (not blurred)
- **Uppercase headings** - Bold, high-visibility text

### 9.2 Standard Component Patterns

| Element | Styling |
|---------|---------|
| **Card container** | `bg-white border-2 border-black shadow-[6px_6px_0px_0px_#000]` |
| **Header** | `style={{ backgroundColor: 'var(--pink-accent, #FF0055)' }}` + `text-black` |
| **Table header** | `style={{ backgroundColor: 'var(--pink-accent, #FF0055)' }}` + `text-black font-bold` |
| **Table row alt** | `className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}` |
| **Accent box** | `bg-pink-50 border-l-4 p-4` + `style={{ borderColor: 'var(--pink-accent)' }}` |
| **Warning box** | `bg-yellow-50 border-l-4 border-yellow-500 p-4` |
| **Error box** | `bg-red-50 border-l-4 border-red-500 p-4` |
| **Success box** | `bg-green-50 border-l-4 border-green-500 p-4` |
| **Close button** | `bg-black text-white w-7 h-7 font-bold` |
| **Font** | `style={{ fontFamily: 'monospace' }}` |
| **Headings** | `uppercase tracking-wide font-bold text-black` |

### 9.3 Main Container Template (Theme-Aligned)

```tsx
<div className={`
    fixed top-1/2 right-8 -translate-y-1/2
    w-[750px] max-w-[90vw] max-h-[600px]
    bg-white border-2 border-black
    shadow-[6px_6px_0px_0px_#000]
    flex flex-col overflow-hidden
    transition-all duration-300 ease-out
`}
    style={{ fontFamily: 'monospace, "Courier New", Courier' }}
>
    {/* Header - Uses CSS variable */}
    <div 
        className="text-black px-6 py-3 border-b-2 border-black"
        style={{ backgroundColor: 'var(--pink-accent, #FF0055)' }}
    >
        <h3 className="text-lg font-bold tracking-wide uppercase">
            {title}
        </h3>
    </div>
    
    {/* Body */}
    <div className="p-6 overflow-y-auto flex-1 bg-gray-50">
        {content}
    </div>
    
    {/* Footer */}
    <div className="px-6 py-3 border-t-2 border-black bg-white">
        <p className="text-xs text-black uppercase tracking-wide">
            <span className="font-bold">Reference:</span> {source}
        </p>
    </div>
</div>
```

### 9.4 Table Template (Theme-Aligned)

```tsx
<table className="w-full text-sm border-2 border-black">
    <thead style={{ backgroundColor: 'var(--pink-accent, #FF0055)' }}>
        <tr>
            <th className="px-3 py-2 text-left font-bold text-black border-r border-black">
                Column 1
            </th>
            <th className="px-3 py-2 text-left font-bold text-black">
                Column 2
            </th>
        </tr>
    </thead>
    <tbody className="bg-white">
        {items.map((item, idx) => (
            <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                <td className="px-3 py-2 font-semibold border-r border-gray-200">
                    {item.name}
                </td>
                <td className="px-3 py-2">{item.value}</td>
            </tr>
        ))}
    </tbody>
</table>
```

### 9.5 Accent Box Template (Theme-Aligned)

```tsx
<div 
    className="bg-pink-50 border-l-4 p-4" 
    style={{ borderColor: 'var(--pink-accent, #FF0055)' }}
>
    <h4 className="text-base font-bold text-black mb-2 uppercase">
        Section Title
    </h4>
    <p className="text-sm text-gray-800">
        Content here
    </p>
</div>
```

### 9.6 Status Colors (Semantic)

```tsx
const statusColors = {
    pass: 'bg-green-100 text-green-800',
    fail: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    neutral: 'bg-gray-100 text-gray-800',
};
```

### 9.7 Customizing for Different Domains

To change the accent color for different projects, update `globals.css`:

```css
/* Finance theme */
:root {
  --pink-accent: #10B981;  /* Emerald green */
}

/* Retail theme */
:root {
  --pink-accent: #F97316;  /* Orange */
}

/* Healthcare theme */
:root {
  --pink-accent: #14B8A6;  /* Teal */
}

/* Corporate theme */
:root {
  --pink-accent: #3B82F6;  /* Blue */
}
```

The variable name `--pink-accent` can remain unchanged (for compatibility) or be renamed to `--accent-color`.

---

## 10. Testing Checklist

```
□ Python agent starts without errors
□ Tool appears in LLM's available tools
□ Tool is called when triggered by speech
□ send_overlay() logs success
□ RPC method receives payload
□ Overlay state updates in React
□ Correct switch case handles type
□ UI renders with correct data
□ Dismiss button works
□ Styling matches design
```

### Debug Logging

**Python:**
```python
logger.info(f"Tool called with: {param}")
logger.info(f"Sending overlay: {json.dumps(data)}")
```

**TypeScript:**
```tsx
console.log("Overlay received:", overlay);
console.log("Rendering type:", overlay.type);
```

---

## 11. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `additionalProperties is required` | `dict`/`list` parameter | Use `str` + `json.loads()` |
| Overlay not appearing | Type mismatch | Match Python `overlay_type` with TSX `case` |
| "No participant connected" | User not in room | Wait for connection |
| Blank content | Data extraction error | Check type casting |
| Tool not called by LLM | Not in tools list | Add to `tools=[...]` |
| RPC timeout | Frontend not receiving | Verify RPC registration |

---

## Quick Reference

```
┌────────────────────────────────────────────────────────────────┐
│                    NEW OVERLAY CHECKLIST                        │
├────────────────────────────────────────────────────────────────┤
│ 1. PLAN: Define data structure and UI layout                   │
│ 2. PYTHON: Create @llm.function_tool                           │
│ 3. PYTHON: Use str params + json.loads() for complex data      │
│ 4. PYTHON: Call send_overlay() with unique type                │
│ 5. PYTHON: Add tool to Agent tools list                        │
│ 6. TSX: Add type to OverlayData interface (optional)           │
│ 7. TSX: Add case to renderContent switch                       │
│ 8. TSX: Create content component with styling                  │
│ 9. TEST: Restart agent, refresh browser, test with voice       │
└────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Maintainer:** Development Team
