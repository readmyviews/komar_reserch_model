# Anthropic Claude Integration Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Integrate Anthropic Claude Sonnet 4.6 (with hybrid/extended reasoning thinking mode) alongside Google Gemini, allowing users to switch between providers via `.env` file configurations.

**Architecture:** We will implement a multi-provider LLM coordinator in `src/agent.py` that checks the `LLM_PROVIDER` environment variable and routes requests. When using Anthropic, we will force a structured output using Anthropic's tool calling mechanism, converting our existing `AnalysisResponse` Pydantic model into a JSON schema tool. If the model supports reasoning, we will dynamically inject the Anthropic SDK `thinking` parameters using the user-defined budget.

**Tech Stack:** Python, Streamlit, yfinance, google-genai, anthropic, pydantic, pytest.

---

### Task 1: Environment & Dependency Setup

**Files:**
- Modify: [requirements.txt](file:///d:/Work/komar/requirements.txt)

**Step 1: Write the requirement change**
Modify `requirements.txt` to add `anthropic>=0.18.0` on a new line.

**Step 2: Install dependencies**
Run: `pip install -r requirements.txt`
Expected: Installs `anthropic` and its transitive dependencies successfully.

**Step 3: Verify installation**
Run: `python -c "import anthropic; print(anthropic.__version__)"`
Expected: Prints version >= 0.18.0 without any errors.

**Step 4: Commit dependency update**
```bash
git add requirements.txt
git commit -m "chore: add anthropic dependency in requirements.txt"
```

---

### Task 2: Multi-Provider Core Routing & Anthropic Integration in `agent.py`

**Files:**
- Modify: [src/agent.py](file:///d:/Work/komar/src/agent.py)

**Step 1: Implement conditional provider logic in `src/agent.py`**
We will add `import anthropic` and implement the `_run_anthropic_analysis` helper function, then update the main `generate_komar_analysis` entrypoint.

Exact code changes in `src/agent.py`:
```python
# Import anthropic alongside existing google client imports
import anthropic
```

Helper function `_run_anthropic_analysis`:
```python
def _run_anthropic_analysis(name: str, country: str, stats: dict) -> dict:
    """
    Formulates the qualitative prompt and fires it to Anthropic Claude.
    Guarantees structured schema output by using forced tool calling.
    Handles extended thinking configurations for compatible models.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is missing!")
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Please add it to your .env file.")
        
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
    
    # 1. Standard Prompt & System instructions
    system_instruction = (
        "You are an expert stock market analyst applying seasoned trader Julian Komar's "
        "fundamental and thematic research methodology. You act like a 'detective' to figure "
        "out exactly what big institutional investors see in a company's fundamentals and thematic story.\n\n"
        "Analyze the user-provided stock by detailing: \n"
        "1. Fundamental Growth Layer: Evaluate YoY Sales/EPS growth figures against target thresholds (20%, 30%, 40%+). Categorize the stock as CANSLIM Stock, Sales Grower, or Story Stock.\n"
        "2. The Story Layer: Explain the business model, current success, and core future catalysts (AI, cloud, cyber, clean energy, biotech, etc.).\n"
        "3. Sister Stocks & Theme Alignment: List 3-4 competitor/sister stocks in the same country or globally also showing strong momentum. Confirm if the overall industry/theme is in high institutional demand.\n"
        "4. Institutional Quality Check (Liquidity): Compare average daily dollar volume to Komar's minimum thresholds ($20M-$100M USD mature, $5M-$10M USD young micro-cap). Assess if institutions can accumulate and exit safely.\n\n"
        "Provide a final verdict, a rating score from 1 to 10, and a rigorous rating breakdown scoring five key elements (2 points each) to explain exactly why this rating was given. "
        "Also factor in whether the stock is in a solid uptrend based on its 50-day and 200-day Simple Moving Averages. Keep descriptions analytical, insightful, and detailed. DO NOT use generic filler text."
    )
    
    formatted_vol = f"${stats['avg_daily_dollar_volume']:,.2f}"
    formatted_sales = f"{stats['sales_growth_yoy']:.2f}%"
    formatted_eps = f"{stats['eps_growth_yoy']:.2f}%"
    formatted_mcap = f"${stats['market_cap']:,.2f}"
    sma_status = (
        f"Trading ABOVE 50 SMA (${stats['sma_50']:.2f}) and ABOVE 200 SMA (${stats['sma_200']:.2f})" 
        if stats['is_above_50_sma'] and stats['is_above_200_sma'] 
        else f"SMA 50: ${stats['sma_50']:.2f} (Above: {stats['is_above_50_sma']}), SMA 200: ${stats['sma_200']:.2f} (Above: {stats['is_above_200_sma']})"
    )
    
    prompt = f"""
    Conduct a comprehensive detective-style fundamental & thematic analysis for:
    - Stock Name: {name}
    - Country: {country}
    - Resolved Ticker: {stats['ticker']}
    - Current Price: {stats['current_price']:.2f}
    - Market Cap (raw): {formatted_mcap}
    
    Calculated Quantitative Financial Metrics (Use these directly in your growth and liquidity evaluations):
    - YoY Sales Growth: {formatted_sales}
    - YoY EPS Growth: {formatted_eps}
    - Average Daily Dollar Volume (30-day window): {formatted_vol} USD equivalent
    - 30-Day Price Momentum / Return: {stats['price_return_30d']:.2f}%
    - Technical Trend (SMAs): {sma_status}
    
    Structure your analysis to follow Julian Komar's framework exactly. Return your findings as a structured analysis payload using the forced tool schema.
    """
    
    # 2. Define the tool configuration mapping our Pydantic schema
    tool_definition = {
        "name": "analyze_stock",
        "description": "Returns the structured qualitative research report matching the Julian Komar framework schema.",
        "input_schema": AnalysisResponse.model_json_schema()
    }
    
    # 3. Configure Thinking Budget
    thinking_budget_str = os.getenv("ANTHROPIC_THINKING_BUDGET", "1024")
    try:
        thinking_budget = int(thinking_budget_str)
    except ValueError:
        thinking_budget = 1024
        
    client = anthropic.Anthropic(api_key=api_key)
    
    # Enable extended thinking logic if budget > 0 and using supporting model
    thinking_enabled = False
    # Standard Claude 3.7 / 4.6 models support thinking
    if thinking_budget > 0 and ("claude-3-7" in model_name or "claude-3.7" in model_name or "claude-4" in model_name or "claude-v" in model_name or "thinking" in model_name):
        thinking_enabled = True
        
    kwargs = {
        "model": model_name,
        "system": system_instruction,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [tool_definition],
        "tool_choice": {"type": "tool", "name": "analyze_stock"}
    }
    
    if thinking_enabled:
        logger.info(f"Firing Anthropic Request with Thinking enabled (budget={thinking_budget} tokens) using model: '{model_name}'")
        kwargs["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        }
        kwargs["max_tokens"] = thinking_budget + 4000
    else:
        logger.info(f"Firing Anthropic Request with Thinking disabled using model: '{model_name}'")
        kwargs["max_tokens"] = 4000
        
    response = client.messages.create(**kwargs)
    
    # 4. Extract tool call arguments
    tool_use_block = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "analyze_stock":
            tool_use_block = block
            break
            
    if not tool_use_block:
        logger.error("Claude did not invoke the forced tool 'analyze_stock'")
        raise ValueError("Anthropic LLM did not return a structured analysis tool block.")
        
    logger.info("Successfully received structured response from Anthropic Claude")
    return tool_use_block.input
```

Modify `generate_komar_analysis` to handle routing:
```python
def generate_komar_analysis(name: str, country: str, stats: dict) -> dict:
    """
    Formulates a detailed research prompt applying the Julian Komar framework to the stock.
    Delegates to Gemini or Anthropic based on LLM_PROVIDER.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    
    if provider == "anthropic":
        return _run_anthropic_analysis(name, country, stats)
    else:
        # Existing Gemini flow
        ...
```

**Step 2: Run tests to verify existing Gemini code doesn't regress**
Run: `$env:PYTHONPATH="." ; pytest tests/test_agent.py`
Expected: Test passes successfully.

**Step 3: Commit agent code**
```bash
git add src/agent.py
git commit -m "feat: implement multi-provider routing and Anthropic Claude tool agent"
```

---

### Task 3: Create Automated Tests for Anthropic Provider

**Files:**
- Create: [tests/test_agent_providers.py](file:///d:/Work/komar/tests/test_agent_providers.py)

**Step 1: Write the provider tests**
We will implement tests mocking `anthropic.Anthropic` API behavior to ensure routing and thinking settings work correctly.

Create `tests/test_agent_providers.py`:
```python
import pytest
import os
from unittest.mock import patch, MagicMock
from src.agent import generate_komar_analysis

@patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "dummy_anthropic_key", "ANTHROPIC_MODEL": "claude-3-7-sonnet-20250219"})
@patch("src.agent.anthropic.Anthropic")
def test_anthropic_provider_routing(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    
    # Mocking Anthropic tool use response format
    mock_tool_use = MagicMock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.name = "analyze_stock"
    mock_tool_use.input = {
        "stock_category": "Sales Grower",
        "fundamental_layer_details": "Sales up 30%, EPS up 45%.",
        "story_layer_details": "Clean energy theme catalysts.",
        "sister_stocks_details": "Tata Power is a solid sister stock.",
        "liquidity_details": "Meets average daily volume thresholds.",
        "rating": 7,
        "rating_breakdown": "- Sales Growth: 2/2",
        "buying_range": "₹450 - ₹500",
        "buying_range_status": "IN BUY ZONE",
        "verdict": "Fits profile nicely"
    }
    
    mock_response = MagicMock()
    mock_response.content = [mock_tool_use]
    mock_client.messages.create.return_value = mock_response
    
    stats = {
        "ticker": "TATAPOWER.NS",
        "current_price": 480.0,
        "recent_volume": 1500000,
        "avg_daily_dollar_volume": 8000000.0,
        "sales_growth_yoy": 30.0,
        "eps_growth_yoy": 45.0,
        "market_cap": 1200000000.0,
        "sma_50": 460.0,
        "sma_200": 430.0,
        "is_above_50_sma": True,
        "is_above_200_sma": True,
        "price_return_30d": 8.0
    }
    
    res = generate_komar_analysis("Tata Power", "India", stats)
    assert res["stock_category"] == "Sales Grower"
    assert res["rating"] == 7
    assert res["buying_range"] == "₹450 - ₹500"
    
    # Verify that Anthropic client was called with thinking configuration
    mock_client.messages.create.assert_called_once()
    called_kwargs = mock_client.messages.create.call_args[1]
    assert called_kwargs["model"] == "claude-3-7-sonnet-20250219"
    assert "thinking" in called_kwargs
    assert called_kwargs["thinking"]["type"] == "enabled"
```

**Step 2: Run tests to verify they pass**
Run: `$env:PYTHONPATH="." ; pytest tests/test_agent_providers.py -v`
Expected: Tests pass.

**Step 3: Commit provider tests**
```bash
git add tests/test_agent_providers.py
git commit -m "test: add unit tests verifying Anthropic provider routing and mocking"
```

---

### Task 4: Polish Dashboard Sidebar UI in `app.py`

**Files:**
- Modify: [app.py](file:///d:/Work/komar/app.py)

**Step 1: Modify `app.py` sidebar key validation**
We will update `app.py` around lines 61-68 to dynamically check based on `LLM_PROVIDER`.

Change in `app.py`:
```python
# Verify API Keys based on LLM_PROVIDER
llm_provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

if llm_provider == "anthropic":
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        st.sidebar.error("⚠️ ANTHROPIC_API_KEY is missing! Add it to your .env file to enable qualitative reasoning.")
        api_configured = False
    else:
        st.sidebar.success("🔑 Anthropic API Key configured.")
        api_configured = True
else:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        st.sidebar.error("⚠️ GEMINI_API_KEY is missing! Add it to your .env file to enable qualitative reasoning.")
        api_configured = False
    else:
        st.sidebar.success("🔑 Gemini API Key configured.")
        api_configured = True
```

Update pipeline validation around line 83:
```python
# Trigger analysis or retrieve from state to optimize rendering (Streamlit session state)
if analyze_btn or "metrics" in st.session_state:
    if not api_configured:
        st.error(f"Please add a valid API key to your `.env` file first for {llm_provider.capitalize()}.")
```

**Step 2: Run all tests to make sure app imports and routing work correctly**
Run: `$env:PYTHONPATH="." ; pytest`
Expected: All 9+ tests pass perfectly.

**Step 3: Commit app UI updates**
```bash
git add app.py
git commit -m "feat: update sidebar API key verification to dynamically support active LLM provider"
```
