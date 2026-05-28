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
    
    /* High contrast body text, paragraphs, list items, and markdown writes */
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] li,
    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown li,
    .stText,
    p,
    li,
    div.stWrite {
        color: #cbd5e1 !important; /* Professional light slate gray for outstanding contrast */
        font-size: 0.95rem !important;
        line-height: 1.65 !important;
    }
    
    /* High contrast sidebar text rules and guidelines legibility */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] div {
        color: #94a3b8 !important; /* Slate-400 for maximum readability */
        font-size: 0.85rem !important;
        line-height: 1.525 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    
    /* Streamlit Radio options high contrast color overrides */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] p,
    div[data-testid="stRadio"] span,
    div[data-testid="stRadio"] div,
    [data-testid="stSidebar"] div[data-testid="stRadio"] label,
    [data-testid="stSidebar"] div[data-testid="stRadio"] p,
    [data-testid="stSidebar"] div[data-testid="stRadio"] span,
    [data-testid="stSidebar"] div[data-testid="stRadio"] div {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    
    /* TradingView Dark Textbox Input Field Overrides */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background-color: #1e222d !important;
        border: 1px solid #363c4e !important;
        border-radius: 4px !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stTextInput"] input {
        background-color: transparent !important;
        color: #30323e !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 0.75rem !important;
        border: none !important;
    }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: #2962ff !important;
        box-shadow: 0 0 0 1px #2962ff !important;
    }
    
    /* TradingView Flat Blue CTA Buttons overrides */
    div[data-testid="stButton"] button,
    div.stButton > button,
    .stButton button {
        background-color: #2962ff !important;
        background: #2962ff !important;
        color: #ffffff !important;
        border-radius: 4px !important;
        padding: 0.55rem 1.4rem !important;
        font-weight: 600 !important;
        font-size: 0.925rem !important;
        border: none !important;
        box-shadow: none !important;
        text-shadow: none !important;
        transition: background-color 0.15s ease, transform 0.1s ease !important;
        width: 100% !important;
    }
    div[data-testid="stButton"] button:hover,
    div.stButton > button:hover,
    .stButton button:hover {
        background-color: #1e53e5 !important;
        background: #1e53e5 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stButton"] button:active,
    div.stButton > button:active,
    .stButton button:active {
        background-color: #1a49c7 !important;
        background: #1a49c7 !important;
        border: none !important;
        box-shadow: none !important;
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
    
    /* TradingView Custom Styled Tab Bar */
    div[data-testid="stTabBar"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #2a2e39 !important;
        border-radius: 0px !important;
        padding: 0px !important;
        box-shadow: none !important;
    }
    button[data-baseweb="tab"] {
        color: #787b86 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.25rem !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0px !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.15s ease !important;
        margin-right: 8px !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #cbd5e1 !important;
        background: transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2962ff !important;
        background: transparent !important;
        border-bottom: 2px solid #2962ff !important;
        box-shadow: none !important;
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
    
    /* Custom Neon-Blue Badges */
    .komar-badge {
        background: rgba(41, 98, 255, 0.12) !important;
        color: #2962ff !important;
        border: 1px solid rgba(41, 98, 255, 0.3) !important;
        border-radius: 4px !important;
        padding: 0.2rem 0.5rem !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        display: inline-block !important;
        text-shadow: none !important;
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
    to Pratik Patel's 20% growth entry threshold.
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
            text="<b>Financial Growth vs. Patel's 20% Threshold</b>",
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

def get_highcharts_html(history: pd.DataFrame, ticker: str, price_symbol: str = "$") -> str:
    """
    Returns an HTML string that renders a beautiful Highcharts area chart with
    volume bars overlaid, optimized for our dark theme.
    """
    import json
    dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in history.index]
    prices = [float(p) for p in history["Close"]]
    volumes = [int(v) for v in history["Volume"]]
    
    dates_json = json.dumps(dates)
    prices_json = json.dumps(prices)
    volumes_json = json.dumps(volumes)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <style>
            body {{
                background-color: transparent;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: 'Outfit', sans-serif;
            }}
            #container {{
                width: 100%;
                height: 380px;
            }}
        </style>
    </head>
    <body>
        <div id="container"></div>
        <script>
            const dates = {dates_json};
            const prices = {prices_json};
            const volumes = {volumes_json};
            const ticker = "{ticker}";
            const priceSymbol = "{price_symbol}";

            Highcharts.chart('container', {{
                chart: {{
                    backgroundColor: 'rgba(0,0,0,0)',
                    type: 'area',
                    height: 380,
                    marginRight: 60,
                    marginLeft: 60,
                    style: {{
                        fontFamily: 'Outfit, sans-serif'
                    }}
                }},
                title: {{
                    text: '<b>' + ticker + ' Price & Volume Performance (Last 30 Trading Days)</b>',
                    align: 'left',
                    style: {{
                        color: '#f8fafc',
                        fontSize: '15px',
                        fontWeight: 'bold'
                    }}
                }},
                credits: {{
                    enabled: false
                }},
                xAxis: {{
                    categories: dates,
                    gridLineColor: 'rgba(255, 255, 255, 0.02)',
                    gridLineWidth: 1,
                    labels: {{
                        style: {{
                            color: '#64748b',
                            fontSize: '10px'
                        }}
                    }},
                    lineColor: 'rgba(255,255,255,0.05)',
                    tickColor: 'rgba(255,255,255,0.05)'
                }},
                yAxis: [{{
                    title: {{
                        text: 'Price (' + priceSymbol + ')',
                        style: {{
                            color: '#3b82f6',
                            fontSize: '11px',
                            fontWeight: '600'
                        }}
                    }},
                    gridLineColor: 'rgba(255, 255, 255, 0.02)',
                    labels: {{
                        style: {{
                            color: '#3b82f6'
                        }}
                    }}
                }}, {{
                    title: {{
                        text: 'Volume',
                        style: {{
                            color: '#64748b',
                            fontSize: '11px',
                            fontWeight: '600'
                        }}
                    }},
                    gridLineWidth: 0,
                    labels: {{
                        style: {{
                            color: '#64748b'
                        }}
                    }},
                    opposite: true
                }}],
                legend: {{
                    itemStyle: {{
                        color: '#64748b',
                        fontSize: '11px'
                    }},
                    itemHoverStyle: {{
                        color: '#94a3b8'
                    }},
                    align: 'right',
                    verticalAlign: 'top',
                    y: -10
                }},
                tooltip: {{
                    shared: true,
                    backgroundColor: '#1e222d',
                    borderColor: '#363c4e',
                    borderRadius: 4,
                    style: {{
                        color: '#cbd5e1',
                        fontSize: '12px'
                    }}
                }},
                plotOptions: {{
                    area: {{
                        fillColor: {{
                            linearGradient: {{ x1: 0, y1: 0, x2: 0, y2: 1 }},
                            stops: [
                                [0, 'rgba(59, 130, 246, 0.22)'],
                                [1, 'rgba(59, 130, 246, 0.00)']
                            ]
                        }},
                        marker: {{
                            radius: 3,
                            fillColor: '#3b82f6',
                            lineWidth: 1,
                            lineColor: '#1e222d'
                        }},
                        lineWidth: 3,
                        lineColor: '#3b82f6',
                        threshold: null
                    }}
                }},
                series: [{{
                    name: 'Close Price',
                    type: 'area',
                    data: prices,
                    yAxis: 0,
                    tooltip: {{
                        valuePrefix: priceSymbol
                    }}
                }}, {{
                    name: 'Volume',
                    type: 'column',
                    data: volumes,
                    yAxis: 1,
                    color: 'rgba(148, 163, 184, 0.1)',
                    borderWidth: 0,
                    tooltip: {{
                        valueDecimals: 0
                    }}
                }}]
            }});
        </script>
    </body>
    </html>
    """
    return html
