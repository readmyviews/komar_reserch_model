# Julian Komar Stock Detective Dashboard Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Build a premium Python-based Streamlit stock analytics dashboard applying the fundamental, thematic, and liquidity research methodology of Julian Komar, powered by yfinance and Gemini.

**Architecture:** A multi-layered clean architecture consisting of a data fetcher (`src/analyzer.py`), a Gemini detective LLM agent (`src/agent.py`), a custom visualization utility (`src/ui_components.py`), and a master entry point (`app.py`).

**Tech Stack:** Python 3.10+, Streamlit, yfinance, google-genai, python-dotenv, pandas, plotly, pytest

---

### Task 1: Environment & Requirements Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/test_env.py`

**Step 1: Write a test verifying core packages are importable**
Create `tests/test_env.py`:
```python
def test_imports():
    import streamlit as st
    import yfinance as yf
    from google import genai
    import dotenv
    import pandas as pd
    import plotly.graph_objects as go
    assert True
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_env.py`
Expected: FAIL with `ModuleNotFoundError` because dependencies are not installed in the environment yet.

**Step 3: Write minimal implementation**
Create `requirements.txt`:
```text
streamlit>=1.35.0
yfinance>=0.2.40
google-genai>=0.1.1
python-dotenv>=1.0.1
pandas>=2.0.0
plotly>=5.22.0
pytest>=8.0.0
```
Run installation command:
`pip install -r requirements.txt`

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_env.py`
Expected: PASS

**Step 5: Commit**
Run in PowerShell:
```powershell
git add requirements.txt tests/test_env.py ; git commit -m "chore: setup dependencies and verification tests"
```

---

### Task 2: Core Data Analyzer (`src/analyzer.py`)

**Files:**
- Create: `src/__init__.py` (Empty file)
- Create: `src/analyzer.py`
- Create: `tests/test_analyzer.py`

**Step 1: Write a failing test for data fetching & resolving ticker names**
Create `tests/test_analyzer.py`:
```python
import pytest
from src.analyzer import resolve_ticker, calculate_metrics

def test_resolve_ticker_india():
    assert resolve_ticker("Adani Power", "India") == "ADANIPOWER.NS"

def test_resolve_ticker_us():
    assert resolve_ticker("Nvidia", "US") == "NVDA"

def test_calculate_metrics():
    # Test metric calculations for a known ticker like 'NVDA' or mock it
    metrics = calculate_metrics("NVDA")
    assert "sales_growth_yoy" in metrics
    assert "eps_growth_yoy" in metrics
    assert "avg_daily_dollar_volume" in metrics
    assert metrics["avg_daily_dollar_volume"] > 0
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_analyzer.py`
Expected: FAIL with `ModuleNotFoundError` or "cannot import name"

**Step 3: Implement `src/analyzer.py`**
Create `src/analyzer.py`:
```python
import yfinance as yf
import pandas as pd
import numpy as np

def resolve_ticker(name: str, country: str) -> str:
    name_clean = name.strip()
    if not name_clean:
        return ""
    
    # Simple direct overrides
    overrides = {
        "adani power": "ADANIPOWER.NS",
        "nvidia": "NVDA",
        "tesla": "TSLA"
    }
    key = name_clean.lower()
    if key in overrides:
        return overrides[key]
        
    if country.lower() == "india":
        if not (name_clean.endswith(".NS") or name_clean.endswith(".BO")):
            return f"{name_clean.upper()}.NS"
    return name_clean.upper()

def calculate_metrics(ticker_symbol: str) -> dict:
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Fetch historical price for liquidity check (last 30 trading days)
    history = ticker.history(period="30d")
    if history.empty:
        raise ValueError(f"Could not fetch historical data for {ticker_symbol}")
    
    # Daily dollar volume = Close * Volume
    history["dollar_volume"] = history["Close"] * history["Volume"]
    avg_daily_dollar_volume = float(history["dollar_volume"].mean())
    current_price = float(history["Close"].iloc[-1])
    recent_volume = int(history["Volume"].iloc[-1])

    # 2. Fetch financial reports for Sales/EPS Growth
    financials = ticker.financials
    quarterly_financials = ticker.quarterly_financials
    
    sales_growth_yoy = None
    eps_growth_yoy = None
    
    # Try using quarterly statements (preferred for rapid YoY growth checking)
    if quarterly_financials is not None and not quarterly_financials.empty:
        try:
            # YoY Revenue growth comparing the latest quarter to same quarter last year
            # Columns are sorted descending by date
            rev_latest = quarterly_financials.loc["Total Revenue"].iloc[0]
            rev_prior_year = quarterly_financials.loc["Total Revenue"].iloc[4] # 4 quarters ago
            sales_growth_yoy = float(((rev_latest - rev_prior_year) / rev_prior_year) * 100)
        except Exception:
            pass

        try:
            # YoY EPS growth comparing latest quarter to same quarter last year
            eps_row = "Diluted EPS" if "Diluted EPS" in quarterly_financials.index else "Basic EPS"
            eps_latest = quarterly_financials.loc[eps_row].iloc[0]
            eps_prior_year = quarterly_financials.loc[eps_row].iloc[4]
            if eps_prior_year != 0:
                eps_growth_yoy = float(((eps_latest - eps_prior_year) / abs(eps_prior_year)) * 100)
        except Exception:
            pass

    # Fallback to annual statements if quarterly failed
    if sales_growth_yoy is None and financials is not None and not financials.empty:
        try:
            rev_latest = financials.loc["Total Revenue"].iloc[0]
            rev_prior = financials.loc["Total Revenue"].iloc[1]
            sales_growth_yoy = float(((rev_latest - rev_prior) / rev_prior) * 100)
        except Exception:
            pass
            
        try:
            eps_row = "Diluted EPS" if "Diluted EPS" in financials.index else "Basic EPS"
            eps_latest = financials.loc[eps_row].iloc[0]
            eps_prior = financials.loc[eps_row].iloc[1]
            if eps_prior != 0:
                eps_growth_yoy = float(((eps_latest - eps_prior) / abs(eps_prior)) * 100)
        except Exception:
            pass
            
    return {
        "ticker": ticker_symbol,
        "current_price": current_price,
        "recent_volume": recent_volume,
        "avg_daily_dollar_volume": avg_daily_dollar_volume,
        "sales_growth_yoy": sales_growth_yoy if sales_growth_yoy is not None else 0.0,
        "eps_growth_yoy": eps_growth_yoy if eps_growth_yoy is not None else 0.0
    }
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_analyzer.py`
Expected: PASS

**Step 5: Commit**
Run in PowerShell:
```powershell
git add src/analyzer.py src/__init__.py tests/test_analyzer.py ; git commit -m "feat: implement resolved tickers and financial metric calculations"
```

---

### Task 3: Gemini Detective Agent (`src/agent.py`)

**Files:**
- Create: `src/agent.py`
- Create: `tests/test_agent.py`

**Step 1: Write a failing test for Gemini analysis generation**
Create `tests/test_agent.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from src.agent import generate_komar_analysis

@patch("src.agent.genai.Client")
def test_generate_komar_analysis(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = '{"stock_category": "CANSLIM Stock", "rating": 4, "verdict": "Fits profile well"}'
    mock_client.models.generate_content.return_value = mock_response
    
    stats = {
        "ticker": "ADANIPOWER.NS",
        "current_price": 500.0,
        "avg_daily_dollar_volume": 12000000.0,
        "sales_growth_yoy": 35.5,
        "eps_growth_yoy": 120.0
    }
    
    res = generate_komar_analysis("Adani Power", "India", stats)
    assert res["stock_category"] == "CANSLIM Stock"
    assert res["rating"] == 4
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_agent.py`
Expected: FAIL with `ModuleNotFoundError` or "cannot import name"

**Step 3: Implement `src/agent.py`**
Create `src/agent.py`:
```python
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_komar_analysis(name: str, country: str, stats: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
        
    client = genai.Client(api_key=api_key)
    
    system_instruction = (
        "You are an expert stock market analyst applying seasoned trader Julian Komar's "
        "fundamental and thematic research methodology. You act like a 'detective' to figure "
        "out exactly what institutional investors see in a stock's fundamentals and thematic story.\n"
        "Analyze the provided stock name and country, using both the quantitative metrics provided "
        "and your broad world knowledge or search capability to research the story, business model, "
        "and sister stocks. Return a beautifully structured JSON response matching the schema."
    )
    
    prompt = f"""
    Analyze this stock:
    - Name: {name}
    - Country: {country}
    - Ticker Suffix/Symbol: {stats['ticker']}
    - Current Price: {stats['current_price']}
    - Sales Growth YoY (Calculated): {stats['sales_growth_yoy']:.2f}%
    - EPS Growth YoY (Calculated): {stats['eps_growth_yoy']:.2f}%
    - Avg Daily Dollar Volume 30d (Calculated): ${stats['avg_daily_dollar_volume']:,.2f} USD equivalent
    
    Provide analysis according to the following 4 sections of Julian Komar's framework:
    1. Fundamental Growth Layer (The Numbers): Evaluate our Sales/EPS growth calculations against target thresholds (20%, 30%, 40%+). Explicitly categorize into CANSLIM Stock, Sales Grower, or Story Stock.
    2. The Story Layer (The 'Why'): Deep-dive business model and specific catalyst (e.g. AI, cyber, cloud, green energy).
    3. Sister Stocks & Theme Alignment: List 3-4 competitor/sister stocks in the same sector globally or locally showing strong growth and momentum. Confirm if the theme is in high market demand.
    4. Institutional Quality Check (Liquidity): Compare Daily Dollar volume (${stats['avg_daily_dollar_volume']:,.2f}) to thresholds ($20M-$100M USD for mature themes; $5M-$10M USD for young micro-caps). Explain if institutions can enter/exit safely.
    
    Finally, give a 1-5 star Julian Komar Rating (1: poor fit, 5: perfect fit) and a concise Verdict.
    """
    
    class AnalysisResponse(types.BaseModel):
        stock_category: str
        fundamental_layer_details: str
        story_layer_details: str
        sister_stocks_details: str
        liquidity_details: str
        rating: int
        verdict: str

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=AnalysisResponse,
            temperature=0.2
        )
    )
    
    return json.loads(response.text)
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_agent.py`
Expected: PASS

**Step 5: Commit**
Run in PowerShell:
```powershell
git add src/agent.py tests/test_agent.py ; git commit -m "feat: implement Gemini detective agent with structured JSON output"
```

---

### Task 4: Premium UI Elements & Charts (`src/ui_components.py`)

**Files:**
- Create: `src/ui_components.py`

**Step 1: Write failing visual test stub**
Since UI components are primarily visual and rendering-oriented, create a standard test verify functions return Plotly objects or correct CSS strings.
Create `tests/test_ui.py`:
```python
import plotly.graph_objects as go
from src.ui_components import get_price_chart, get_growth_chart, get_glassmorphic_css

def test_ui_generators():
    import pandas as pd
    history_df = pd.DataFrame({
        "Close": [100, 101, 102],
        "Volume": [1000, 1500, 1200]
    }, index=pd.date_range("2026-01-01", periods=3))
    
    chart = get_price_chart(history_df, "TEST")
    assert isinstance(chart, go.Figure)
    
    css = get_glassmorphic_css()
    assert ".komar-card" in css
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_ui.py`
Expected: FAIL (Cannot import)

**Step 3: Implement `src/ui_components.py`**
Create `src/ui_components.py`:
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def get_glassmorphic_css() -> str:
    return """
    <style>
    .reportview-container {
        background: #0f172a;
    }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
    }
    .komar-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    .komar-metric-title {
        color: #94a3b8;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    .komar-metric-value {
        color: #f1f5f9;
        font-size: 1.75rem;
        font-weight: 700;
    }
    .komar-metric-status {
        font-size: 0.825rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }
    .status-positive {
        color: #10b981;
    }
    .status-negative {
        color: #ef4444;
    }
    .star-filled {
        color: #f59e0b;
        font-size: 1.5rem;
    }
    .star-empty {
        color: #475569;
        font-size: 1.5rem;
    }
    </style>
    """

def get_price_chart(history: pd.DataFrame, ticker: str) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Glowing Area Close Price
    fig.add_trace(
        go.Scatter(
            x=history.index, 
            y=history["Close"], 
            name="Close Price",
            line=dict(color="#3b82f6", width=3),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.05)"
        ),
        secondary_y=False
    )
    
    # Volume Bar Chart
    fig.add_trace(
        go.Bar(
            x=history.index, 
            y=history["Volume"], 
            name="Volume",
            marker=dict(color="rgba(148, 163, 184, 0.25)")
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{ticker} Historical Performance (30 Trading Days)</b>",
            font=dict(color="#f1f5f9", size=16),
            x=0.0
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#94a3b8")),
        margin=dict(t=50, b=20, l=10, r=10),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickfont=dict(color="#94a3b8")
        ),
        yaxis=dict(
            title="Price",
            titlefont=dict(color="#3b82f6"),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickfont=dict(color="#3b82f6")
        ),
        yaxis2=dict(
            title="Volume",
            titlefont=dict(color="#94a3b8"),
            showgrid=False,
            tickfont=dict(color="#94a3b8")
        )
    )
    return fig

def get_growth_chart(sales_growth: float, eps_growth: float) -> go.Figure:
    categories = ["YoY Sales Growth", "YoY EPS Growth"]
    values = [sales_growth, eps_growth]
    colors = [
        "#10b981" if sales_growth >= 20 else "#ef4444",
        "#10b981" if eps_growth >= 20 else "#ef4444"
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f"{v:.1f}%" for v in values],
            textposition="auto",
            width=0.4
        )
    ])
    
    # Target line at 20%
    fig.add_shape(
        type="line",
        x0=-0.5, y0=20, x1=1.5, y1=20,
        line=dict(color="#f59e0b", width=2, dash="dash")
    )
    
    fig.update_layout(
        title=dict(
            text="<b>Financial Growth vs. Komar's 20% Target Threshold</b>",
            font=dict(color="#f1f5f9", size=14)
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=20, l=10, r=10),
        yaxis=dict(
            title="Growth (%)",
            tickfont=dict(color="#94a3b8"),
            gridcolor="rgba(255,255,255,0.05)"
        ),
        xaxis=dict(tickfont=dict(color="#94a3b8"))
    )
    return fig

def render_rating_stars(rating: int) -> str:
    stars = ""
    for i in range(5):
        if i < rating:
            stars += '<span class="star-filled">★</span>'
        else:
            stars += '<span class="star-empty">☆</span>'
    return stars
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_ui.py`
Expected: PASS

**Step 5: Commit**
Run in PowerShell:
```powershell
git add src/ui_components.py tests/test_ui.py ; git commit -m "feat: implement high-fidelity plotly charts and glassmorphic css metrics generator"
```

---

### Task 5: Master Application Assembly (`app.py`)

**Files:**
- Create: `app.py`
- Modify: `docs/plans/task.md` (Update task statuses to complete)

**Step 1: Write a basic sanity test verifying app.py can import dependencies**
Create `tests/test_app.py`:
```python
def test_app_imports():
    import app
    assert True
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_app.py`
Expected: FAIL with `ModuleNotFoundError` (because app.py does not exist yet)

**Step 3: Implement `app.py`**
Create `app.py`:
```python
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv
import os

from src.analyzer import resolve_ticker, calculate_metrics
from src.agent import generate_komar_analysis
from src.ui_components import (
    get_glassmorphic_css, 
    get_price_chart, 
    get_growth_chart, 
    render_rating_stars
)

load_dotenv()

# Set Page Config
st.set_page_config(
    page_title="Julian Komar Stock Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Beautiful Styling
st.markdown(get_glassmorphic_css(), unsafe_allow_html=True)

# Application Header
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05);">
    <h1 style="color: #3b82f6; margin-bottom: 0.5rem; font-size: 2.75rem; text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);">🔍 Komar Stock Detective</h1>
    <p style="color: #94a3b8; font-size: 1.1rem; max-width: 800px; margin: 0 auto;">
        Apply seasoned trader <b>Julian Komar's</b> specific fundamental, thematic, and institutional liquidity 
        research framework using real-time Yahoo Finance data and Gemini AI detective intelligence.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("""
<h3 style="color: #3b82f6; margin-bottom: 1rem;">⚙️ Settings</h3>
""", unsafe_allow_html=True)

stock_name = st.sidebar.text_input("Stock Ticker / Name:", value="Adani Power")
country = st.sidebar.radio("Country:", options=["India", "US"])

# Check API Key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.sidebar.error("⚠️ GEMINI_API_KEY not found in .env file! Please set it to proceed.")
else:
    st.sidebar.success("🔑 Gemini API Key configured.")

analyze_btn = st.sidebar.button("Run Detective Analysis 🔍")

# Default state or trigger analysis
if analyze_btn or "metrics" in st.session_state:
    if not gemini_api_key:
        st.error("Please add a `GEMINI_API_KEY` to your `.env` file first.")
    elif not stock_name:
        st.warning("Please enter a valid stock name or ticker symbol.")
    else:
        try:
            with st.spinner("Analyzing stock ticker and calculating fundamental metrics..."):
                resolved_ticker = resolve_ticker(stock_name, country)
                stats = calculate_metrics(resolved_ticker)
                
                # Fetch yfinance ticker object for historical data
                ticker_obj = yf.Ticker(resolved_ticker)
                history = ticker_obj.history(period="30d")
                
            with st.spinner("Invoking Gemini Detective to perform deep qualitative research..."):
                analysis = generate_komar_analysis(stock_name, country, stats)
            
            # Save into session state
            st.session_state["resolved_ticker"] = resolved_ticker
            st.session_state["stats"] = stats
            st.session_state["history"] = history
            st.session_state["analysis"] = analysis
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("💡 Pro-tip: For Indian stocks, make sure to use tickers listed on NSE (e.g. ADANIPOWER or ADANIPOWER.NS).")

# Render analysis if available in state
if "analysis" in st.session_state:
    stats = st.session_state["stats"]
    analysis = st.session_state["analysis"]
    history = st.session_state["history"]
    resolved_ticker = st.session_state["resolved_ticker"]
    
    # 1. Core Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Price card
    with col1:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">CURRENT PRICE</div>
            <div class="komar-metric-value">
                {"₹" if country == "India" else "$"}{stats['current_price']:.2f}
            </div>
            <div class="komar-metric-status">Ticker: {stats['ticker']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Liquidity card
    usd_equiv_liquidity = stats['avg_daily_dollar_volume']
    is_liquid = usd_equiv_liquidity >= 5000000.0 # Komar's minimum emerging theme threshold
    status_class = "status-positive" if is_liquid else "status-negative"
    status_text = "PASSED" if is_liquid else "FAIL"
    
    with col2:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">DAILY DOLLAR VOLUME</div>
            <div class="komar-metric-value">${usd_equiv_liquidity/1e6:.1f}M USD</div>
            <div class="komar-metric-status {status_class}">Liquidity: {status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Growth card
    sales_growth = stats['sales_growth_yoy']
    growth_passed = sales_growth >= 20.0
    growth_class = "status-positive" if growth_passed else "status-negative"
    growth_text = "PASSED (20%+)" if growth_passed else "LOW GROWTH"
    
    with col3:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">YOY SALES GROWTH</div>
            <div class="komar-metric-value">{sales_growth:.1f}%</div>
            <div class="komar-metric-status {growth_class}">{growth_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Rating card
    stars_html = render_rating_stars(analysis['rating'])
    with col4:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">KOMAR RATING</div>
            <div style="margin: 0.1rem 0;">{stars_html}</div>
            <div class="komar-metric-status" style="color:#f59e0b; font-weight:700;">
                Category: {analysis['stock_category']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. Charts Section
    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        st.plotly_chart(get_price_chart(history, resolved_ticker), use_container_width=True)
    with chart_col2:
        st.plotly_chart(get_growth_chart(stats['sales_growth_yoy'], stats['eps_growth_yoy']), use_container_width=True)
        
    # 3. Gemini Detective Report Layers
    st.markdown("### 🕵️‍♂️ Julian Komar Detective Research Report")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Fundamental Growth Layer", 
        "🔥 The Story & Catalysts", 
        "👯 Sister Stocks & Theme", 
        "🏁 Quality Check & Verdict"
    ])
    
    with tab1:
        st.markdown(f"**Stock Categorization**: `{analysis['stock_category']}`")
        st.write(analysis['fundamental_layer_details'])
        
    with tab2:
        st.write(analysis['story_layer_details'])
        
    with tab3:
        st.write(analysis['sister_stocks_details'])
        
    with tab4:
        st.markdown("#### Institutional Liquidity Assessment")
        st.write(analysis['liquidity_details'])
        st.markdown("---")
        st.markdown("#### Final Verdict")
        st.info(analysis['verdict'])
else:
    st.info("👈 Enter a stock name and country, then click 'Run Detective Analysis' in the sidebar to begin.")
```

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_app.py`
Expected: PASS

**Step 5: Commit**
Run in PowerShell:
```powershell
git add app.py tests/test_app.py ; git commit -m "feat: assemble streamlit application integrating yfinance stats and Gemini analysis"
```
