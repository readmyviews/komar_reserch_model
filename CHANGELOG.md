# Changelog

All notable changes to the **Julian Komar Stock Detective Dashboard** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

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
