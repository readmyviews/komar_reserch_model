# Rate Limit Resilience Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** Shield Streamlit from Gemini 429 Quota errors using exponential backoff retry loops with randomized jitter, combined with a multi-model fallback chain.

**Architecture:** Add a dynamically resolved fallback chain of models in `src/agent.py`. For each model, try to execute the generation call up to 5 times, applying exponential backoff with randomized jitter on rate limit errors. If a model exhausts its retries, catch the error and try the next model in the chain. Update `tests/test_agent.py` with comprehensive unit tests checking this behavior without delaying the test run.

**Tech Stack:** Python, Google GenAI SDK, pytest

---

### Task 1: Update Retry & Fallback Logic in `src/agent.py`

**Files:**
- Modify: `src/agent.py`

**Step 1: Write minimal implementation in `src/agent.py`**
Replace the rate limit retry and fallback logic in `generate_komar_analysis` to implement exponential backoff retry and a multi-tiered fallback chain.

```python
    import random
    
    primary_model = _get_secret("GEMINI_MODEL", "gemini-2.5-flash").strip()
    
    # Construct the fallback chain dynamically based on the primary model
    fallback_chain = [primary_model]
    if "gemini-2.5-flash" not in fallback_chain:
        fallback_chain.append("gemini-2.5-flash")
    if "gemini-2.0-flash" not in fallback_chain:
        fallback_chain.append("gemini-2.0-flash")
    
    max_retries = 5
    base_delay = 2.0
    
    last_exception = None
    
    for model_name in fallback_chain:
        logger.info(f"Attempting analysis using model '{model_name}' in the fallback chain")
        for attempt in range(max_retries):
            try:
                return _execute_gemini_call(client, model_name, system_instruction, prompt)
            except Exception as e:
                err_msg = str(e).lower()
                is_rate_limit = any(x in err_msg for x in ["429", "resource_exhausted", "rate limit", "quota", "exhausted"])
                
                if is_rate_limit:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter: base_delay^attempt + jitter
                        delay = (base_delay ** attempt) + random.uniform(0.1, 1.0)
                        logger.warning(
                            f"Gemini API rate limit or quota exceeded on attempt {attempt+1}/{max_retries} "
                            f"for model '{model_name}'. Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.warning(
                            f"Model '{model_name}' exhausted all {max_retries} retries due to rate limits."
                        )
                        break  # Break inner loop, move to next model in fallback_chain
                else:
                    logger.error(f"Gemini API call failed with non-rate-limit exception: {str(e)}", exc_info=True)
                    raise e
                    
    # If we exit the fallback chain without returning, raise the last exception
    logger.error("All models in the fallback chain exhausted their retries due to rate limits.", exc_info=True)
    if last_exception:
        raise last_exception
    raise Exception("API Rate Limit Exceeded: All fallback models exhausted.")
```

**Step 2: Commit**

```bash
git add src/agent.py
git commit -m "feat: implement resilient multi-tiered fallback and exponential backoff retry loop"
```

---

### Task 2: Align and Enhance Unit Tests in `tests/test_agent.py`

**Files:**
- Modify: `tests/test_agent.py`

**Step 1: Write/Update the unit tests in `tests/test_agent.py`**
Update `test_generate_komar_analysis_fallback_on_rate_limit` and write any new tests to verify:
- Retries happen exactly 5 times on the primary model before falling back.
- If the primary model fails all 5 times, it falls back to the next model in the chain.
- If the entire chain fails, it raises the rate limit exception.
- Patch `time.sleep` and `random.uniform` to ensure tests run instantly.

```python
@patch("src.agent.random.uniform")
@patch("src.agent.time.sleep")
@patch("src.agent._get_secret")
@patch("src.agent.genai.Client")
def test_generate_komar_analysis_fallback_on_rate_limit(mock_client_class, mock_get_secret, mock_sleep, mock_uniform):
    mock_uniform.return_value = 0.5
    # Mock secrets to return a custom primary model
    mock_get_secret.side_effect = lambda key, default=None: "dummy_key" if key == "GEMINI_API_KEY" else ("gemini-3.1-pro-preview" if key == "GEMINI_MODEL" else default)

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    call_count = 0
    mock_response = MagicMock()
    mock_response.text = '{"stock_category": "Story Stock", "company_brief": "Nvidia profile", "key_strengths": ["AI"], "key_weaknesses": ["Valuation"], "fundamental_layer_details": "EPS Growth is 80%.", "story_layer_details": "Nvidia is the AI leader.", "sister_stocks_details": "AMD is also showing momentum.", "liquidity_details": "High daily dollar volume.", "rating": 9, "rating_breakdown": "- Sales Growth: 2/2", "buying_range": "$900 - $950", "buying_range_status": "AWAITING PULLBACK", "verdict": "Fits profile perfectly"}'
    
    def mock_generate_content(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        model = kwargs.get("model", "")
        # First 5 calls are for gemini-3.1-pro-preview, raise 429
        # Sixth call is for gemini-2.5-flash fallback, succeed
        if model == "gemini-3.1-pro-preview":
            raise Exception("429 Resource Exhausted: Quota exceeded for gemini-3.1-pro-preview")
        return mock_response
        
    mock_client.models.generate_content.side_effect = mock_generate_content
    
    stats = {
        "ticker": "NVDA", "current_price": 920.0, "recent_volume": 40000000,
        "avg_daily_dollar_volume": 36000000000.0, "sales_growth_yoy": 250.0, "eps_growth_yoy": 400.0,
        "market_cap": 2200000000000.0, "sma_50": 850.0, "sma_200": 700.0,
        "is_above_50_sma": True, "is_above_200_sma": True, "price_return_30d": 15.0
    }
    
    res = generate_komar_analysis("Nvidia", "US", stats)
    assert res["stock_category"] == "Story Stock"
    assert res["rating"] == 9
    
    # 5 attempts on gemini-3.1-pro-preview, 1 on gemini-2.5-flash
    assert call_count == 6
    calls = mock_client.models.generate_content.call_args_list
    assert len(calls) == 6
    for i in range(5):
        assert calls[i][1]["model"] == "gemini-3.1-pro-preview"
    assert calls[5][1]["model"] == "gemini-2.5-flash"
    
    # Verify sleep was called 4 times for the 5 attempts (on the 5th attempt it breaks, no sleep)
    assert mock_sleep.call_count == 4
```

**Step 2: Run test to verify it passes**

Run: `$env:PYTHONPATH="."; pytest tests/test_agent.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_agent.py
git commit -m "test: update unit tests to verify exponential backoff and new fallback chain"
```

---

### Task 3: Full Workspace Verification

**Step 1: Run entire test suite**

Run: `$env:PYTHONPATH="."; pytest`
Expected: 15 passed, 0 failed

**Step 2: Verify local application works**
Run the Streamlit application to ensure no runtime errors, and verify the console logs reflect retry/fallback behavior if quota issues are simulated or hit.
