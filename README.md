# Julian Komar Stock Detective Dashboard

A premium Python-based analytics dashboard that applies seasoned growth investor **Julian Komar's** fundamental, thematic, and institutional liquidity research framework to US and Indian equities. The application is powered by live market datasets via `yfinance` and qualitative reasoning agents utilizing **Google Gemini AI**.

---

## Key Features

1. **Fundamental Growth Layer**: Computes Year-over-Year (YoY) quarterly and annual Sales and EPS growth percentages, comparing company metrics to Julian Komar's 20%, 30%, and 40%+ expansion check gates. Automatically classifies stocks into **CANSLIM Stock**, **Sales Grower**, or **Story Stock**.
2. **Secular Story & Thematic Catalyst Layer**: Integrates the `google-genai` SDK and `gemini-2.5-flash` model to analyze business models, detect industry-specific catalysts (e.g. AI, SaaS, robotics, clean energy), and identify secular institutional demand.
3. **Sister Stock Sector Alignment**: Employs Gemini to verify sector momentum by locating 3–4 corresponding competitor/sister stocks locally and globally showing strong momentum.
4. **Institutional Liquidity Check**: Calculates Average Daily Dollar Volume over a 30-day window and validates them against Komar's strict institutional risk limits ($5M–$10M USD for young micro-caps; $20M–$100M USD for mature themes).
5. **Modern Glassmorphic UI**: Designed a gorgeous dark-themed Streamlit layout complete with glowing metrics indicators, interactive neon Plotly price/volume area charts, and financial growth bar charts.

---

## Code Architecture

```text
d:\Work\komar\
├── .gitignore
├── requirements.txt            # Package dependencies
├── .env                        # Environment variables (GEMINI_API_KEY)
├── app.py                      # Master Streamlit dashboard entrypoint
├── src/
│   ├── __init__.py
│   ├── analyzer.py             # yfinance metrics resolver and cache processor
│   ├── agent.py                # Gemini detective agent with structured JSON output
│   └── ui_components.py        # Glassmorphic CSS overrides and Plotly indicators
└── tests/
    ├── test_env.py             # Verifies python packages import correctly
    ├── test_analyzer.py        # Verifies ticker resolving and math calculations
    ├── test_agent.py           # Verifies Gemini LLM mocking and structured schemas
    ├── test_ui.py              # Verifies CSS structures and Plotly figures
    └── test_app.py             # Verifies app coordination imports
```

---

## Execution Steps

### 1. Prerequisites
Ensure you have **Python 3.10 or newer** installed on your operating system.

### 2. Installation
Clone or navigate to the workspace directory, then install all project dependencies specified in the requirements file:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory of the project:
```bash
# Create a .env file containing your Gemini API key:
echo "GEMINI_API_KEY=your_actual_gemini_api_key_here" > .env
```

### 4. Running the Dashboard
Launch the interactive Streamlit server from the project root:
```bash
streamlit run app.py
```
This will automatically open the application in your default web browser at `http://localhost:8501`.

---

## Running Automated Tests

We maintain a complete test suite under the `tests/` directory ensuring high code reliability. To execute the automated tests, run:
```bash
# In Windows PowerShell:
$env:PYTHONPATH="." ; pytest

# In Bash / macOS / Linux:
PYTHONPATH=. pytest
```
All unit tests should pass successfully.
