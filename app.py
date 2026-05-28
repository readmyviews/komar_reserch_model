# pyrefly: ignore [missing-import]
import streamlit as st
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os
import logging
import time

import streamlit.components.v1 as components
import textwrap
from src.analyzer import resolve_ticker, calculate_metrics
from src.agent import generate_komar_analysis
from src.ui_components import (
    get_glassmorphic_css, 
    get_price_chart, 
    get_growth_chart, 
    render_rating_stars,
    get_highcharts_html
)

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("komar.app")

# Set Page Config for responsive full-screen layouts
st.set_page_config(
    page_title="Pratik Patel Stock Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern dark styles and glassmorphism properties
st.markdown(get_glassmorphic_css(), unsafe_allow_html=True)

# Main Application Title Header
if "analysis" in st.session_state:
    stats = st.session_state["stats"]
    price_symbol = "₹" if st.session_state["last_search_country"] == "India" else "$"
    high_52w = stats.get("fifty_two_week_high", 0.0)
    low_52w = stats.get("fifty_two_week_low", 0.0)
    
    st.markdown(f"""
    <div style="margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.9) 100%); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.15); box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1 style="color: #ffffff; margin: 0; font-size: 2.4rem; font-weight: 800; letter-spacing: -0.02em; display: flex; align-items: center; gap: 0.5rem;">
                    📈 <span style="background: linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{st.session_state["last_search_name"].upper()}</span> 
                    <span style="font-size: 1.1rem; color: #3b82f6; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 600;">{stats['ticker']}</span>
                </h1>
                <p style="color: #64748b; margin: 0.25rem 0 0 0; font-size: 0.95rem; font-weight: 500;">
                    Real-Time Market Analytics & Strategic Detective Intelligence
                </p>
            </div>
            <div style="display: flex; gap: 2rem; align-items: center; flex-wrap: wrap;">
                <div style="text-align: right;">
                    <div style="color: #64748b; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.1rem;">Current Price</div>
                    <div style="color: #3b82f6; font-size: 1.85rem; font-weight: 800; text-shadow: 0 0 10px rgba(59, 130, 246, 0.15);">{price_symbol}{stats['current_price']:.2f}</div>
                </div>
                <div style="width: 1px; height: 35px; background: rgba(255,255,255,0.08);"></div>
                <div style="text-align: right;">
                    <div style="color: #10b981; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.1rem;">52W Highest</div>
                    <div style="color: #10b981; font-size: 1.5rem; font-weight: 700;">{price_symbol}{high_52w:.2f}</div>
                </div>
                <div style="width: 1px; height: 35px; background: rgba(255,255,255,0.08);"></div>
                <div style="text-align: right;">
                    <div style="color: #f43f5e; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.1rem;">52W Lowest</div>
                    <div style="color: #f43f5e; font-size: 1.5rem; font-weight: 700;">{price_symbol}{low_52w:.2f}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar configurations
st.sidebar.markdown("""
<div style="padding: 0.25rem 0; margin-bottom: 1rem;">
    <h3 style="color: #3b82f6; margin: 0; font-size: 1.25rem;">🕵️‍♂️ Control Center</h3>
    <hr style="margin: 0.5rem 0; border-color: rgba(255, 255, 255, 0.08);"/>
</div>
""", unsafe_allow_html=True)

stock_name = st.sidebar.text_input("Stock Name or Ticker Symbol:", value="Adani Power", help="e.g. Adani Power, Nvidia, TSLA, Tata Power")
country = st.sidebar.radio("Country/Listing Region:", options=["India", "US"], index=0, help="India utilizes NSE (.NS suffix); US utilizes Nasdaq/NYSE")

st.sidebar.markdown("<br/>", unsafe_allow_html=True)

# Verify API Keys (Check st.secrets first for deployment, fallback to environment)
gemini_api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not gemini_api_key:
    gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    st.sidebar.error("⚠️ GEMINI_API_KEY is missing! Add it to .streamlit/secrets.toml or your .env file to enable qualitative reasoning.")
    api_configured = False
else:
    api_configured = True

analyze_btn = st.sidebar.button("Run Analysis")

# Trigger analysis or retrieve from state to optimize rendering (Streamlit session state)
if analyze_btn or "metrics" in st.session_state:
    if not api_configured:
        st.error("Please add a valid `GEMINI_API_KEY` to your secrets configuration first.")
    elif not stock_name:
        st.warning("Please enter a valid stock name or ticker symbol.")
    else:
        # Check if the user is triggering a fresh run or reloading
        fresh_run = analyze_btn or "metrics" not in st.session_state or st.session_state.get("last_search_name") != stock_name or st.session_state.get("last_search_country") != country
        
        if fresh_run:
            logger.info(f"Triggering fresh detective analysis pipeline for name: '{stock_name}' in country: '{country}'")
            try:
                with st.spinner("🕵️‍♂️ Step 1: Resolving ticker symbol and fetching yfinance data..."):
                    resolved_ticker = resolve_ticker(stock_name, country)
                    logger.info(f"Resolved symbol: '{resolved_ticker}'")
                    
                    stats = calculate_metrics(resolved_ticker)
                    
                    # Fetch price history for custom Plotly rendering
                    ticker_obj = yf.Ticker(resolved_ticker)
                    history = ticker_obj.history(period="30d")
                    try:
                        news_list = ticker_obj.news
                        if not news_list:
                            news_list = []
                    except Exception:
                        news_list = []
                    
                with st.spinner("🧠 Step 2: Running Gemini detective to perform thematic research..."):
                    analysis = generate_komar_analysis(stock_name, country, stats)
                    
                # Save details into Streamlit Session State for seamless interactions
                st.session_state["resolved_ticker"] = resolved_ticker
                st.session_state["stats"] = stats
                st.session_state["history"] = history
                st.session_state["analysis"] = analysis
                st.session_state["news"] = news_list[:3]
                st.session_state["last_search_name"] = stock_name
                st.session_state["last_search_country"] = country
                st.session_state["metrics"] = True
                
                logger.info(f"Pipeline executed successfully. Results cached in session state for ticker '{resolved_ticker}'")
                
            except Exception as e:
                logger.error(f"Failed to execute pipeline for stock '{stock_name}': {str(e)}", exc_info=True)
                st.error(f"❌ Analysis failed: {str(e)}")
                st.info("💡 Pro-tip: Verify the stock symbol is correct. For Indian equities listed on NSE, use symbols like ADANIPOWER, Reliance, or Tata Power.")

# Draw Dashboard UI if session state contains metrics
if "analysis" in st.session_state:
    stats = st.session_state["stats"]
    analysis = st.session_state["analysis"]
    history = st.session_state["history"]
    resolved_ticker = st.session_state["resolved_ticker"]
    
    # ------------------ Company Overview & News Section (Top of UI) ------------------
    # Task 1: Stock Details Card (Widescreen header card before Company Profile)
    price_symbol = "₹" if st.session_state.get("last_search_country", "India") == "India" else "$"
    high_52w = stats.get("fifty_two_week_high", 0.0)
    low_52w = stats.get("fifty_two_week_low", 0.0)
    
    header_html = f"""
    <div class="komar-card" style="margin-bottom: 1.5rem; padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h3 style="color: #3b82f6; margin: 0; font-size: 1.45rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem;">
                    🏢 {st.session_state.get('last_search_name', '').upper()} <span style="font-size: 0.95rem; color: #64748b; font-weight: 600;">({stats['ticker']})</span>
                </h3>
            </div>
            <div style="display: flex; gap: 1.5rem; align-items: center;">
                <div>
                    <span style="color: #64748b; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; display: block; margin-bottom: 0.1rem;">Current Price</span>
                    <span style="color: #ffffff; font-size: 1.35rem; font-weight: 800;">{price_symbol}{stats['current_price']:.2f}</span>
                </div>
                <div style="width: 1px; height: 25px; background: rgba(255,255,255,0.08);"></div>
                <div>
                    <span style="color: #10b981; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; display: block; margin-bottom: 0.1rem;">52W High</span>
                    <span style="color: #10b981; font-size: 1.35rem; font-weight: 700;">{price_symbol}{high_52w:.2f}</span>
                </div>
                <div style="width: 1px; height: 25px; background: rgba(255,255,255,0.08);"></div>
                <div>
                    <span style="color: #f43f5e; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; display: block; margin-bottom: 0.1rem;">52W Low</span>
                    <span style="color: #f43f5e; font-size: 1.35rem; font-weight: 700;">{price_symbol}{low_52w:.2f}</span>
                </div>
            </div>
        </div>
    </div>
    """
    header_html_flat = "\n".join(line.strip() for line in header_html.split("\n"))
    st.markdown(header_html_flat, unsafe_allow_html=True)

    col_overview, col_news = st.columns([2, 1])
    
    with col_overview:
        strengths_html = "".join(f"<li style='margin-bottom: 0.35rem; color:#cbd5e1;'><span style='color:#10b981; margin-right: 0.5rem;'>✓</span>{s}</li>" for s in analysis.get('key_strengths', []))
        weaknesses_html = "".join(f"<li style='margin-bottom: 0.35rem; color:#cbd5e1;'><span style='color:#f43f5e; margin-right: 0.5rem;'>✗</span>{w}</li>" for w in analysis.get('key_weaknesses', []))
        
        st.markdown(f"""
        <div class="komar-card" style="margin-bottom: 1.5rem; min-height: 250px;">
            <h4 style="color: #3b82f6; margin-top: 0; margin-bottom: 0.75rem; font-size: 1.25rem;">🏢 Company Profile & Strategic Overview</h4>
            <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.25rem;">
                {analysis.get('company_brief', 'No dynamic profile summary available.')}
            </p>
            <div style="display: flex; gap: 1.5rem; width: 100%; margin-top: 0.5rem;">
                <div style="flex: 1; background: rgba(16, 185, 129, 0.02); border: 1px solid rgba(16, 185, 129, 0.08); padding: 0.85rem 1.1rem; border-radius: 8px;">
                    <div style="color: #10b981; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">💪 Core Strengths</div>
                    <ul style="margin: 0; padding: 0; list-style-type: none; font-size: 0.875rem;">
                        {strengths_html if strengths_html else "<li style='color:#64748b;'>No key strengths reported.</li>"}
                    </ul>
                </div>
                <div style="flex: 1; background: rgba(244, 63, 94, 0.02); border: 1px solid rgba(244, 63, 94, 0.08); padding: 0.85rem 1.1rem; border-radius: 8px;">
                    <div style="color: #f43f5e; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">⚠️ Key Weaknesses</div>
                    <ul style="margin: 0; padding: 0; list-style-type: none; font-size: 0.875rem;">
                        {weaknesses_html if weaknesses_html else "<li style='color:#64748b;'>No key weaknesses reported.</li>"}
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_news:
        news_html = ""
        news_list = st.session_state.get("news", [])
        if news_list:
            for item in news_list[:3]:
                # Dynamic yfinance news schema nested & flat resolver
                content = item.get("content", item)
                
                title = content.get("title")
                if not title:
                    title = item.get("title", "News Headline")
                    
                link = "#"
                click_through = content.get("clickThroughUrl")
                canonical = content.get("canonicalUrl")
                if isinstance(click_through, dict):
                    link = click_through.get("url", "#")
                elif isinstance(canonical, dict):
                    link = canonical.get("url", "#")
                else:
                    link = item.get("link", "#")
                if not link:
                    link = "#"
                    
                publisher = "Source"
                provider = content.get("provider")
                if isinstance(provider, dict):
                    publisher = provider.get("displayName", "Source")
                else:
                    publisher = item.get("publisher", "Source")
                if not publisher:
                    publisher = "Source"
                
                # Flat string representation to prevent Markdown 4-space code block rendering bugs
                news_html += f'<div style="margin-bottom: 0.85rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 0.5rem;">' \
                             f'<a href="{link}" target="_blank" style="color: #2962ff; text-decoration: none; font-weight: 600; font-size: 0.9rem; line-height: 1.4; display: block;">🔗 {title}</a>' \
                             f'<span style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-top: 0.25rem; display: block;">📰 {publisher}</span>' \
                             f'</div>'
        else:
            news_html = "<p style='color: #64748b; font-size: 0.9rem; margin-top: 1rem;'>No recent news or updates available.</p>"
            
        st.markdown(f"""
        <div class="komar-card" style="margin-bottom: 1.5rem; min-height: 250px;">
            <h4 style="color: #2962ff; margin-top: 0; margin-bottom: 0.75rem; font-size: 1.25rem;">📰 Recent Updates & News</h4>
            <div style="max-height: 200px; overflow-y: auto; padding-right: 0.25rem;">
                {news_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # ------------------ Row 1: Glassmorphic Metrics Summary Cards (Row 1) ------------------
    price_symbol = "₹" if country == "India" else "$"
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Price card
    with col1:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">CURRENT PRICE</div>
            <div class="komar-metric-value">{price_symbol}{stats['current_price']:.2f}</div>
            <div class="komar-metric-status">Resolved: {stats['ticker']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. Optimal Buying Range Card
    buy_range_val = analysis.get('buying_range', 'Calculating...')
    buy_status = analysis.get('buying_range_status', 'N/A')
    
    # Format status colors nicely
    buy_status_lower = buy_status.lower()
    if "buy" in buy_status_lower or "zone" in buy_status_lower or "passed" in buy_status_lower:
        buy_status_class = "status-positive"
    elif "pullback" in buy_status_lower or "wait" in buy_status_lower or "retracement" in buy_status_lower:
        buy_status_class = "status-negative"
    else:
        buy_status_class = ""
        
    with col2:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">OPTIMAL BUYING RANGE</div>
            <div class="komar-metric-value" style="font-size:1.45rem; line-height:2.1rem;">{buy_range_val}</div>
            <div class="komar-metric-status {buy_status_class}">Status: {buy_status}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 3. Market Cap Card
    mcap_native = stats.get('market_cap', 0.0)
    if mcap_native >= 1e12:
        mcap_text = f"{price_symbol}{mcap_native/1e12:.2f}T"
    elif mcap_native >= 1e9:
        mcap_text = f"{price_symbol}{mcap_native/1e9:.2f}B"
    elif mcap_native >= 1e6:
        mcap_text = f"{price_symbol}{mcap_native/1e6:.2f}M"
    else:
        mcap_text = f"{price_symbol}{mcap_native:,.2f}"
        
    with col3:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">MARKET CAPITALIZATION</div>
            <div class="komar-metric-value">{mcap_text}</div>
            <div class="komar-metric-status">Native Valuation</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 4. Rating Card (out of 10)
    stars_html = render_rating_stars(analysis['rating'])
    with col4:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">PATEL RATING</div>
            <div style="margin: 0.1rem 0;">{stars_html}</div>
            <div class="komar-metric-status" style="color:#f59e0b; font-weight:700;">
                Score: {analysis['rating']}/10 ({analysis['stock_category']})
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ------------------ Row 2: Glassmorphic Metrics Summary Cards (Row 2) ------------------
    col2_1, col2_2, col2_3, col2_4 = st.columns(4)
    
    # 1. Sales Growth Card
    sales_growth = stats['sales_growth_yoy']
    growth_passed = sales_growth >= 20.0
    growth_class = "status-positive" if growth_passed else "status-negative"
    growth_text = "PASSED (20%+)" if growth_passed else "LOW GROWTH"
    with col2_1:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">YOY SALES GROWTH</div>
            <div class="komar-metric-value">{sales_growth:.1f}%</div>
            <div class="komar-metric-status {growth_class}">Patel Threshold: {growth_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. EPS Growth Card
    eps_growth = stats['eps_growth_yoy']
    eps_passed = eps_growth >= 20.0
    eps_class = "status-positive" if eps_passed else "status-negative"
    eps_text = "PASSED (20%+)" if eps_passed else "LOW EARNINGS"
    with col2_2:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">YOY EPS GROWTH</div>
            <div class="komar-metric-value">{eps_growth:.1f}%</div>
            <div class="komar-metric-status {eps_class}">Patel Threshold: {eps_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Daily Volume (Localized native AND USD)
    avg_vol_native = stats.get('avg_daily_volume_native', stats['avg_daily_dollar_volume'])
    if avg_vol_native >= 1e9:
        vol_native_text = f"{price_symbol}{avg_vol_native/1e9:.2f}B"
    else:
        vol_native_text = f"{price_symbol}{avg_vol_native/1e6:.2f}M"
        
    avg_vol_usd = stats['avg_daily_dollar_volume']
    is_liquid = avg_vol_usd >= 5000000.0 # Emerging micro-cap threshold
    liq_class = "status-positive" if is_liquid else "status-negative"
    liq_text = "LIQUID" if is_liquid else "ILLIQUID"
    
    with col2_3:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">DAILY DOLLAR VOLUME</div>
            <div class="komar-metric-value">{vol_native_text} <span style="font-size:1rem; color:#64748b;">/ ${avg_vol_usd/1e6:.1f}M USD</span></div>
            <div class="komar-metric-status {liq_class}">Patel Liquidity: {liq_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Moving Average Trend Card & 4 Market Phases
    sma_above_all = stats.get('is_above_50_sma', False) and stats.get('is_above_200_sma', False)
    trend_class = "status-positive" if sma_above_all else "status-negative"
    trend_text = "BULLISH UPTREND" if sma_above_all else "NEUTRAL / BEARISH"
    
    phase_name = stats.get("market_phase", "Accumulation")
    if phase_name == "Accumulation":
        phase_badge_style = "background: rgba(59, 130, 246, 0.12); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3);"
    elif phase_name == "Uptrend":
        phase_badge_style = "background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3);"
    elif phase_name == "Distribution":
        phase_badge_style = "background: rgba(234, 179, 8, 0.12); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.3);"
    else: # Downtrend
        phase_badge_style = "background: rgba(244, 63, 94, 0.12); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.3);"
        
    with col2_4:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">TECHNICAL TREND STATUS</div>
            <div class="komar-metric-value {trend_class}" style="font-size: 1.55rem; line-height: 1.8rem; margin-bottom: 0.25rem;">{trend_text}</div>
            <div style="margin-top: 0.35rem; margin-bottom: 0.1rem;">
                <span style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; margin-right: 0.5rem; letter-spacing: 0.05em;">Phase:</span>
                <span style="font-size: 0.85rem; font-weight: 700; border-radius: 4px; padding: 0.2rem 0.5rem; {phase_badge_style}">{phase_name}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ------------------ Row 2.5: Glassmorphic EVA and MVA KPI Cards ------------------
    col_eva, col_mva = st.columns(2)
    
    # Format EVA
    eva_val = stats.get("eva_native", 0.0)
    eva_class = "status-positive" if eva_val >= 0 else "status-negative"
    if abs(eva_val) >= 1e12:
        eva_text = f"{price_symbol}{eva_val/1e12:.2f}T"
    elif abs(eva_val) >= 1e9:
        eva_text = f"{price_symbol}{eva_val/1e9:.2f}B"
    elif abs(eva_val) >= 1e6:
        eva_text = f"{price_symbol}{eva_val/1e6:.2f}M"
    else:
        eva_text = f"{price_symbol}{eva_val:,.2f}"
        
    # Format MVA
    mva_val = stats.get("mva_native", 0.0)
    mva_class = "status-positive" if mva_val >= 0 else "status-negative"
    if abs(mva_val) >= 1e12:
        mva_text = f"{price_symbol}{mva_val/1e12:.2f}T"
    elif abs(mva_val) >= 1e9:
        mva_text = f"{price_symbol}{mva_val/1e9:.2f}B"
    elif abs(mva_val) >= 1e6:
        mva_text = f"{price_symbol}{mva_val/1e6:.2f}M"
    else:
        mva_text = f"{price_symbol}{mva_val:,.2f}"

    with col_eva:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">ECONOMIC VALUE ADDED (EVA)</div>
            <div class="komar-metric-value {eva_class}">{eva_text}</div>
            <div class="komar-metric-status">NOPAT - (Invested Capital * WACC)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_mva:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">MARKET VALUE ADDED (MVA)</div>
            <div class="komar-metric-value {mva_class}">{mva_text}</div>
            <div class="komar-metric-status">Market Cap - Book Value of Equity</div>
        </div>
        """, unsafe_allow_html=True)
        
    # ------------------ Row 3: Charts and Visualizations ------------------
    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        components.html(get_highcharts_html(history, resolved_ticker, price_symbol), height=390)
    with chart_col2:
        st.plotly_chart(get_growth_chart(stats['sales_growth_yoy'], stats['eps_growth_yoy']), width="stretch")
        
    # ------------------ Row 3.5: Historical Performance & Financial Growth Section ------------------
    verdict = stats.get("performance_verdict", "Average")
    if verdict == "Good":
        verdict_color = "#10b981"
        verdict_bg = "rgba(16, 185, 129, 0.05)"
        verdict_border = "rgba(16, 185, 129, 0.2)"
    elif verdict == "Bad":
        verdict_color = "#f43f5e"
        verdict_bg = "rgba(244, 63, 94, 0.05)"
        verdict_border = "rgba(244, 63, 94, 0.2)"
    else:
        verdict_color = "#eab308"
        verdict_bg = "rgba(234, 179, 8, 0.05)"
        verdict_border = "rgba(234, 179, 8, 0.2)"

    def fmt_ret(val):
        if val is None:
            return "N/A", "#64748b"
        color = "#10b981" if val >= 0 else "#f43f5e"
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}%", color

    r1m_text, r1m_color = fmt_ret(stats.get("return_1m"))
    r3m_text, r3m_color = fmt_ret(stats.get("return_3m"))
    r6m_text, r6m_color = fmt_ret(stats.get("return_6m"))
    r1y_text, r1y_color = fmt_ret(stats.get("return_1y"))
    r5y_text, r5y_color = fmt_ret(stats.get("return_5y"))

    sales_growth = stats.get("sales_growth_yoy", 0.0)
    rev_growth = stats.get("revenue_growth", 0.0)
    net_profit = stats.get("net_profit_margin", 0.0)

    perf_html = f"""
    <div class="komar-card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem;">
            <h4 style="color: #3b82f6; margin: 0; font-size: 1.25rem;">📈 Historical Performance & Financial Growth Overview</h4>
            <div style="background: {verdict_bg}; border: 1px solid {verdict_border}; padding: 0.4rem 1rem; border-radius: 6px; display: flex; align-items: center; gap: 0.75rem;">
                <span style="color: #64748b; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Automated Verdict:</span>
                <span style="color: {verdict_color}; font-weight: 800; font-size: 0.95rem; text-transform: uppercase;">{verdict}</span>
            </div>
        </div>
        
        <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; width: 100%;">
            <div style="flex: 1; min-width: 300px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px;">
                <div style="color: #3b82f6; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem;">📅 Price Horizon Returns</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">1 Month Return:</span>
                    <span style="font-weight: 700; color: {r1m_color}">{r1m_text}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">3 Months Return:</span>
                    <span style="font-weight: 700; color: {r3m_color}">{r3m_text}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">6 Months Return:</span>
                    <span style="font-weight: 700; color: {r6m_color}">{r6m_text}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">1 Year Return:</span>
                    <span style="font-weight: 700; color: {r1y_color}">{r1y_text}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span style="color: #64748b;">5 Years Return:</span>
                    <span style="font-weight: 700; color: {r5y_color}">{r5y_text}</span>
                </div>
            </div>
            
            <div style="flex: 1; min-width: 300px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px;">
                <div style="color: #10b981; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem;">📊 Financial Growth Rates</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">YoY Sales Growth:</span>
                    <span style="font-weight: 700; color: {'#10b981' if sales_growth >= 20.0 else '#cbd5e1'}">{sales_growth:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">YoY Revenue Growth:</span>
                    <span style="font-weight: 700; color: {'#10b981' if rev_growth >= 20.0 else '#cbd5e1'}">{rev_growth:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span style="color: #64748b;">Net Profit Margin:</span>
                    <span style="font-weight: 700; color: {'#10b981' if net_profit >= 15.0 else '#cbd5e1'}">{net_profit:.1f}%</span>
                </div>
            </div>
        </div>
    </div>
    """
    perf_html_flat = "\n".join(line.strip() for line in perf_html.split("\n"))
    st.markdown(perf_html_flat, unsafe_allow_html=True)
        
    # ------------------ Row 4: Gemini Detective Analytical Reports ------------------
    st.markdown("""
    <h3 style="color:#3b82f6; margin-top:1.5rem; margin-bottom: 0.75rem;">🕵️‍♂️ Detective Research Analysis Report</h3>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Fundamental Growth Layer", 
        "🔥 The Story & Catalysts", 
        "👯 Sister Stocks & Theme", 
        "🏁 Quality Check & Verdict",
        "🎯 Rating Decision Scorecard"
    ])
    
    with tab1:
        st.markdown(f"##### Stock Categorization: <span class='komar-badge'>{analysis['stock_category']}</span>", unsafe_allow_html=True)
        st.write(analysis['fundamental_layer_details'])
        
    with tab2:
        st.write(analysis['story_layer_details'])
        
    with tab3:
        st.write(analysis['sister_stocks_details'])
        
    with tab4:
        st.markdown("##### Institutional Liquidity Assessment")
        st.write(analysis['liquidity_details'])
        st.markdown("<hr style='border-color:rgba(255,255,255,0.05)'/>", unsafe_allow_html=True)
        st.markdown("##### Final Detective Verdict")
        st.info(analysis['verdict'])
        
    with tab5:
        st.markdown(f"### Pratik Patel Decision Score: `{analysis['rating']}/10`")
        st.markdown("Here is the exact scorecard breakdown leading to this detective analysis rating:")
        
        # Display Gemini rating breakdown list
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.4); padding: 1.5rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem;">
            {analysis['rating_breakdown']}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### Technical Moving Averages Support Card")
        # Build technical indicators table
        sma50_icon = "✅ Above" if stats['is_above_50_sma'] else "❌ Below"
        sma200_icon = "✅ Above" if stats['is_above_200_sma'] else "❌ Below"
        
        st.table(pd.DataFrame({
            "Indicator / Metric": ["Current Stock Price", "50-Day Simple Moving Average (SMA)", "200-Day Simple Moving Average (SMA)"],
            "Value": [
                f"{price_symbol}{stats['current_price']:.2f}",
                f"{price_symbol}{stats['sma_50']:.2f}",
                f"{price_symbol}{stats['sma_200']:.2f}"
            ],
            "Trend Status": ["Base Reference", sma50_icon, sma200_icon]
        }))
else:
    # Highly attractive, premium glassmorphic momentum strategy welcome page
    welcome_html = """
    <div style="margin-top: 1rem; font-family: 'Outfit', sans-serif;">
        <!-- Large beautiful glassmorphic welcome card -->
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(59, 130, 246, 0.15); border-radius: 16px; padding: 2.5rem; text-align: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-bottom: 2rem;">
            <h1 style="color: #3b82f6; margin-bottom: 0.5rem; font-size: 3rem; font-weight: 800; text-shadow: 0 0 15px rgba(59, 130, 246, 0.3);">🔍 PATEL STOCK DETECTIVE</h1>
            <p style="color: #cbd5e1; font-size: 1.15rem; max-width: 750px; margin: 0 auto; line-height: 1.6; font-weight: 400;">
                Apply seasoned growth investor <b>Pratik Patel's</b> rigorous, institutional-grade 
                fundamental and thematic momentum research framework. Powered by live datasets and GenAI.
            </p>
        </div>
        
        <!-- Strategy Grid Section Title -->
        <h3 style="color: #ffffff; text-align: center; margin-bottom: 1.5rem; font-weight: 700; font-size: 1.4rem; text-transform: uppercase; letter-spacing: 0.05em;">
            🛡️ Core Pillars of Patel's Momentum Strategy
        </h3>
        
        <!-- 2x2 Grid using clean flex/columns container -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem;">
            
            <!-- Pillar 1: Hyper Growth -->
            <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
                <div style="color: #3b82f6; font-size: 1.3rem; font-weight: 800; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    ⚡ <span>Hyper-Growth Fundamentals</span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Targets companies with explosive <b>sales growth of 20%, 30%, or 40%+ YoY</b>. High-growth value-creation metrics (EVA/MVA) are prioritized over standard PE values.
                </p>
            </div>

            <!-- Pillar 2: Thematic Catalysts -->
            <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
                <div style="color: #10b981; font-size: 1.3rem; font-weight: 800; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    🔮 <span>Secular Catalysts & Story</span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Focuses on strong qualitative trends, technological innovations, and powerful tailwinds (e.g. Artificial Intelligence, SaaS, clean energy, national infrastructure).
                </p>
            </div>

            <!-- Pillar 3: Sister Stocks -->
            <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
                <div style="color: #eab308; font-size: 1.3rem; font-weight: 800; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    👯 <span>Sister Stocks & Theme</span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Avoids isolated success stories. Requires other industry competitors and sector themes to also display strong fundamental and technical price action.
                </p>
            </div>

            <!-- Pillar 4: Institutional Liquidity -->
            <div style="background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
                <div style="color: #f43f5e; font-size: 1.3rem; font-weight: 800; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    💧 <span>Institutional Liquidity</span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Ensures safe entries and exits for institutions by enforcing strict Average Daily Dollar Volume thresholds ($5M-$10M USD for micro-caps, $20M-$100M+ USD for mature themes).
                </p>
            </div>
            
        </div>

        <!-- Active Call to Action Section -->
        <div style="background: rgba(59, 130, 246, 0.04); border: 1px dashed rgba(59, 130, 246, 0.25); border-radius: 12px; padding: 1.5rem; text-align: center; max-width: 680px; margin: 0 auto;">
            <h4 style="color: #3b82f6; margin-top: 0; margin-bottom: 0.35rem; font-weight: 700; font-size: 1.1rem; text-transform: uppercase;">🕵️‍♂️ The Detective is Ready</h4>
            <p style="color: #cbd5e1; font-size: 0.9rem; margin: 0; line-height: 1.525;">
                Configure your stock name and country region in the <b>Control Center</b> sidebar on the left, then click the blue <b>Run Analysis</b> button to fetch live data and start the AI Detective audit!
            </p>
        </div>
    </div>
    """
    welcome_html_flat = "\n".join(line.strip() for line in welcome_html.split("\n"))
    st.markdown(welcome_html_flat, unsafe_allow_html=True)
