import pytest
import os
from unittest.mock import patch, MagicMock
from src.agent import generate_komar_analysis

@patch.dict(os.environ, {
    "LLM_PROVIDER": "anthropic",
    "ANTHROPIC_API_KEY": "dummy_anthropic_key",
    "ANTHROPIC_MODEL": "claude-3-7-sonnet-20250219",
    "ANTHROPIC_THINKING_BUDGET": "2048"
})
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
    assert called_kwargs["thinking"]["budget_tokens"] == 2048
    assert called_kwargs["max_tokens"] == 6048  # budget + 4000
