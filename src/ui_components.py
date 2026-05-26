import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import logging
import time

# Configure logging
logger = logging.getLogger("komar.ui")

def get_glassmorphic_css() -> str:
    """
    Returns custom CSS containing dark theme overlays, glowing border effects,
    and glassmorphism properties for the Streamlit dashboard layout.
    """
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

def get_price_chart(history: pd.DataFrame, ticker: str, price_symbol: str = "$") -> go.Figure:
    """
    Returns a custom, high-fidelity dark-themed Plotly stock price area chart
    with a volume overlay in the background.
    """
    start_time = time.time()
    logger.debug(f"Generating price-volume Plotly chart for ticker {ticker}")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Glowing Area Close Price (Vibrant cyber blue)
    fig.add_trace(
        go.Scatter(
            x=history.index, 
            y=history["Close"], 
            name="Close Price",
            line=dict(color="#3b82f6", width=3),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.03)"
        ),
        secondary_y=False
    )
    
    # Translucent Volume Bar Chart
    fig.add_trace(
        go.Bar(
            x=history.index, 
            y=history["Volume"], 
            name="Volume",
            marker=dict(color="rgba(148, 163, 184, 0.1)")
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{ticker} Price & Volume Performance (Last 30 Trading Days)</b>",
            font=dict(color="#f8fafc", size=15),
            x=0.0
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#64748b"), orientation="h", y=1.1, x=0.8),
        margin=dict(t=50, b=20, l=10, r=10),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.02)",
            tickfont=dict(color="#64748b")
        ),
        yaxis=dict(
            title=dict(text=f"Price ({price_symbol})", font=dict(color="#3b82f6")),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.02)",
            tickfont=dict(color="#3b82f6")
        ),
        yaxis2=dict(
            title=dict(text="Volume", font=dict(color="#64748b")),
            showgrid=False,
            tickfont=dict(color="#64748b")
        )
    )
    logger.info(f"Generated price chart for {ticker} in {time.time() - start_time:.4f}s")
    return fig

def get_growth_chart(sales_growth: float, eps_growth: float) -> go.Figure:
    """
    Returns a Plotly bar chart comparing the stock's actual growth metrics
    to Julian Komar's 20% growth entry threshold.
    """
    start_time = time.time()
    logger.debug(f"Generating growth comparison Plotly chart for {sales_growth}% Sales, {eps_growth}% EPS")
    
    categories = ["YoY Sales Growth", "YoY EPS Growth"]
    values = [sales_growth, eps_growth]
    colors = [
        "#10b981" if sales_growth >= 20 else "rgba(244, 63, 94, 0.4)",
        "#10b981" if eps_growth >= 20 else "rgba(244, 63, 94, 0.4)"
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker=dict(
                color=colors,
                line=dict(color=["#10b981" if sales_growth >= 20 else "#f43f5e", "#10b981" if eps_growth >= 20 else "#f43f5e"], width=1.5)
            ),
            text=[f"{v:.1f}%" for v in values],
            textposition="auto",
            width=0.45
        )
    ])
    
    # 20% Target threshold reference line (Neon Cyan)
    fig.add_shape(
        type="line",
        x0=-0.5, y0=20, x1=1.5, y1=20,
        line=dict(color="#06b6d4", width=2, dash="dash")
    )
    
    fig.update_layout(
        title=dict(
            text="<b>Financial Growth vs. Komar's 20% Threshold</b>",
            font=dict(color="#f8fafc", size=14)
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=20, l=10, r=10),
        yaxis=dict(
            title=dict(text="Growth Rate (%)", font=dict(color="#64748b")),
            tickfont=dict(color="#64748b"),
            gridcolor="rgba(255,255,255,0.02)"
        ),
        xaxis=dict(tickfont=dict(color="#64748b"))
    )
    logger.info(f"Generated growth comparison chart in {time.time() - start_time:.4f}s")
    return fig

def render_rating_stars(rating: int) -> str:
    """
    Returns structured HTML rendering stars based on the 1-10 rating score.
    """
    stars = ""
    for i in range(10):
        if i < rating:
            stars += '<span class="star-filled">★</span>'
        else:
            stars += '<span class="star-empty">☆</span>'
    return stars
