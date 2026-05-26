import pytest
import plotly.graph_objects as go
import pandas as pd
from src.ui_components import get_price_chart, get_growth_chart, get_glassmorphic_css

def test_ui_generators():
    history_df = pd.DataFrame({
        "Close": [100, 101, 102],
        "Volume": [1000, 1500, 1200]
    }, index=pd.date_range("2026-01-01", periods=3))
    
    chart = get_price_chart(history_df, "TEST", "₹")
    assert isinstance(chart, go.Figure)
    
    growth_chart = get_growth_chart(35.0, 120.0)
    assert isinstance(growth_chart, go.Figure)
    
    css = get_glassmorphic_css()
    assert ".komar-card" in css
    assert "background" in css
