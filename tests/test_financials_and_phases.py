import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from src.analyzer import calculate_eva_mva, calculate_market_phase

def test_calculate_eva_mva_basic():
    # Setup mock ticker
    mock_ticker = MagicMock()
    
    # Mock balance sheet
    mock_balance_sheet = pd.DataFrame(
        [[100000000.0], [50000000.0], [10000000.0]], 
        index=["Stockholders Equity", "Total Debt", "Cash And Cash Equivalents"],
        columns=["2026-01-01"]
    )
    mock_ticker.balance_sheet = mock_balance_sheet
    
    # Mock financials (Income Statement)
    mock_financials = pd.DataFrame(
        [[15000000.0], [2000000.0], [8000000.0]], 
        index=["EBIT", "Tax Provision", "Pretax Income"],
        columns=["2026-01-01"]
    )
    mock_ticker.financials = mock_financials
    
    # Mock ticker info
    mock_ticker.info = {
        "beta": 1.2,
        "totalDebt": 50000000.0,
        "totalCash": 10000000.0
    }
    
    market_cap = 200000000.0
    ticker_symbol = "TEST"
    
    results = calculate_eva_mva(mock_ticker, market_cap, ticker_symbol)
    
    assert "eva_native" in results
    assert "mva_native" in results
    
    # Check MVA math: Market Cap - Shareholder Equity = 200M - 100M = 100M
    assert results["mva_native"] == 100000000.0
    
    # Check that EVA computed a valid float
    assert isinstance(results["eva_native"], float)

def test_calculate_market_phase_accumulation():
    # Setup history with flat SMA200 and price within 5% of SMA200
    # Length of 250
    dates = pd.date_range(end="2026-05-27", periods=250)
    # Flat price series around 100
    prices = [100.0] * 250
    history = pd.DataFrame({"Close": prices}, index=dates)
    
    current_price = 101.0 # +1% within buffer
    
    phase = calculate_market_phase(history, current_price, slope_threshold=0.5, price_buffer=5.0)
    # Standard fallback or matching prior trend is checked
    assert phase in ["Accumulation", "Distribution"]

def test_calculate_market_phase_uptrend():
    # Rising price series leading to high SMA200 slope
    dates = pd.date_range(end="2026-05-27", periods=250)
    # Price rises strongly from 50 to 150
    prices = list(np.linspace(50.0, 150.0, 250))
    history = pd.DataFrame({"Close": prices}, index=dates)
    
    # Current price is strictly greater than SMA200 (which would be around 100)
    current_price = 160.0
    
    phase = calculate_market_phase(history, current_price, slope_threshold=0.1, price_buffer=2.0)
    assert phase == "Uptrend"

def test_calculate_market_phase_downtrend():
    # Falling price series
    dates = pd.date_range(end="2026-05-27", periods=250)
    prices = list(np.linspace(150.0, 50.0, 250))
    history = pd.DataFrame({"Close": prices}, index=dates)
    
    current_price = 40.0
    
    phase = calculate_market_phase(history, current_price, slope_threshold=0.1, price_buffer=2.0)
    assert phase == "Downtrend"

def test_evaluate_performance_growth():
    from src.analyzer import evaluate_performance_growth
    # Good score scenario (needs score >= 6)
    # sales_growth=25 (+2), revenue_growth=25 (+2), net_profit=18 (+2), return_1y=20 (+2) = 8
    assert evaluate_performance_growth(25.0, 25.0, 18.0, 20.0) == "Good"
    
    # Average score scenario (score >= 3)
    # sales_growth=12 (+1), revenue_growth=12 (+1), net_profit=9 (+1), return_1y=5 (+1) = 4
    assert evaluate_performance_growth(12.0, 12.0, 9.0, 5.0) == "Average"
    
    # Bad score scenario (score < 3)
    # sales_growth=2 (0), revenue_growth=2 (0), net_profit=3 (0), return_1y=-10 (0) = 0
    assert evaluate_performance_growth(2.0, 2.0, 3.0, -10.0) == "Bad"

