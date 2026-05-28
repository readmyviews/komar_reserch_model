# Changelog

All notable changes to the **Pratik Patel Stock Detective Dashboard** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-05-28

### Changed
- **30-Day Calendar Lookback Refactoring**:
  - Re-verified and optimized the `"30-Day Performance"` calculation logic in the backend (`src/analyzer.py`). Replaced the static 30 trading days lookback slice (`iloc[-30]`) with exactly 30 calendar days lookback utilizing `pd.Timedelta(days=30)` and nearest DatetimeIndex alignment.
- **UI Metrics Card Removal & Grid Re-Alignment**:
  - Removed the `"30-DAY PERFORMANCE"` metrics card from Row 1 of the glassmorphic cards in `app.py`.
  - Re-aligned the Row 1 grid layout to exactly 4 symmetric columns (`col1`, `col2`, `col3`, `col4`) for a perfectly balanced visual representation.
- **Gemini Sidebar Success Message Cleanup**:
  - Removed the `"🔑 Gemini API Key configured."` sidebar success notification from `app.py` for a cleaner sidebar interface.
- **Dynamic Header with 52-Week Pricing Metrics**:
  - Replaced the static `"Patel Stock Detective"` header with an elegant, dynamic header component displaying the resolved stock name, ticker symbol, current price, and 52-week highest and lowest prices when a search is active.
- **Highcharts Integration for Stock Charting**:
  - Replaced the Plotly stock price history chart with an advanced Highcharts area and translucent column volume overlay chart, rendered beautifully using Streamlit iframe components.
- **Premium Glassmorphic Welcome Portal**:
  - Replaced the basic static headers and "Detective is Waiting" instruction card before stock searches with a premium, widescreen glassmorphic welcome page highlighting the four core strategy pillars (Hyper-Growth, Catalysts, Sister Stocks, and Liquidity) of Pratik Patel's framework.

### Fixed
- **Robust yfinance News Parser**:
  - Fixed an `AttributeError` crash on `NoneType` when parsing nested `clickThroughUrl`, `canonicalUrl`, or `provider` keys in the raw `yfinance` news payload. Added robust `isinstance` dictionary type checks.
- **Multi-Stage Market Capitalization Fallbacks**:
  - Implemented a robust, multi-stage fallback mechanism in `src/analyzer.py` to prevent `0.00` market capitalization readings when `yfinance`'s primary `.info` scraper fails. The engine sequentially tries `ticker.info.get("marketCap")`, fast info `fast_info.market_cap`, `ticker.info.get("sharesOutstanding") * price`, fast info `fast_info.shares_outstanding * price`, and finally `balance_sheet["Ordinary Shares Number"] * price`.
- **Welcome Portal Markdown Indentation Fix**:
  - Wrapped the multi-line welcome portal HTML string in `textwrap.dedent` to strip leading Python indentation spacing, resolving the Streamlit markdown parser bug that was rendering the welcome screen as raw text inside a code block.

## [1.1.0] - 2026-05-27

### Added
- **Global Branding Update**:
  - Rebranded all user-facing descriptions, headers, and dashboard page configs to `"Pratik Patel"`.
  - Re-aligned Google Gemini system prompt instructions so qualitative analysis evaluates stocks according to *Pratik Patel's* growth framework.
- **Top-Level Company Profile & News Widget**:
  - Expanded Gemini qualitative analysis to dynamically generate a company brief and a bulleted list of 2-3 key strengths and weaknesses.
  - Programmed dynamic news retrieval pulling the top 3 latest stock news articles from yfinance directly.
  - Implemented a wide dual-column top layout panel display.
- **EVA & MVA Financial Calculations**:
  - Coded dynamic WACC, NOPAT, Invested Capital, and Book Value estimations pulling from yfinance statements.
  - Designed beautiful glassmorphic KPI card overlays displaying native Economic Value Added (EVA) and Market Value Added (MVA) valuations.
- **4 Market Phases Technical Indicator**:
  - Programmed rolling Pandas math calculating SMA200 and its 20-day slope rate of change.
  - Implemented parameterized phase classifications (*Accumulation*, *Uptrend*, *Distribution*, *Downtrend*) showing a neon-colored status badge.
- **Automated Verification Extensions**:
  - Added new comprehensive test file `tests/test_financials_and_phases.py` verifying all mathematical cost metrics and phase classification boundaries. All 13 tests pass.

## [1.0.0] - 2026-05-26

### Added
- **Core Streamlit Dashboard Layout (`app.py`)**:
  - Implemented sleek dark theme and sidebar controls for entering the stock name and country region (US/India).
  - Configured Streamlit session state caching to prevent redundant yfinance/LLM execution on re-runs.
- **Quantitative Metrics Analyzer (`src/analyzer.py`)**:
  - Added smart ticker symbol resolution (appends `.NS` suffix automatically for NSE-listed Indian equities like `Adani Power` -> `ADANIPOWER.NS`).
  - Integrated live data fetching using the `yfinance` library.
  - Implemented Average Daily Dollar Volume computation over a 30-day window to verify institutional liquidity thresholds ($5M-$10M USD for emerging themes, $20M-$100M USD for mature assets).
  - Programmed Year-over-Year (YoY) Sales and EPS growth calculations using quarterly reports with annual statements as a fallback.
  - Optimized metrics computation with an in-memory `lru_cache` to minimize network overhead.
- **Gemini Detective Reasoning Agent (`src/agent.py`)**:
  - Programmed structural LLM wrapper utilizing the official `google-genai` SDK and `gemini-2.5-flash` model.
  - Configured structured response validation with Pydantic JSON schemas to guarantee API output consistency.
  - Designed system instructions enforcing Julian Komar's thematic research methodology (growth checkpoints, catalyst detection, sister stocks momentum, and liquidity constraints).
- **Glassmorphic UI Widgets & Plots (`src/ui_components.py`)**:
  - Added custom CSS overrides injecting glassmorphic properties, glowing button styles, and status metric elements.
  - Built interactive neon Plotly stock price history overlaying a translucent daily volume chart.
  - Designed a YoY Sales/EPS growth bar chart visualizer comparing corporate financials to Komar's 20% growth entry threshold.
  - Coded custom HTML star rating renderer.
- **Automated Verification Suite (`tests/`)**:
  - Implemented 7 unit test cases including dependencies setup verification (`tests/test_env.py`), quantitative financial metrics calculation (`tests/test_analyzer.py`), mocked LLM prompt execution (`tests/test_agent.py`), custom HTML/Plotly generator validation (`tests/test_ui.py`), and full app assembly routing verification (`tests/test_app.py`).
