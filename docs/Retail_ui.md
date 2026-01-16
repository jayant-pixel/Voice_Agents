# Retail Product Advisor - Avatar + Overlay System
## Natural Conversation with Smart Product Display

---

## 🎯 SCENARIO OVERVIEW

**Setting**: Virtual retail kiosk in electronics store  
**User**: Parent shopping for college laptop  
**Avatar**: Product advisor (visible on left)  
**Overlays**: Product cards appear on right as relevant  

---

## 💬 COMPLETE CONVERSATION WITH OVERLAYS

### **[TURN 1] - Opening**

**AVATAR**:  
"Hi there! Welcome to our store. I'm here to help you find exactly what you need today. What brings you in?"

**CUSTOMER**:  
"I'm looking for a good laptop for my daughter. She's starting college next month."

---

### **[TURN 2] - Need Discovery**

**AVATAR**:  
"That's exciting! Congrats to her. To help me point you in the right direction, what will she be studying? And do you know if her program has any specific requirements?"

**CUSTOMER**:  
"She's going into graphic design. I think she mentioned needing something with good graphics?"

---

### **[TURN 3] - Requirements Clarification**

**AVATAR**:  
"Perfect, graphic design is definitely going to need some solid specs. She'll want a laptop with a good dedicated graphics card, plenty of RAM, and a high-quality display for color accuracy. What's your budget range looking like?"

**CUSTOMER**:  
"Probably around $1,200 to $1,500. Is that realistic?"

---

### **[TURN 4] - Product Recommendations (FIRST OVERLAY APPEARS)**

**AVATAR**:  
"Absolutely, that's a great range for what she needs. I'd recommend looking at either the Dell XPS 15 or the MacBook Air M3. Both are around $1,400 right now. Let me show you the comparison."

**[OVERLAY 1 APPEARS - Product Comparison]**

```markdown
┌────────────────────────────────────────────────────────┐
│ 💻 Recommended Laptops for Graphic Design              │
│ Budget: $1,200-$1,500 | Use: Graphic Design           │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────┬──────────────────────────┐  │
│  │ Dell XPS 15          │ MacBook Air M3           │  │
│  ├──────────────────────┼──────────────────────────┤  │
│  │ $1,399               │ $1,399                   │  │
│  │                      │                          │  │
│  │ 15.6" OLED Display   │ 13.6" Liquid Retina     │  │
│  │ 3456 × 2160          │ 2560 × 1664             │  │
│  │                      │                          │  │
│  │ Intel Core i7-13700H │ Apple M3 chip           │  │
│  │ 16GB RAM             │ 16GB RAM                │  │
│  │ 512GB SSD            │ 512GB SSD               │  │
│  │                      │                          │  │
│  │ NVIDIA RTX 4050      │ Integrated M3 GPU       │  │
│  │ 6GB VRAM             │ 10-core GPU             │  │
│  │                      │                          │  │
│  │ Windows 11           │ macOS Sonoma            │  │
│  │                      │                          │  │
│  │ Weight: 4.2 lbs      │ Weight: 2.7 lbs         │  │
│  │ Battery: 6-8 hrs     │ Battery: 15-18 hrs      │  │
│  │                      │                          │  │
│  │ ✅ Adobe certified    │ ✅ Final Cut optimized   │  │
│  │ ✅ Larger screen      │ ✅ Ultra portable        │  │
│  │ ✅ Windows familiar   │ ✅ Best battery life     │  │
│  └──────────────────────┴──────────────────────────┘  │
│                                                         │
│  Stock Status:                                         │
│  • Dell XPS 15: In stock (Silver)                     │
│  • MacBook Air M3: In stock (Midnight, Starlight)     │
│                                                         │
└────────────────────────────────────────────────────────┘

Layout: product-comparison
Width: 650px
Data: 2 products, key specs only
```

**AVATAR**:  
"The Dell has a gorgeous 15.6-inch OLED display and comes with an NVIDIA graphics card, which is excellent for design software like Adobe Creative Suite. The MacBook Air is incredibly portable, has amazing battery life, and the M3 chip handles creative work really well."

---

### **[TURN 5] - Addressing Concerns**

**CUSTOMER**:  
"She's always used Windows. Would switching to Mac be hard?"

**AVATAR**:  
"It's a fair question. There's definitely a learning curve, maybe a week or two to feel comfortable, but a lot of design students actually prefer Mac once they adjust. That said, if she's more comfortable with Windows and wants to jump right in, the Dell XPS 15 is honestly fantastic and she'll have no issues running any design software."

---

### **[TURN 6] - Storage Question (OVERLAY UPDATES)**

**CUSTOMER**:  
"Okay, what about storage? How much does she need?"

**AVATAR**:  
"For graphic design, I'd say 512GB minimum, but 1TB is better if it fits the budget. Design files, especially when she's working with high-resolution images and video projects, eat up space quickly. Let me show you the upgrade options."

**[OVERLAY 2 APPEARS - Storage Options]**

```markdown
┌──────────────────────────────────────────┐
│ 💾 Storage Options                       │
│ Both laptops available                   │
├──────────────────────────────────────────┤
│                                           │
│  Dell XPS 15:                            │
│  ┌─────────────────────────────────────┐ │
│  │ 512GB SSD  → $1,399  (Standard)     │ │
│  │ 1TB SSD    → $1,599  (+$200)        │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  MacBook Air M3:                         │
│  ┌─────────────────────────────────────┐ │
│  │ 512GB SSD  → $1,399  (Standard)     │ │
│  │ 1TB SSD    → $1,599  (+$200)        │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  💡 Recommendation:                      │
│  For graphic design with Adobe Suite,    │
│  1TB provides comfortable working space  │
│  for projects, software, and files.      │
│                                           │
│  Typical Usage:                          │
│  • Adobe Creative Suite: ~30GB           │
│  • Project files (semester): ~100-200GB  │
│  • OS + Apps: ~50GB                      │
│  • Buffer space needed: ~150GB           │
│                                           │
└──────────────────────────────────────────┘

Layout: storage-options
Width: 500px
Data: Price comparison + usage breakdown
```

**AVATAR**:  
"Both laptops I mentioned come with 512GB standard, and you can upgrade to 1TB for about $200 more."

---

### **[TURN 7] - Stock Check**

**CUSTOMER**:  
"And they're both in stock?"

**AVATAR**:  
"Let me check for you real quick..."

*(2 second pause)*

**[OVERLAY 3 APPEARS - Stock & Availability]**

```markdown
┌─────────────────────────────────────┐
│ 📦 Stock Availability               │
│ Current store inventory             │
├─────────────────────────────────────┤
│                                      │
│  Dell XPS 15                        │
│  ┌────────────────────────────────┐ │
│  │ ✅ In Stock                     │ │
│  │                                 │ │
│  │ 512GB: Available (Silver)       │ │
│  │ 1TB:   Available (Silver)       │ │
│  │                                 │ │
│  │ Location: Aisle 7, Display #3   │ │
│  └────────────────────────────────┘ │
│                                      │
│  MacBook Air M3                     │
│  ┌────────────────────────────────┐ │
│  │ ✅ In Stock                     │ │
│  │                                 │ │
│  │ 512GB: Midnight, Starlight      │ │
│  │ 1TB:   Midnight                 │ │
│  │                                 │ │
│  │ Location: Aisle 8, Apple Section│ │
│  └────────────────────────────────┘ │
│                                      │
│  Both available for:                │
│  • Immediate purchase               │
│  • Demo at display units            │
│  • Same-day pickup                  │
│                                      │
└─────────────────────────────────────┘

Layout: stock-status
Width: 450px
Data: Real-time inventory + location
```

**AVATAR**:  
"Yes! We have both models available. The Dell XPS 15 is in stock in silver, and we have the MacBook Air M3 in midnight and starlight colors. Would you like to see them in person, or would you prefer I send the details to your phone so you can discuss with your daughter first?"

---

### **[TURN 8] - Information Sharing Request**

**CUSTOMER**:  
"Can you send me the info? I want to show her tonight."

**AVATAR**:  
"Of course! I'll send you the specs, pricing, and links to both laptops."

**[OVERLAY 4 APPEARS - Summary Card]**

```markdown
┌──────────────────────────────────────────┐
│ 📧 Product Summary                       │
│ Ready to share                           │
├──────────────────────────────────────────┤
│                                           │
│  Selected Products:                      │
│                                           │
│  1. Dell XPS 15                          │
│     • Price: $1,399 (512GB) / $1,599 (1TB)│
│     • 15.6" OLED, Intel i7, RTX 4050     │
│     • Windows 11                         │
│     • In stock: Silver                   │
│                                           │
│  2. MacBook Air M3                       │
│     • Price: $1,399 (512GB) / $1,599 (1TB)│
│     • 13.6" Retina, M3 chip, 16GB RAM    │
│     • macOS Sonoma                       │
│     • In stock: Midnight, Starlight      │
│                                           │
│  Use Case: Graphic Design (College)      │
│  Budget Range: $1,200-$1,500             │
│                                           │
│  Advisor Notes:                          │
│  • Both excellent for Adobe Creative Suite│
│  • Dell: Larger screen, Windows familiar │
│  • Mac: Better battery, ultra portable   │
│  • 1TB recommended for design work       │
│                                           │
│  Share Options:                          │
│  • Email: [Enter address below]          │
│  • SMS: [Enter phone number below]       │
│  • QR Code: [Scan to access on phone]    │
│                                           │
│  [Input field shown on screen]           │
│                                           │
└──────────────────────────────────────────┘

Layout: share-summary
Width: 520px
Data: Complete conversation summary
```

**AVATAR**:  
"Just enter your email or phone number on the screen and you'll get everything in about 30 seconds. Is there anything else I can help you with while you're here?"

---

### **[TURN 9] - Closing**

**CUSTOMER**:  
"No, I think that's it. Thanks for your help!"

**AVATAR**:  
"My pleasure! Good luck with the decision, and feel free to come back if you have any questions. Hope your daughter has an amazing first semester!"

**[OVERLAY FADES OUT]**

---

## 📊 OVERLAY DESIGN SPECIFICATIONS

### **Overlay 1: Product Comparison (Wide)**

```
Type: product-comparison
Width: 650px
Height: ~520px
Layout: 2-column side-by-side
Data Structure:
- Product name
- Price
- Key specs (screen, CPU, RAM, storage, GPU)
- OS
- Physical specs (weight, battery)
- Highlights (3 key features each)
- Stock status
```

### **Overlay 2: Storage Options (Medium)**

```
Type: storage-options
Width: 500px
Height: ~420px
Layout: Stacked pricing + usage breakdown
Data Structure:
- Product name
- Storage tiers with prices
- Price delta shown
- Usage breakdown (visual guide)
- Recommendation with reasoning
```

### **Overlay 3: Stock Status (Compact)**

```
Type: stock-status
Width: 450px
Height: ~380px
Layout: Per-product availability cards
Data Structure:
- Product name
- Availability status (✅/⚠️)
- Available configurations
- Store location
- Purchase options
```

### **Overlay 4: Summary Card (Medium)**

```
Type: share-summary
Width: 520px
Height: ~480px
Layout: Vertical summary list
Data Structure:
- Selected products
- Key specs recap
- Use case reminder
- Advisor notes
- Sharing options
- Input field (if interactive)
```

---

## 🎨 RETAIL-SPECIFIC DESIGN ELEMENTS

### **Color System**

```css
:root {
  /* Design System - Brutalist */
  --border-color: #000;
  --bg-color: #fff;
  --gray-text: #666;
  --pink-accent: #FF0055;
  --font-sans: system-ui, -apple-system, sans-serif;
  --font-mono: monospace;
  
  /* Status */
  --in-stock: #000;
  --low-stock: #666;
  --out-stock: #FF0055;
  
  /* Product Highlights */
  --highlight-bg: #F8F8F6;
  --price-color: #000;
}
```

### **Typography**

```css
.product-name {
  font-family: var(--font-mono);
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #000;
}

.product-price {
  font-size: 1.5rem;
  font-weight: 800;
  color: #000;
}

.spec-label {
  font-family: monospace;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #666;
}

.spec-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: #000;
}

.stock-status {
  font-family: monospace;
  font-size: 0.85rem;
  font-weight: 800;
  text-transform: uppercase;
}

.stock-status.in-stock {
  color: #000;
}

.stock-status.in-stock::before {
  content: '✓ ';
}
```

---

## 📊 PRODUCT COMPARISON OVERLAY (Detailed)

```markdown
┌──────────────────────────────────────────────────────────────┐
│ 💻 Laptop Comparison                                         │
│ For Graphic Design | Budget: $1,200-$1,500                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────┬────────────────────────────┐    │
│  │   Dell XPS 15          │   MacBook Air M3           │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │                        │                            │    │
│  │   [Product Image]      │   [Product Image]          │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Price                  │ Price                      │    │
│  │ $1,399                 │ $1,399                     │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Display                │ Display                    │    │
│  │ 15.6" OLED             │ 13.6" Liquid Retina        │    │
│  │ 3456 × 2160            │ 2560 × 1664                │    │
│  │ 500 nits               │ 500 nits                   │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Processor              │ Processor                  │    │
│  │ Intel i7-13700H        │ Apple M3                   │    │
│  │ 14 cores               │ 8 cores                    │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Memory                 │ Memory                     │    │
│  │ 16GB DDR5              │ 16GB Unified               │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Graphics               │ Graphics                   │    │
│  │ NVIDIA RTX 4050        │ M3 GPU                     │    │
│  │ 6GB VRAM               │ 10-core                    │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Storage                │ Storage                    │    │
│  │ 512GB SSD              │ 512GB SSD                  │    │
│  │ (upgradeable to 1TB)   │ (upgradeable to 1TB)       │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Operating System       │ Operating System           │    │
│  │ Windows 11             │ macOS Sonoma               │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Battery Life           │ Battery Life               │    │
│  │ 6-8 hours              │ 15-18 hours                │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Weight                 │ Weight                     │    │
│  │ 4.2 lbs                │ 2.7 lbs                    │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Best For               │ Best For                   │    │
│  │ ✅ Large screen work    │ ✅ Portability             │    │
│  │ ✅ Adobe Creative Suite │ ✅ Battery life            │    │
│  │ ✅ Windows familiar     │ ✅ Light weight            │    │
│  │ ✅ Dedicated GPU        │ ✅ Fanless design          │    │
│  │                        │                            │    │
│  ├────────────────────────┼────────────────────────────┤    │
│  │ Stock Status           │ Stock Status               │    │
│  │ ✅ In Stock (Silver)    │ ✅ In Stock (2 colors)     │    │
│  └────────────────────────┴────────────────────────────┘    │
│                                                               │
│  💡 Both excellent for graphic design                        │
│     Dell: Better for stationary workstation use              │
│     Mac: Better for on-campus portability                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 OVERLAY PROGRESSION LOGIC

### **Conversation Flow → Overlay Sequence**

```
1. Budget mentioned ($1,200-$1,500)
   → Show filtered products in range

2. Use case clarified (Graphic Design)
   → Show comparison with relevant specs highlighted

3. Specific question (Storage needs)
   → Show storage options + pricing

4. Availability question
   → Show real-time stock status

5. Request to share
   → Show summary card with sharing options
```

### **Smart Data Filtering**

```javascript
// Filter products based on conversation context
function getRelevantProducts(context) {
  return products.filter(p => 
    p.price >= context.budget.min &&
    p.price <= context.budget.max &&
    p.category === context.category &&
    p.specs.matches(context.requirements)
  );
}

// Example context from conversation
const context = {
  budget: { min: 1200, max: 1500 },
  category: 'laptop',
  requirements: {
    useCase: 'graphic-design',
    needsGPU: true,
    displayQuality: 'high',
    osPreference: 'windows' // from "She's always used Windows"
  }
};
```

---

## ✅ KEY RETAIL FEATURES

### **1. Dynamic Product Filtering**
- Conversation → Extract requirements → Filter catalog
- Budget aware
- Use-case specific

### **2. Comparison Focus**
- Show 2 products max at once
- Highlight differences
- Clear recommendations

### **3. Stock Integration**
- Real-time availability
- Store location
- Alternative options if out of stock

### **4. Price Transparency**
- Base price + upgrades shown clearly
- Delta pricing (+$200 for 1TB)
- Bundle options

### **5. Share Functionality**
- Summary card with key info
- Multi-channel (email, SMS, QR)
- Includes advisor notes

---

## 🎯 OVERLAY SIZE SUMMARY (Retail)

| Overlay Type | Width | Content |
|--------------|-------|---------|
| Product Comparison | 650px | 2 products side-by-side |
| Storage Options | 500px | Price tiers + recommendations |
| Stock Status | 450px | Availability per product |
| Summary Card | 520px | Complete conversation recap |

---

## 💡 RETAIL-SPECIFIC OVERLAY PRINCIPLES

1. **Visual Product Cards** - Images + specs in grid
2. **Price Prominent** - Always visible, green color
3. **Stock Status Clear** - ✅ In stock / ⚠️ Low / ❌ Out
4. **Comparison Format** - Side-by-side for 2 products max
5. **Actionable Summary** - Shareable, includes advisor notes

**Ready for retail implementation! 🛍️**