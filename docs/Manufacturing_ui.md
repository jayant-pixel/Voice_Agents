# General Overlay Card System - Clean Data Display
## One Universal Card + Pure Information Examples (No CTAs, No Forms)

---

## 🎯 GENERAL CARD STRUCTURE

### **Universal Card Template (Applies to All Content Types)**

```
┌──────────────────────────────────────┐
│ HEADER                               │  ← Always present
│ • Title                              │
│ • Context info (material, machine)   │
│ • Source reference                   │
├──────────────────────────────────────┤
│                                       │
│ BODY                                 │  ← Dynamic content area
│ • Content changes based on data type │
│ • Layout adapts to content           │
│ • Scrollable if needed               │
│                                       │
└──────────────────────────────────────┘

Note: No footer, no action buttons
Pure information display only
```

---

## 📐 POSITIONING & SIZE

```css
/* Card positioning - Brutalist Style */
.overlay-card {
  position: fixed;
  bottom: 40px;
  right: 40px;
  
  /* Dynamic width based on content */
  width: var(--card-width); /* 350px - 700px */
  max-width: 90vw;
  max-height: calc(100vh - 80px);
  
  background: #fff;
  border-radius: 0; /* Brutalist - no rounded corners */
  border: 1px solid #000;
  box-shadow: 6px 6px 0px 0px #000; /* Brutalist offset shadow */
}

/* Responsive */
@media (max-width: 1023px) {
  .overlay-card {
    bottom: 20px;
    right: 20px;
    left: 20px;
    width: auto;
  }
}
```

---

## 🎨 GENERAL CARD TEMPLATE (CSS)

```css
/* ============================================
   UNIVERSAL CARD STRUCTURE - Brutalist Style
   ============================================ */

:root {
  --border-color: #000;
  --bg-color: #fff;
  --gray-text: #666;
  --pink-accent: #FF0055;
  --font-sans: system-ui, -apple-system, sans-serif;
  --font-mono: monospace;
}

.overlay-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: var(--font-sans);
}

/* HEADER - Fixed */
.overlay-header {
  background: var(--pink-accent);
  color: #000;
  padding: 20px 24px;
  flex-shrink: 0;
  border-bottom: 1px solid #000;
}

.header-title {
  font-family: var(--font-mono);
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.header-context {
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.header-source {
  font-size: 0.75rem;
  opacity: 0.8;
  font-style: italic;
}

/* BODY - Scrollable */
.overlay-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  background: #F8F8F6;
}

/* Custom scrollbar */
.overlay-body::-webkit-scrollbar {
  width: 8px;
}

.overlay-body::-webkit-scrollbar-track {
  background: #f4f4f4;
}

.overlay-body::-webkit-scrollbar-thumb {
  background: #000;
  border-radius: 0;
}
```

---

## 📊 EXAMPLE 1: QUICK LOOKUP (Compact Card)

**Query**: "What die for 0.35mm wire?"

**Card Width**: `400px`

```markdown
┌────────────────────────────────────────┐
│ 🔧 Die & Nozzle Selection              │
│ Wire Size: 0.35mm                      │
│ Source: DDR Chart-3, Row 3             │
├────────────────────────────────────────┤
│                                         │
│  Wire Size: 0.3-0.35mm                 │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │ Die ID: 9 or 10                 │  │
│  │                                  │  │
│  │ Nozzle OD: 4.5                  │  │
│  │                                  │  │
│  │ Nozzle ID: 0.8 or 1             │  │
│  │                                  │  │
│  │ Thickness Options:               │  │
│  │ • 0.32mm (standard)              │  │
│  │ • 0.25mm (thinner)               │  │
│  └─────────────────────────────────┘  │
│                                         │
│  Adjacent Wire Sizes:                  │
│  • 0.25-0.3mm: Same configuration      │
│  • 0.35-0.4mm: Die 10, Nozzle ID 1     │
│                                         │
└────────────────────────────────────────┘

Layout Type: quick-lookup
Data Extracted: 1 row + adjacent context
Card Dimensions: 400px × ~320px
```

---

## 📊 EXAMPLE 2: PARAMETER DISPLAY (Medium Card)

**Query**: "Temperature settings for ETFE"

**Card Width**: `550px`

```markdown
┌──────────────────────────────────────────────┐
│ 🌡️  Temperature Settings                    │
│ Material: ETFE | Machine: ROSENDAHL          │
│ Source: TPL-TD-28, Page 1                    │
├──────────────────────────────────────────────┤
│                                               │
│  Zone Temperatures (°C):                     │
│                                               │
│  ┌──────────┬──────────┬──────────┐         │
│  │ Z1       │ Z2       │ Z3       │         │
│  │ 280°C    │ 290°C    │ 310°C    │         │
│  │ 260-300  │ 270-310  │ 290-330  │         │
│  └──────────┴──────────┴──────────┘         │
│                                               │
│  ┌──────────┬──────────┬──────────┐         │
│  │ Z4       │ Flange   │ H1       │         │
│  │ 330°C    │ 340°C    │ 350°C    │         │
│  │ 310-350  │ 320-360  │ 330-370  │         │
│  └──────────┴──────────┴──────────┘         │
│                                               │
│  ┌──────────┬──────────┐                     │
│  │ H2       │ Die      │                     │
│  │ 360°C    │ 370°C    │                     │
│  │ 340-380  │ 350-390  │                     │
│  └──────────┴──────────┘                     │
│                                               │
│  Auxiliary Settings:                         │
│  • Water Cooling: 40°C (±10°C)               │
│  • Tolerance: ±20°C on all zones             │
│  • Gap Distance: 0.5-1.5 meters              │
│                                               │
└──────────────────────────────────────────────┘

Layout Type: parameter-grid
Data Extracted: ETFE row only (8 zones)
Card Dimensions: 550px × ~480px
Grid Layout: 3-3-2 arrangement
```

---

## 📊 EXAMPLE 3: SINGLE VALUE (Extra Compact)

**Query**: "What's Z3 temperature for ETFE?"

**Card Width**: `350px`

```markdown
┌──────────────────────────────┐
│ 🌡️  Z3 Temperature           │
│ Material: ETFE               │
│ Source: TPL-TD-28            │
├──────────────────────────────┤
│                               │
│         310°C                 │
│                               │
│  Acceptable Range:            │
│  290°C - 330°C                │
│                               │
│  Tolerance: ±20°C             │
│                               │
└──────────────────────────────┘

Layout Type: single-value
Data Extracted: 1 cell + tolerance
Card Dimensions: 350px × ~200px
Display: Centered, large text
```

---

## 📊 EXAMPLE 4: COMPARISON DATA (Wide Card)

**Query**: "Compare ETFE and FEP temperatures"

**Card Width**: `650px`

```markdown
┌────────────────────────────────────────────────────────┐
│ ⚖️  Temperature Comparison                             │
│ ETFE vs FEP | Machine: ROSENDAHL                       │
│ Source: TPL-TD-28                                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────┬────────┬────────┬──────────┐             │
│  │ Zone   │ ETFE   │ FEP    │ Status   │             │
│  ├────────┼────────┼────────┼──────────┤             │
│  │ Z1     │ 280°C  │ 280°C  │ Same ✓   │             │
│  │ Z2     │ 290°C  │ 290°C  │ Same ✓   │             │
│  │ Z3     │ 310°C  │ 310°C  │ Same ✓   │             │
│  │ Z4     │ 330°C  │ 330°C  │ Same ✓   │             │
│  │ Flange │ 340°C  │ 340°C  │ Same ✓   │             │
│  │ H1     │ 350°C  │ 350°C  │ Same ✓   │             │
│  │ H2     │ 360°C  │ 360°C  │ Same ✓   │             │
│  │ Die    │ 370°C  │ 370°C  │ Same ✓   │             │
│  └────────┴────────┴────────┴──────────┘             │
│                                                         │
│  Water Cooling:                                        │
│  • ETFE: 40°C (±10°C)                                 │
│  • FEP:  40°C (±10°C)  ✓ Same                         │
│                                                         │
│  💡 Analysis:                                          │
│  All temperature parameters are identical.             │
│  Materials are interchangeable for this machine.       │
│                                                         │
└────────────────────────────────────────────────────────┘

Layout Type: comparison-table
Data Extracted: 2 rows (ETFE, FEP), temp columns only
Card Dimensions: 650px × ~480px
Table: 4 columns, 8 rows + summary
```

---

## 📊 EXAMPLE 5: RANGE/SPECIFICATION (Compact)

**Query**: "Water cooling temperature range"

**Card Width**: `420px`

```markdown
┌─────────────────────────────────────┐
│ 💧 Water Cooling Temperature        │
│ Material: ETFE | Machine: ROSENDAHL │
│ Source: TPL-TD-28                   │
├─────────────────────────────────────┤
│                                      │
│  Target Temperature:                │
│         40°C                         │
│                                      │
│  Acceptable Range:                  │
│  ┌────────────────────────────────┐ │
│  │ Minimum: 30°C                  │ │
│  │ Target:  40°C   ← Standard     │ │
│  │ Maximum: 50°C                  │ │
│  └────────────────────────────────┘ │
│                                      │
│  Tolerance: ±10°C                   │
│                                      │
│  Gap to Hot Water Zone:             │
│  0.5 - 1.5 meters                   │
│                                      │
└─────────────────────────────────────┘

Layout Type: range-display
Data Extracted: Single parameter with range
Card Dimensions: 420px × ~320px
Visual: Range bar with target marker
```

---

## 📊 EXAMPLE 6: SAFETY INFORMATION (Alert Style)

**Query**: "What's different with PFA material?"

**Card Width**: `500px`

```markdown
┌─────────────────────────────────────────┐
│ ⚠️  Material-Specific Requirements      │
│ Material: PFA                           │
│ Source: Inner Extrusion WI, Note 9      │
├─────────────────────────────────────────┤
│                                          │
│          ⚠️                              │
│                                          │
│  🚫 DO NOT USE WATER COOLING            │
│                                          │
│  Critical Differences from ETFE/FEP:    │
│                                          │
│  ❌ Water circulation must be OFF       │
│  ❌ Gap distance does not apply         │
│  ❌ Different cooling method required   │
│                                          │
│  ✅ Temperature: 320-390°C (higher)     │
│  ✅ Pre-heater: 80-100% (higher)        │
│  ✅ No water bath needed                │
│                                          │
│  Reference Note:                         │
│  "For PFA insulation don't use water"   │
│                                          │
└─────────────────────────────────────────┘

Layout Type: alert-information
Data Extracted: Material-specific warnings
Card Dimensions: 500px × ~380px
Style: Yellow/amber background (#FEF3C7)
Border: 3px solid #F59E0B
```

---

## 📊 EXAMPLE 7: ADJACENT DATA CONTEXT (Smart Lookup)

**Query**: "Die for 0.4mm wire"

**Card Width**: `480px`

```markdown
┌──────────────────────────────────────────┐
│ 🔧 Die & Nozzle Selection                │
│ Wire Size: 0.4mm                         │
│ Source: DDR Chart-3                      │
├──────────────────────────────────────────┤
│                                           │
│  Wire Size: 0.35-0.4mm                   │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │ Die ID: 10                          │ │
│  │ Nozzle OD: 4.5                      │ │
│  │ Nozzle ID: 1                        │ │
│  │ Thickness: 0.32 or 0.25             │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  Adjacent Wire Sizes:                    │
│                                           │
│  Previous (0.3-0.35mm):                  │
│  • Die: 9 or 10                          │
│  • Nozzle ID: 0.8 or 1                   │
│                                           │
│  Next (0.41-0.45mm):                     │
│  • Die: 10 (same)                        │
│  • Nozzle ID: 1 (same)                   │
│                                           │
│  💡 Note: If wire diameter varies        │
│     between 0.35-0.45mm, Die 10          │
│     covers the entire range.             │
│                                           │
└──────────────────────────────────────────┘

Layout Type: lookup-with-context
Data Extracted: 1 main row + 2 adjacent rows
Card Dimensions: 480px × ~380px
Context: ±1 wire size for variance handling
```

---

## 📊 EXAMPLE 8: MULTI-PARAMETER LOOKUP

**Query**: "ETFE water temperature and gap"

**Card Width**: `460px`

```markdown
┌────────────────────────────────────┐
│ 💧 Water System Settings           │
│ Material: ETFE | ROSENDAHL         │
│ Source: TPL-TD-28                  │
├────────────────────────────────────┤
│                                     │
│  Water Cooling Temperature:        │
│  ┌──────────────────────────────┐ │
│  │ Target:  40°C                │ │
│  │ Range:   30-50°C             │ │
│  │ Tolerance: ±10°C             │ │
│  └──────────────────────────────┘ │
│                                     │
│  Gap Distance:                     │
│  ┌──────────────────────────────┐ │
│  │ From head to hot water zone  │ │
│  │ Required: 0.5 - 1.5 meters   │ │
│  └──────────────────────────────┘ │
│                                     │
│  Critical Note:                    │
│  Water circulation for barrel      │
│  must be ON during extrusion       │
│                                     │
└────────────────────────────────────┘

Layout Type: multi-parameter
Data Extracted: 2 related parameters
Card Dimensions: 460px × ~340px
Grouping: Related settings together
```

---

## 🎨 CONTENT LAYOUT TYPES (CSS Components)

### **Type 1: Value Grid (2-3 columns)**

```css
.value-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.value-box {
  background: #fff;
  padding: 16px;
  border-radius: 0;
  border: 1px solid #000;
  box-shadow: 3px 3px 0px 0px #000;
  text-align: center;
}

.value-label {
  font-family: monospace;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #666;
  margin-bottom: 4px;
}

.value-number {
  font-size: 1.5rem;
  font-weight: 800;
  color: #000;
}

.value-range {
  font-size: 0.75rem;
  color: #666;
  margin-top: 4px;
}
```

### **Type 2: Comparison Table**

```css
.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  border: 1px solid #000;
}

.comparison-table th {
  background: var(--pink-accent);
  padding: 10px 12px;
  text-align: left;
  font-family: monospace;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #000;
  border-bottom: 1px solid #000;
}

.comparison-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #000;
  background: #fff;
}

.comparison-table .match-icon {
  color: #000;
  font-weight: 800;
}
```

### **Type 3: Alert Box**

```css
.alert-box {
  background: #fff;
  border: 2px solid #000;
  border-left: 6px solid var(--pink-accent);
  border-radius: 0;
  padding: 20px;
  box-shadow: 4px 4px 0px 0px #000;
}

.alert-icon {
  font-size: 32px;
  text-align: center;
  margin-bottom: 12px;
}

.alert-title {
  font-family: monospace;
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #000;
  margin-bottom: 12px;
}

.alert-item {
  padding: 6px 0;
  padding-left: 28px;
  position: relative;
  font-size: 0.85rem;
  color: #000;
}

.alert-item::before {
  position: absolute;
  left: 0;
  font-weight: bold;
  font-size: 16px;
}

.alert-item.do::before {
  content: '✅';
}

.alert-item.dont::before {
  content: '❌';
}
```

### **Type 4: Single Large Value**

```css
.single-value-display {
  text-align: center;
  padding: 32px 24px;
}

.single-value-main {
  font-size: 3.5rem;
  font-weight: 800;
  color: #000;
  margin-bottom: 16px;
  line-height: 1;
}

.single-value-label {
  font-family: monospace;
  font-size: 0.7rem;
  font-weight: 700;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 20px;
}

.single-value-range {
  display: inline-block;
  background: #fff;
  padding: 12px 20px;
  border: 1px solid #000;
  border-radius: 0;
  box-shadow: 3px 3px 0px 0px #000;
  font-size: 0.9rem;
  color: #000;
}
```

---

## 🔄 DYNAMIC CARD SIZING

```javascript
// Card automatically adjusts width based on content type
const cardSizes = {
  'single-value': '350px',
  'quick-lookup': '400px',
  'range-display': '420px',
  'multi-parameter': '460px',
  'lookup-with-context': '480px',
  'alert-information': '500px',
  'parameter-grid': '550px',
  'comparison-table': '650px'
};

function showOverlay(data) {
  const cardWidth = cardSizes[data.layoutType];
  
  document.querySelector('.overlay-card').style.setProperty(
    '--card-width', 
    cardWidth
  );
  
  renderContent(data);
}
```

---

## 📏 CARD SIZE REFERENCE

| Layout Type | Width | Height | Best For |
|-------------|-------|--------|----------|
| single-value | 350px | ~200px | Z3 temp |
| quick-lookup | 400px | ~320px | Die/nozzle |
| range-display | 420px | ~320px | Water temp range |
| multi-parameter | 460px | ~340px | Water + gap |
| lookup-with-context | 480px | ~380px | Wire size lookup |
| alert-information | 500px | ~380px | PFA warning |
| parameter-grid | 550px | ~480px | All temp zones |
| comparison-table | 650px | ~480px | Material compare |

---

## 🎯 KEY PRINCIPLES

1. **No Action Buttons** - Pure information display only
2. **No Forms** - Read-only data presentation
3. **Focused Extraction** - Show only relevant row/columns
4. **Minimal Context** - Adjacent data only when helpful
5. **Clean Layout** - Header + Body (no footer)
6. **Smart Sizing** - Card width adapts to content (350-650px)
7. **Source Attribution** - Always show where data came from

---

## ✅ FINAL STRUCTURE SUMMARY

```
GENERAL CARD (Universal):
├─ Header (Fixed)
│  ├─ Icon + Title
│  ├─ Context (material, machine, wire size)
│  └─ Source reference (document, page)
│
└─ Body (Dynamic)
   └─ Content Layout (adapts to data type):
      ├─ Single Value Display
      ├─ Value Grid (2-3 columns)
      ├─ Comparison Table
      ├─ Range Display
      ├─ Alert Box
      └─ Multi-parameter List

Position: Fixed bottom-right
Width: 350-650px (content-dependent)
Height: Auto (scrollable if needed)
Actions: None (display only)
```

**Clean, focused, information-only overlays! 🎯**