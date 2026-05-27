import pytest
import os
from unittest.mock import patch, MagicMock
from src.agent import generate_komar_analysis

@patch("src.agent._get_secret")
@patch("src.agent.genai.Client")
def test_generate_komar_analysis(mock_client_class, mock_get_secret):
    # Mock secrets to be independent of local secrets.toml on disk
    mock_get_secret.side_effect = lambda key, default=None: "dummy_key" if key == "GEMINI_API_KEY" else (default or "gemini-2.5-flash")

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    # Mocking standard structured response JSON
    mock_response.text = (
        '{"stock_category": "CANSLIM Stock", '
        '"company_brief": "Adani Power is a prominent Indian power utility company.", '
        '"key_strengths": ["Strong operational capacity", "Favorable regulatory push"], '
        '"key_weaknesses": ["Coal dependency", "High leverage"], '
        '"fundamental_layer_details": "EPS Growth is 120%, exceeding 40% threshold.", '
        '"story_layer_details": "Adani Power is a leading Indian power generator.", '
        '"sister_stocks_details": "Competitors like Tata Power are also showing strong momentum.", '
        '"liquidity_details": "Trading volume is robust, allowing institutions safe entries/exits.", '
        '"rating": 8, '
        '"rating_breakdown": "- Sales Growth: 2/2\\n- EPS Growth: 2/2\\n- Catalyst: 2/2\\n- Sister Stocks: 1/2\\n- Liquidity: 1/2", '
        '"buying_range": "₹480 - ₹510", '
        '"buying_range_status": "IN BUY ZONE", '
        '"verdict": "Adani Power is an excellent Pratik Patel candidate due to massive growth."}'
    )
    mock_client.models.generate_content.return_value = mock_response
    
    stats = {
        "ticker": "ADANIPOWER.NS",
        "current_price": 500.0,
        "recent_volume": 2000000,
        "avg_daily_dollar_volume": 12000000.0,
        "sales_growth_yoy": 35.5,
        "eps_growth_yoy": 120.0,
        "market_cap": 2500000000.0,
        "sma_50": 480.0,
        "sma_200": 450.0,
        "is_above_50_sma": True,
        "is_above_200_sma": True,
        "price_return_30d": 12.5
    }
    
    res = generate_komar_analysis("Adani Power", "India", stats)
    assert res["stock_category"] == "CANSLIM Stock"
    assert res["rating"] == 8
    assert "Sales Growth" in res["rating_breakdown"]
    assert res["buying_range"] == "₹480 - ₹510"
    assert res["buying_range_status"] == "IN BUY ZONE"
    assert " Tata Power " in res["sister_stocks_details"]

@patch("src.agent._get_secret")
@patch("src.agent.genai.Client")
def test_generate_komar_analysis_fallback_on_rate_limit(mock_client_class, mock_get_secret):
    # Mock secrets to be independent of local secrets.toml on disk
    mock_get_secret.side_effect = lambda key, default=None: "dummy_key" if key == "GEMINI_API_KEY" else ("gemini-3.1-pro-preview" if key == "GEMINI_MODEL" else default)

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Define a side_effect function for generate_content
    # The first call (with gemini-3.1-pro-preview) will raise a rate-limit exception
    # The second call (with gemini-2.5-flash fallback) will succeed
    call_count = 0
    
    mock_response = MagicMock()
    mock_response.text = (
        '{"stock_category": "Story Stock", '
        '"company_brief": "Nvidia is the world leader in AI chips.", '
        '"key_strengths": ["AI market dominance", "Robust developer ecosystem"], '
        '"key_weaknesses": ["High valuation", "Supply chain dependency"], '
        '"fundamental_layer_details": "EPS Growth is 80%.", '
        '"story_layer_details": "Nvidia is the AI chips leader.", '
        '"sister_stocks_details": "AMD is also showing strong momentum.", '
        '"liquidity_details": "High daily dollar volume.", '
        '"rating": 9, '
        '"rating_breakdown": "- Sales Growth: 2/2", '
        '"buying_range": "$900 - $950", '
        '"buying_range_status": "AWAITING PULLBACK", '
        '"verdict": "Fits profile perfectly"}'
    )
    
    def mock_generate_content(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Raise resource exhausted / rate limit error
            raise Exception("429 Resource Exhausted: Quota exceeded for gemini-3.1-pro-preview")
        return mock_response
        
    mock_client.models.generate_content.side_effect = mock_generate_content
    
    stats = {
        "ticker": "NVDA",
        "current_price": 920.0,
        "recent_volume": 40000000,
        "avg_daily_dollar_volume": 36000000000.0,
        "sales_growth_yoy": 250.0,
        "eps_growth_yoy": 400.0,
        "market_cap": 2200000000000.0,
        "sma_50": 850.0,
        "sma_200": 700.0,
        "is_above_50_sma": True,
        "is_above_200_sma": True,
        "price_return_30d": 15.0
    }
    
    res = generate_komar_analysis("Nvidia", "US", stats)
    assert res["stock_category"] == "Story Stock"
    assert res["rating"] == 9
    assert res["buying_range"] == "$900 - $950"
    
    # Confirm generate_content was called twice (first failed, second succeeded)
    assert call_count == 2
    
    # Check that the second call was called with fallback model gemini-2.5-flash
    calls = mock_client.models.generate_content.call_args_list
    assert len(calls) == 2
    assert calls[0][1]["model"] == "gemini-3.1-pro-preview"
    assert calls[1][1]["model"] == "gemini-2.5-flash"
