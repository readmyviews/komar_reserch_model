import streamlit as st
import yfinance as yf
from dotenv import load_dotenv
import os
import logging
import time

from src.analyzer import resolve_ticker, calculate_metrics
from src.agent import generate_komar_analysis
from src.ui_components import (
    get_glassmorphic_css, 
    get_price_chart, 
    get_growth_chart, 
    render_rating_stars
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
    page_title="Julian Komar Stock Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern dark styles and glassmorphism properties
st.markdown(get_glassmorphic_css(), unsafe_allow_html=True)

# Main Application Title Header
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
    <h1 style="color: #3b82f6; margin-bottom: 0.5rem; font-size: 2.75rem; text-shadow: 0 0 10px rgba(59, 130, 246, 0.25);">🔍 Komar Stock Detective</h1>
    <p style="color: #94a3b8; font-size: 1.05rem; max-width: 800px; margin: 0 auto; line-height: 1.5;">
        Apply seasoned growth investor <b>Julian Komar's</b> specific fundamental, thematic, and institutional liquidity 
        research framework to Indian and US equities. Powered by live Yahoo Finance datasets and Gemini AI.
    </p>
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

# Verify API Keys
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.sidebar.error("⚠️ GEMINI_API_KEY is missing! Add it to your .env file to enable qualitative reasoning.")
else:
    st.sidebar.success("🔑 Gemini API Key configured.")

analyze_btn = st.sidebar.button("Run Detective Analysis 🔍")

# Display quick guidelines in the sidebar
st.sidebar.markdown("""
<br/><hr style="border-color: rgba(255, 255, 255, 0.08);"/>
<h5 style="color: #94a3b8; margin-bottom: 0.5rem;">Julian Komar Core Rules</h5>
<p style="color: #64748b; font-size: 0.775rem; line-height: 1.4;">
1. <b>Hyper-Growth Sales</b>: Targets 20%, 30%, or 40%+ YoY Sales. Value stocks are ignored.<br/>
2. <b>The Story & Theme</b>: Invests in strong catalysts and secular trends (AI, clean energy, SaaS).<br/>
3. <b>Sister Stocks</b>: Avoids "lonely survivors". Direct competitors must show momentum.<br/>
4. <b>Institutional Liquidity</b>: Requires $5M-$10M USD/day for young micro-caps; $20M-$100M USD/day for mature names.
</p>
""", unsafe_allow_html=True)

# Trigger analysis or retrieve from state to optimize rendering (Streamlit session state)
if analyze_btn or "metrics" in st.session_state:
    if not gemini_api_key and not os.getenv("GEMINI_API_KEY"):
        # Attempt fallback to loaded environment key in case of manual entry
        st.error("Please add a `GEMINI_API_KEY` to your `.env` file first.")
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
                    
                with st.spinner("🧠 Step 2: Running Gemini detective to perform thematic research..."):
                    analysis = generate_komar_analysis(stock_name, country, stats)
                    
                # Save details into Streamlit Session State for seamless interactions
                st.session_state["resolved_ticker"] = resolved_ticker
                st.session_state["stats"] = stats
                st.session_state["history"] = history
                st.session_state["analysis"] = analysis
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
    
    # ------------------ Row 1: Glassmorphic Metrics Summary Cards ------------------
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Price card
    price_symbol = "₹" if country == "India" else "$"
    with col1:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">CURRENT PRICE</div>
            <div class="komar-metric-value">{price_symbol}{stats['current_price']:.2f}</div>
            <div class="komar-metric-status">Resolved: {stats['ticker']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. Daily Dollar Volume (Liquidity Check)
    avg_vol = stats['avg_daily_dollar_volume']
    is_liquid = avg_vol >= 5000000.0 # Min micro-cap emerging threshold is $5M USD
    liq_class = "status-positive" if is_liquid else "status-negative"
    liq_text = "PASSED (>$5M)" if is_liquid else "LOW VOLUME"
    with col2:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">DAILY DOLLAR VOLUME</div>
            <div class="komar-metric-value">${avg_vol/1e6:.2f}M USD</div>
            <div class="komar-metric-status {liq_class}">Liquidity: {liq_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 3. YoY Sales Growth (Fundamental Growth Check)
    sales_growth = stats['sales_growth_yoy']
    growth_passed = sales_growth >= 20.0
    growth_class = "status-positive" if growth_passed else "status-negative"
    growth_text = "PASSED (20%+)" if growth_passed else "UNDERPERFORMING"
    with col3:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">YOY SALES GROWTH</div>
            <div class="komar-metric-value">{sales_growth:.1f}%</div>
            <div class="komar-metric-status {growth_class}">{growth_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 4. Rating Stars
    stars_html = render_rating_stars(analysis['rating'])
    with col4:
        st.markdown(f"""
        <div class="komar-card">
            <div class="komar-metric-title">KOMAR RATING</div>
            <div style="margin: 0.15rem 0;">{stars_html}</div>
            <div class="komar-metric-status" style="color:#f59e0b; font-weight:700;">
                Category: {analysis['stock_category']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # ------------------ Row 2: Charts and Visualizations ------------------
    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        st.plotly_chart(get_price_chart(history, resolved_ticker), use_container_width=True)
    with chart_col2:
        st.plotly_chart(get_growth_chart(stats['sales_growth_yoy'], stats['eps_growth_yoy']), use_container_width=True)
        
    # ------------------ Row 3: Gemini Detective Analytical Reports ------------------
    st.markdown("""
    <h3 style="color:#3b82f6; margin-top:1.5rem; margin-bottom: 0.75rem;">🕵️‍♂️ Detective Research Analysis Report</h3>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Fundamental Growth Layer", 
        "🔥 The Story & Catalysts", 
        "👯 Sister Stocks & Theme", 
        "🏁 Quality Check & Verdict"
    ])
    
    with tab1:
        st.markdown(f"##### Stock Categorization: `{analysis['stock_category']}`")
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
else:
    # Warm welcome instruction box
    st.markdown("""
    <div style="padding: 2.5rem; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px dashed rgba(255, 255, 255, 0.08); text-align: center; margin-top: 1rem;">
        <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">🕵️‍♂️ The Detective is Waiting...</h4>
        <p style="color: #64748b; font-size: 0.95rem; max-width: 600px; margin: 0 auto;">
            Configure the stock name and country listing region in the <b>Control Center</b> sidebar, 
            then click <b>Run Detective Analysis 🔍</b> to fetch real-time analytics and launch our qualitative Gemini agent.
        </p>
    </div>
    """, unsafe_allow_html=True)
