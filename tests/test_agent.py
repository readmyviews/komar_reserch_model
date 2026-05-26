import pytest
import os
from unittest.mock import patch, MagicMock
from src.agent import generate_komar_analysis

@patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"})
@patch("src.agent.genai.Client")
def test_generate_komar_analysis(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    # Mocking standard structured response JSON
    mock_response.text = (
        '{"stock_category": "CANSLIM Stock", '
        '"fundamental_layer_details": "EPS Growth is 120%, exceeding 40% threshold.", '
        '"story_layer_details": "Adani Power is a leading Indian power generator.", '
        '"sister_stocks_details": "Competitors like Tata Power are also showing strong momentum.", '
        '"liquidity_details": "Trading volume is robust, allowing institutions safe entries/exits.", '
        '"rating": 4, '
        '"verdict": "Adani Power is an excellent Julian Komar candidate due to massive growth."}'
    )
    mock_client.models.generate_content.return_value = mock_response
    
    stats = {
        "ticker": "ADANIPOWER.NS",
        "current_price": 500.0,
        "recent_volume": 2000000,
        "avg_daily_dollar_volume": 12000000.0,
        "sales_growth_yoy": 35.5,
        "eps_growth_yoy": 120.0
    }
    
    res = generate_komar_analysis("Adani Power", "India", stats)
    assert res["stock_category"] == "CANSLIM Stock"
    assert res["rating"] == 4
    assert " Tata Power " in res["sister_stocks_details"]
