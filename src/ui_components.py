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
    .reportview-container {
        background: #0f172a;
    }
    /* Sleek buttons with glowing blue gradient */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
        color: #ffffff !important;
    }
    /* Glassmorphism metric cards */
    .komar-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border 0.2s ease;
    }
    .komar-card:hover {
        transform: translateY(-1px);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .komar-metric-title {
        color: #94a3b8;
        font-size: 0.825rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .komar-metric-value {
        color: #f1f5f9;
        font-size: 1.65rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .komar-metric-status {
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 0.35rem;
    }
    .status-positive {
        color: #10b981;
        text-shadow: 0 0 6px rgba(16, 185, 129, 0.2);
    }
    .status-negative {
        color: #ef4444;
        text-shadow: 0 0 6px rgba(239, 68, 68, 0.2);
    }
    .star-filled {
        color: #f59e0b;
        font-size: 1.45rem;
        margin-right: 0.1rem;
        text-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
    }
    .star-empty {
        color: #475569;
        font-size: 1.45rem;
        margin-right: 0.1rem;
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
    
    # Glowing Area Close Price
    fig.add_trace(
        go.Scatter(
            x=history.index, 
            y=history["Close"], 
            name="Close Price",
            line=dict(color="#3b82f6", width=3),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.04)"
        ),
        secondary_y=False
    )
    
    # Translucent Volume Bar Chart
    fig.add_trace(
        go.Bar(
            x=history.index, 
            y=history["Volume"], 
            name="Volume",
            marker=dict(color="rgba(148, 163, 184, 0.15)")
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>{ticker} Price & Volume Performance (Last 30 Trading Days)</b>",
            font=dict(color="#f1f5f9", size=15),
            x=0.0
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#94a3b8"), orientation="h", y=1.1, x=0.8),
        margin=dict(t=50, b=20, l=10, r=10),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.03)",
            tickfont=dict(color="#94a3b8")
        ),
        yaxis=dict(
            title=dict(text=f"Price ({price_symbol})", font=dict(color="#3b82f6")),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.03)",
            tickfont=dict(color="#3b82f6")
        ),
        yaxis2=dict(
            title=dict(text="Volume", font=dict(color="#94a3b8")),
            showgrid=False,
            tickfont=dict(color="#94a3b8")
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
            width=0.45
        )
    ])
    
    # 20% Target threshold reference line
    fig.add_shape(
        type="line",
        x0=-0.5, y0=20, x1=1.5, y1=20,
        line=dict(color="#f59e0b", width=2, dash="dash")
    )
    
    fig.update_layout(
        title=dict(
            text="<b>Financial Growth vs. Komar's 20% Threshold</b>",
            font=dict(color="#f1f5f9", size=14)
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=20, l=10, r=10),
        yaxis=dict(
            title="Growth Rate (%)",
            tickfont=dict(color="#94a3b8"),
            gridcolor="rgba(255,255,255,0.03)"
        ),
        xaxis=dict(tickfont=dict(color="#94a3b8"))
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
