# Dynamic Stock Header, Historical Performance, and Growth Metrics Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Implement a new widescreen stock detail header block, compute 1M/3M/6M/1Y/5Y calendar-lookback price returns, retrieve YoY revenue growth and Net Profit margin, build an automated backend review verdict logic ("Good", "Average", "Bad"), and render these details in high-fidelity cards inside the Streamlit dashboard.

**Architecture:** 
1. **Data Layer (`src/analyzer.py`)**: Expand history lookback from 250 days to 5 years (`period="5y"`). Compute calendar-based lookbacks for 1M/3M/6M/1Y/5Y return horizons. Fetch latest quarterly YoY Revenue Growth and Net Profit margin with financial statement fallbacks.
2. **Reviewer Engine (`src/analyzer.py`)**: Write `evaluate_performance_growth` utilizing score-based baseline thresholds to compute the final verdict ("Good", "Average", "Bad").
3. **UI Layout Layer (`app.py`)**:
   - Render a new stock detail summary card containing Name, Price, 52W High, and 52W Low directly above the `🏢 Company Profile & Strategic Overview` block.
   - Render a new dual-column `Historical Performance & Growth Metrics` grid immediately before the `🕵️‍♂️ Detective Research Analysis Report` tabs.

**Tech Stack:** Streamlit, Pandas, yfinance, Outfit Typography.

---

## Proposed Tasks

### Task 1: Extend yfinance History and Fetch Growth Stats

**Files:**
- Modify: [analyzer.py](file:///d:/Work/komar/src/analyzer.py)
- Test: [test_analyzer.py](file:///d:/Work/komar/tests/test_analyzer.py)

**Step 1: Write the failing test**
Create a test case inside `tests/test_analyzer.py` verifying that the return dictionary includes historical horizons and growth stats.

```python
def test_extended_metrics():
    metrics = calculate_metrics("NVDA")
    assert "return_1m" in metrics
    assert "return_3m" in metrics
    assert "return_6m" in metrics
    assert "return_1y" in metrics
    assert "return_5y" in metrics
    assert "revenue_growth" in metrics
    assert "net_profit_margin" in metrics
    assert "performance_verdict" in metrics
    assert metrics["performance_verdict"] in ["Good", "Average", "Bad"]
```

**Step 2: Run test to verify it fails**
Run: `$env:PYTHONPATH="."; pytest tests/test_analyzer.py -k test_extended_metrics`
Expected: FAIL with `KeyError` or `AssertionError` for new metrics keys.

**Step 3: Implement minimal code to make the test pass**
1. In `src/analyzer.py`, change historical load from `period="250d"` to `period="5y"`.
2. Add lookback helper calculation:
```python
def _calculate_calendar_return(history: pd.DataFrame, latest_date: pd.Timestamp, days_ago: int) -> float:
    first_date = history.index[0]
    if (latest_date - first_date).days >= days_ago:
        target_date = latest_date - pd.Timedelta(days=days_ago)
        idx = history.index.get_indexer([target_date], method="nearest")[0]
        if idx != -1:
            price_then = float(history["Close"].iloc[idx])
            if price_then > 0:
                current_price = float(history["Close"].iloc[-1])
                return float(((current_price - price_then) / price_then) * 100)
    return None
```
3. Extract `revenue_growth` and `net_profit_margin` from `ticker.info` or fallbacks:
```python
        # Fetch Revenue Growth
        revenue_growth = None
        try:
            revenue_growth = float(ticker.info.get("revenueGrowth") or 0.0) * 100.0
        except Exception:
            pass
        if not revenue_growth or revenue_growth == 0.0:
            revenue_growth = sales_growth_yoy if sales_growth_yoy is not None else 0.0

        # Fetch Net Profit Margin
        net_profit_margin = None
        try:
            net_profit_margin = float(ticker.info.get("profitMargins") or 0.0) * 100.0
        except Exception:
            pass
        if not net_profit_margin or net_profit_margin == 0.0:
            try:
                # Fallback: calculate Net Profit Margin from financials: Net Income / Total Revenue
                net_income = quarterly_financials.loc["Net Income"].iloc[0]
                revenue = quarterly_financials.loc["Total Revenue"].iloc[0]
                if revenue and revenue > 0:
                    net_profit_margin = (float(net_income) / float(revenue)) * 100.0
            except Exception:
                pass
        if net_profit_margin is None:
            net_profit_margin = 10.0
```
4. Define the `evaluate_performance_growth` function and execute it.
5. Pop values in `metrics_dict`.

**Step 4: Run test to verify it passes**
Run: `$env:PYTHONPATH="."; pytest tests/test_analyzer.py -k test_extended_metrics`
Expected: PASS

**Step 5: Commit**
```bash
git add src/analyzer.py tests/test_analyzer.py
git commit -m "feat: add 1M-5Y returns, growth stats, and automated verdict engine"
```

---

### Task 2: Implement Reviewer Engine Logic

**Files:**
- Modify: [analyzer.py](file:///d:/Work/komar/src/analyzer.py)
- Test: [test_financials_and_phases.py](file:///d:/Work/komar/tests/test_financials_and_phases.py)

**Step 1: Write the failing test**
Create a test case inside `tests/test_financials_and_phases.py` verifying the baseline threshold logic.

```python
from src.analyzer import evaluate_performance_growth

def test_evaluate_performance_growth():
    assert evaluate_performance_growth(25.0, 25.0, 18.0, 20.0) == "Good"
    assert evaluate_performance_growth(12.0, 12.0, 9.0, 5.0) == "Average"
    assert evaluate_performance_growth(2.0, 2.0, 3.0, -10.0) == "Bad"
```

**Step 2: Run test to verify it fails**
Run: `$env:PYTHONPATH="."; pytest tests/test_financials_and_phases.py -k test_evaluate_performance_growth`
Expected: FAIL with `ImportError` or `NameError`.

**Step 3: Implement minimal code to make the test pass**
Add `evaluate_performance_growth` inside `src/analyzer.py`:
```python
def evaluate_performance_growth(sales_growth: float, revenue_growth: float, net_profit: float, return_1y: float) -> str:
    score = 0
    if sales_growth >= 20.0:
        score += 2
    elif sales_growth >= 10.0:
        score += 1
        
    if revenue_growth >= 20.0:
        score += 2
    elif revenue_growth >= 10.0:
        score += 1
        
    if net_profit >= 15.0:
        score += 2
    elif net_profit >= 8.0:
        score += 1
        
    if return_1y is not None:
        if return_1y >= 15.0:
            score += 2
        elif return_1y >= 0.0:
            score += 1
    else:
        score += 1
        
    if score >= 6:
        return "Good"
    elif score >= 3:
        return "Average"
    else:
        return "Bad"
```

**Step 4: Run test to verify it passes**
Run: `$env:PYTHONPATH="."; pytest tests/test_financials_and_phases.py -k test_evaluate_performance_growth`
Expected: PASS

**Step 5: Commit**
```bash
git add src/analyzer.py tests/test_financials_and_phases.py
git commit -m "feat: implement performance & growth reviewer logic with unit tests"
```

---

### Task 3: Build new Header Card (Stock Name, Price, 52W metrics)

**Files:**
- Modify: [app.py](file:///d:/Work/komar/app.py)
- Test: Run Streamlit locally to verify layout.

**Step 1: Write implementation**
Place a new widescreen summary card immediately above the columns overview block:
```python
    # Task 1: Stock summary details above Company Profile
    st.markdown(f"""
    <div class="komar-card" style="margin-bottom: 1.5rem; padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h3 style="color: #3b82f6; margin: 0; font-size: 1.45rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem;">
                    🏢 {st.session_state["last_search_name"].upper()} <span style="font-size: 0.95rem; color: #64748b; font-weight: 600;">({stats['ticker']})</span>
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
                    <span style="color: #10b981; font-size: 1.35rem; font-weight: 700;">{price_symbol}{stats.get('fifty_two_week_high', 0.0):.2f}</span>
                </div>
                <div style="width: 1px; height: 25px; background: rgba(255,255,255,0.08);"></div>
                <div>
                    <span style="color: #f43f5e; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; display: block; margin-bottom: 0.1rem;">52W Low</span>
                    <span style="color: #f43f5e; font-size: 1.35rem; font-weight: 700;">{price_symbol}{stats.get('fifty_two_week_low', 0.0):.2f}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

**Step 2: Commit**
```bash
git add app.py
git commit -m "ui: add widescreen stock metrics header card above Company Profile section"
```

---

### Task 4: Build Historical Performance & Growth Metrics Section

**Files:**
- Modify: [app.py](file:///d:/Work/komar/app.py)
- Test: Run Streamlit locally to verify layout.

**Step 1: Write implementation**
Place a new widescreen statistics details block immediately before the `🕵️‍♂️ Detective Research Analysis Report` header:
1. Format verdict with color-coding (Good -> Green `#10b981`, Average -> Yellow `#eab308`, Bad -> Red `#f43f5e`).
2. Build layout with returns columns and growth columns.
3. Clean strings using flat split-strip flattener to prevent markdown parser bugs.

```python
    verdict = stats.get("performance_verdict", "Average")
    if verdict == "Good":
        verdict_color = "#10b981"
    elif verdict == "Bad":
        verdict_color = "#f43f5e"
    else:
        verdict_color = "#eab308"

    perf_html = f"""
    <div class="komar-card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
            <h4 style="color: #3b82f6; margin: 0; font-size: 1.25rem;">📈 Historical Performance & Financial Growth Overview</h4>
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 0.4rem 1rem; border-radius: 6px; display: flex; align-items: center; gap: 0.75rem;">
                <span style="color: #64748b; font-size: 0.775rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Automated Verdict:</span>
                <span style="color: {verdict_color}; font-weight: 800; font-size: 0.95rem; text-transform: uppercase;">{verdict}</span>
            </div>
        </div>
        
        <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 300px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px;">
                <div style="color: #3b82f6; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem;">📅 Price Horizon Returns</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">1 Month Return:</span>
                    <span style="font-weight: 700; color: {'#10b981' if (stats.get('return_1m') or 0.0) >= 0 else '#f43f5e'}">{f"{stats.get('return_1m'):.1f}%" if stats.get('return_1m') is not None else 'N/A'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">3 Months Return:</span>
                    <span style="font-weight: 700; color: {'#10b981' if (stats.get('return_3m') or 0.0) >= 0 else '#f43f5e'}">{f"{stats.get('return_3m'):.1f}%" if stats.get('return_3m') is not None else 'N/A'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">6 Months Return:</span>
                    <span style="font-weight: 700; color: {'#10b981' if (stats.get('return_6m') or 0.0) >= 0 else '#f43f5e'}">{f"{stats.get('return_6m'):.1f}%" if stats.get('return_6m') is not None else 'N/A'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">1 Year Return:</span>
                    <span style="font-weight: 700; color: {'#10b981' if (stats.get('return_1y') or 0.0) >= 0 else '#f43f5e'}">{f"{stats.get('return_1y'):.1f}%" if stats.get('return_1y') is not None else 'N/A'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span style="color: #64748b;">5 Years Return:</span>
                    <span style="font-weight: 700; color: {'#10b981' if (stats.get('return_5y') or 0.0) >= 0 else '#f43f5e'}">{f"{stats.get('return_5y'):.1f}%" if stats.get('return_5y') is not None else 'N/A'}</span>
                </div>
            </div>
            
            <div style="flex: 1; min-width: 300px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px;">
                <div style="color: #10b981; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem;">📊 Financial Growth Rates</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">YoY Sales Growth:</span>
                    <span style="font-weight: 700; color: {'#10b981' if stats['sales_growth_yoy'] >= 20.0 else '#cbd5e1'}">{stats['sales_growth_yoy']:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.85rem;">
                    <span style="color: #64748b;">YoY Revenue Growth:</span>
                    <span style="font-weight: 700; color: {'#10b981' if stats.get('revenue_growth', 0.0) >= 20.0 else '#cbd5e1'}">{stats.get('revenue_growth', 0.0):.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                    <span style="color: #64748b;">Net Profit Margin:</span>
                    <span style="font-weight: 700; color: {'#10b981' if stats.get('net_profit_margin', 0.0) >= 15.0 else '#cbd5e1'}">{stats.get('net_profit_margin', 0.0):.1f}%</span>
                </div>
            </div>
        </div>
    </div>
    """
    perf_html_flat = "\n".join(line.strip() for line in perf_html.split("\n"))
    st.markdown(perf_html_flat, unsafe_allow_html=True)
```

**Step 2: Commit**
```bash
git add app.py
git commit -m "ui: add Historical Performance & Growth Metrics dashboard section with verdict panel"
```

---

## Verification Plan

### Automated Tests
- Run full pytest suite to verify new extended calculation metrics and reviewer engine coverage:
  `$env:PYTHONPATH="."; pytest`

### Manual Verification
- Launch Streamlit app locally: `streamlit run app.py`
- Resolve Nvidia or Adani Power to verify new cards display correct and fully formatted numbers.
