# Professional Black UI Theme Integration Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Overhaul the Stock Analyst UI to implement an immersive, professional pitch-black canvas with cyber-neon blue and cyan styling accents.

**Architecture:** We will inject advanced custom CSS rules globally in `src/ui_components.py` that override Streamlit's default container, sidebar, and tab components. We will also revamp the Plotly price and growth chart configurations to set transparent backgrounds, sub-pixel gridline overlays, and neon blue outlines, completely preserving all data metrics and financial calculations.

**Tech Stack:** Python, Streamlit, Plotly, pandas, pytest.

---

### Task 1: Custom CSS Overrides in `ui_components.py`

**Files:**
- Modify: [src/ui_components.py](file:///d:/Work/komar/src/ui_components.py)

**Step 1: Write CSS upgrades**
In `src/ui_components.py`, rewrite `get_glassmorphic_css` to inject the upgraded styling rules:
- Google Font `Outfit` integration.
- Custom container styling (`[data-testid="stAppViewContainer"]` set to pitch black `#020202` with top-left radial gradient).
- Custom sidebar styling (`[data-testid="stSidebar"]` set to `#09090b` with sub-pixel outline).
- High-end metric cards (`.komar-card` set to `rgba(10, 10, 12, 0.8)` with glowing borders and cyber-blue drop shadows).
- Styled Streamlit Tabs bar (`[data-testid="stTabBar"]`, active tab highlighted with a cyan/blue glow).
- Glowing call-to-action buttons with spring-offset hover animations.

Exact CSS content to implement in `get_glassmorphic_css`:
```python
def get_glassmorphic_css() -> str:
    logger.debug("Generating custom glassmorphic CSS rules")
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stText, .stMarkdown, p, div, span, h1, h2, h3, h4, h5, h6, label {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Immersive Pitch Black App Container with top-left ambient blue glow */
    [data-testid="stAppViewContainer"] {
        background-color: #020202 !important;
        background: radial-gradient(circle at 10% 10%, #081026 0%, #020202 70%) !important;
    }
    
    /* Sleek Pitch Black Sidebar Navigation */
    [data-testid="stSidebar"] {
        background-color: #09090b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.5) !important;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(2, 2, 2, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important;
    }
    
    /* Sleek Control Buttons with glowing cyber blue gradient */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 0.65rem 2.2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.025em !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        width: 100%;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(37, 99, 235, 0.45), 0 0 15px rgba(6, 182, 212, 0.3) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
    }
    div.stButton > button:first-child:active {
        transform: translateY(0px) !important;
    }
    
    /* Premium Glassmorphic Metrics Panels */
    .komar-card {
        background: rgba(10, 10, 12, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 14px !important;
        padding: 1.35rem !important;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.7), inset 0 1px 1px rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        margin-bottom: 1rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .komar-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(37, 99, 235, 0.25) !important;
        box-shadow: 0 16px 48px 0 rgba(0, 0, 0, 0.8), 0 0 20px rgba(37, 99, 235, 0.12) !important;
    }
    
    .komar-metric-title {
        color: #64748b !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 0.35rem !important;
    }
    .komar-metric-value {
        color: #f8fafc !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }
    .komar-metric-status {
        font-size: 0.825rem !important;
        font-weight: 700 !important;
        margin-top: 0.45rem !important;
        letter-spacing: 0.02em !important;
    }
    
    .status-positive {
        color: #10b981 !important;
        text-shadow: 0 0 8px rgba(16, 185, 129, 0.25) !important;
    }
    .status-negative {
        color: #f43f5e !important;
        text-shadow: 0 0 8px rgba(244, 63, 94, 0.25) !important;
    }
    
    .star-filled {
        color: #eab308 !important;
        font-size: 1.45rem !important;
        margin-right: 0.1rem !important;
        text-shadow: 0 0 10px rgba(234, 179, 8, 0.45) !important;
    }
    .star-empty {
        color: #334155 !important;
        font-size: 1.45rem !important;
        margin-right: 0.1rem !important;
    }
    
    /* Styled Custom Tabs Bar */
    div[data-testid="stTabBar"] {
        background-color: rgba(10, 10, 12, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 12px !important;
        padding: 0.3rem !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.5) !important;
    }
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-size: 0.925rem !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.4rem !important;
        background: transparent !important;
        border: none !important;
        border-radius: 9px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin-right: 4px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #cbd5e1 !important;
        background: rgba(255,255,255,0.02) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3b82f6 !important;
        background: rgba(37, 99, 235, 0.1) !important;
        box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.18) !important;
    }
    
    /* Styled custom tables */
    div[data-testid="stTable"] table {
        border-collapse: collapse !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        background-color: rgba(10, 10, 12, 0.3) !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTable"] th {
        background-color: rgba(15, 23, 42, 0.5) !important;
        color: #94a3b8 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.05) !important;
        padding: 0.8rem 1.2rem !important;
    }
    div[data-testid="stTable"] td {
        color: #cbd5e1 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
        padding: 0.75rem 1.2rem !important;
    }
    
    /* Input adjustments */
    div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
    }
    </style>
    """
```

**Step 2: Commit CSS updates**
```bash
git add src/ui_components.py
git commit -m "feat: design custom CSS overrides for immersive pitch-black dark theme"
```

---

### Task 2: Polishing Neon Plotly Charts in `ui_components.py`

**Files:**
- Modify: [src/ui_components.py](file:///d:/Work/komar/src/ui_components.py)

**Step 1: Overhaul Price Chart Visuals**
In `src/ui_components.py:95-157` (`get_price_chart`), apply updated properties:
- Area close price color: Cyber neon-blue (`#2563eb`).
- Transparent area fill: `rgba(37, 99, 235, 0.03)`.
- Volume chart bars marker color: Translucent deep slate-gray `rgba(71, 85, 105, 0.15)`.
- X and Y gridlines: Barely visible sub-pixel overlay (`rgba(255, 255, 255, 0.02)`).
- Fonts: Set title and tick colors matching our design.

**Step 2: Overhaul Growth Chart Visuals**
In `src/ui_components.py:159-208` (`get_growth_chart`), apply updated properties:
- Growth comparison bars marker colors: Neon blue (`#2563eb`) for valid growth, translucent red (`rgba(244, 63, 94, 0.35)`) for low-growth targets.
- Threshold shape line: Cyber-cyan/cyan color (`#06b6d4`, `width=2`, dashed).
- Fonts: Match dashboard canvas fonts.

**Step 3: Run pytest to ensure logic remains stable**
Run: `& "C:\Users\Dhanush\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m pytest -v`
Expected: All 9 tests pass.

**Step 4: Commit Plotly updates**
```bash
git add src/ui_components.py
git commit -m "feat: revamp Plotly price-volume and growth charts to matching cyber-neon style"
```

---

### Task 3: Git Sync & Push

**Step 1: Check git status**
Run: `git status`
Expected: Clean working tree.

**Step 2: Push changes to GitHub**
Run: `git push origin main`
Expected: Successfully pushed to GitHub remote `main`.
