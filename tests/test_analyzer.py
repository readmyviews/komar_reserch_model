import pytest
from src.analyzer import resolve_ticker, calculate_metrics

def test_resolve_ticker_india():
    assert resolve_ticker("Adani Power", "India") == "ADANIPOWER.NS"

def test_resolve_ticker_india_with_spaces():
    assert resolve_ticker("Tata Power", "India") == "TATAPOWER.NS"
    assert resolve_ticker("TATA POWER.NS", "India") == "TATAPOWER.NS"

def test_resolve_ticker_us():
    assert resolve_ticker("Nvidia", "US") == "NVDA"

def test_calculate_metrics():
    # Test metric calculations for a known ticker like 'NVDA'
    metrics = calculate_metrics("NVDA")
    assert "ticker" in metrics
    assert metrics["ticker"] == "NVDA"
    assert "sales_growth_yoy" in metrics
    assert "eps_growth_yoy" in metrics
    assert "avg_daily_dollar_volume" in metrics
    assert metrics["avg_daily_dollar_volume"] > 0
    assert metrics["current_price"] > 0
