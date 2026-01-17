# RPC Connection & Overlay System

This document outlines the Remote Procedure Call (RPC) connection used to control the Frontend UI from the Python Agent.

## 🔗 Architecture

**Protocol**: standard LiveKit Data Channel RPC.  
**Direction**: Agent (Backend) → Client (React Frontend).

### 1. Backend (`agent.py`)

The agent sends RPC/Data messages to the connected user's `participant_identity`.

```python
await room.local_participant.perform_rpc(
    destination_identity=participant_identity,
    method="showOverlay",  # or "hideOverlay"
    payload=json.dumps({
        "type": "info",
        "title": "Title",
        "subtitle": "Subtitle",
        "source": "Source",
        "data": { ... }
    }),
    response_timeout=5.0
)
```

### 2. Frontend (`AvatarRoom.tsx`)

The frontend registers an RPC method listener locally.

```typescript
useLocalParticipant().localParticipant.registerRpcMethod(
    "showOverlay", 
    async (data: RpcInvocationData) => {
        const payload = JSON.parse(data.payload);
        setOverlay(payload); // Updates React State -> OverlayCard
    }
);
```

---

## 📦 Payload Schemas

The `data` field in the payload changes based on `type`.

### `info` (Simple Text)
```json
{
  "type": "info",
  "data": {
    "text": "The engine operates at 5000 RPM.",
    "icon": "⚙️"
  }
}
```

### `value-grid` (Dashboard)
```json
{
  "type": "value-grid",
  "data": {
    "values": [
      {"label": "Temperature", "value": "98°C", "unit": "Celsius"},
      {"label": "Pressure", "value": "120", "unit": "PSI"}
    ]
  }
}
```

### `comparison` (Table)
```json
{
  "type": "comparison",
  "data": {
    "items": [
      {"name": "Model A", "specs": {"Speed": "Fast", "Price": "$100"}},
      {"name": "Model B", "specs": {"Speed": "Faster", "Price": "$200"}}
    ]
  }
}
```

### `alert` (Notifications)
```json
{
  "type": "alert",
  "data": {
    "message": "System Check Complete",
    "icon": "✅",
    "items": ["Check 1 Passed", "Check 2 Passed"]
  }
}
```

### `product` (E-commerce)
```json
{
  "type": "product",
  "data": {
    "name": "Super Widget",
    "price": "$19.99",
    "image": "https://...",
    "specs": {"Color": "Red", "Size": "M"}
  }
}
```

### `image` (KB Diagrams / Photos)
```json
{
  "type": "image",
  "data": {
    "image": "data:image/png;base64,iVBORw0KGgo...", 
    "caption": "Figure 1: Diagram",
    "text": "Optional description text."
  }
}
```

---

## 🛠️ Usage in Agent

To trigger these from the AI:
1. Define a tool function (e.g., `show_status`).
2. Construct the JSON.
3. Call `show_overlay` (if using the helper tool) OR `perform_rpc` directly.

**Example Tool:**
```python
@llm.function_tool
async def show_engine_status():
    await show_overlay(
        overlay_type="value-grid",
        title="Engine Status",
        content=json.dumps({
            "values": [{"label": "RPM", "value": "3000"}]
        })
    )
    return "Displaying status."
```
