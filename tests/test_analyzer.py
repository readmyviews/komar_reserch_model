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
    assert "market_cap" in metrics
    assert "sma_50" in metrics
    assert "sma_200" in metrics
    assert "price_return_30d" in metrics
    assert "eva_native" in metrics
    assert "mva_native" in metrics
    assert "market_phase" in metrics
    assert metrics["market_phase"] in ["Accumulation", "Uptrend", "Distribution", "Downtrend"]

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

