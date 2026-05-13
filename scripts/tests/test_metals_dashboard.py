import pytest
from unittest.mock import MagicMock
from metals_dashboard import render_macro, render_metal_panel, make_layout
from rich.panel import Panel

def test_make_layout():
    layout = make_layout()
    # Check if children exist by name
    assert layout["header"] is not None
    assert layout["macro"] is not None
    assert layout["body"] is not None
    assert layout["XAU"] is not None
    assert layout["XAG"] is not None

def test_render_macro_empty():
    panel = render_macro(None, {})
    assert isinstance(panel, Panel)
    # title can be a str or Text object. If it's str, just check it.
    title = str(panel.title)
    assert "Macro Environment" in title

def test_render_macro_with_data():
    macro_data = {
        "DXY": {"current": 104.2, "change": 0.5, "history": [103.5, 104.2]},
        "GOLD": {"current": 2350.5, "change": -0.2, "history": [2355, 2350.5]}
    }
    correlations = {"DXY": -0.85, "GOLD": 1.0}
    panel = render_macro(macro_data, correlations)
    assert isinstance(panel, Panel)

def test_render_metal_panel_loading():
    panel = render_metal_panel("XAU", None, MagicMock())
    assert isinstance(panel, Panel)
    # Check renderable content
    assert "Loading" in str(panel.renderable)

def test_render_metal_panel_with_data():
    engine = MagicMock()
    engine.analyze_trend.return_value = ("Strong Uptrend", 2, "EMA stuff")
    engine.calculate_rsi.return_value = 65.5
    engine.calculate_supertrend.return_value = (2300.0, 1)
    engine.calculate_vwap.return_value = 2320.0
    
    data = {
        "binance": [
            [[0, 0, 0, 0, 2350.0]] * 100, # Spot
            [[0, 0, 0, 0, 2355.0]]         # Fut
        ],
        "depth": {
            "skew": 0.15,
            "bids": [{"p": 2340.0, "v": 2000000}],
            "asks": [{"p": 2360.0, "v": 1500000}]
        }
    }
    
    panel = render_metal_panel("XAU", data, engine, detailed=True)
    assert isinstance(panel, Panel)
    assert "XAU" in str(panel.title)
    
    panel_summary = render_metal_panel("XAG", data, engine, detailed=False)
    assert isinstance(panel_summary, Panel)
    assert "XAG" in str(panel_summary.title)
