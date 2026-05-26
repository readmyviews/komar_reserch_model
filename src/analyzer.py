import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("komar.analyzer")

# Direct overrides mapping stock names/common names to ticker symbols
TICKER_OVERRIDES = {
    "adani power": "ADANIPOWER.NS",
    "adani": "ADANIPOWER.NS",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "netflix": "NFLX"
}

def resolve_ticker(name: str, country: str) -> str:
    """
    Resolves the provided stock name or ticker symbol to a standard Yahoo Finance ticker.
    Appends country-specific suffixes (.NS for NSE, India) if required.
    """
    start_time = time.time()
    name_clean = name.strip()
    if not name_clean:
        logger.warning("Empty stock name provided for resolution")
        return ""
    
    key = name_clean.lower()
    
    # 1. Check direct overrides list
    if key in TICKER_OVERRIDES:
        resolved = TICKER_OVERRIDES[key]
        logger.info(f"Resolved name '{name_clean}' via overrides to '{resolved}' in {time.time() - start_time:.4f}s")
        return resolved
        
    # 2. Apply country rules
    if country.lower() == "india":
        # Suffix NSE ticker if not already present
        if not (name_clean.upper().endswith(".NS") or name_clean.upper().endswith(".BO")):
            resolved = f"{name_clean.upper()}.NS"
        else:
            resolved = name_clean.upper()
    else:
        resolved = name_clean.upper()
        
    logger.info(f"Resolved name '{name_clean}' ({country}) to ticker '{resolved}' in {time.time() - start_time:.4f}s")
    return resolved

# Simple caching system to avoid hitting Yahoo Finance repeatedly during Streamlit re-runs
# We cache up to 128 tickers
@lru_cache(maxsize=128)
def calculate_metrics(ticker_symbol: str) -> dict:
    """
    Fetches real-time stock price, 30-day historical data, and financial statements
    from yfinance. Computes Average Daily Dollar Volume and YoY Sales and EPS Growth.
    """
    start_time = time.time()
    logger.info(f"Starting metric calculations for ticker '{ticker_symbol}'")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # --- 1. Fetch Price History & Liquidity Check ---
        logger.debug(f"Fetching 30d history for {ticker_symbol}")
        history = ticker.history(period="30d")
        if history.empty:
            logger.error(f"yfinance returned empty price history for {ticker_symbol}")
            raise ValueError(f"Could not fetch historical data for ticker '{ticker_symbol}'")
            
        history["dollar_volume"] = history["Close"] * history["Volume"]
        avg_daily_dollar_volume = float(history["dollar_volume"].mean())
        current_price = float(history["Close"].iloc[-1])
        recent_volume = int(history["Volume"].iloc[-1])
        
        logger.info(f"Successfully calculated liquidity metrics for {ticker_symbol}. Avg daily dollar volume: ${avg_daily_dollar_volume:,.2f} USD equiv.")

        # --- 2. Fetch Growth Metrics (YoY Sales / EPS) ---
        sales_growth_yoy = None
        eps_growth_yoy = None
        
        # yfinance statements can be slow, log the attempt
        logger.debug(f"Fetching quarterly financials for {ticker_symbol}")
        quarterly_financials = ticker.quarterly_financials
        
        # Try using quarterly financials first (more immediate YoY indicators)
        if quarterly_financials is not None and not quarterly_financials.empty:
            logger.info(f"Quarterly financials index for {ticker_symbol}: {list(quarterly_financials.index)}")
            try:
                # YoY Revenue growth comparing the latest quarter to same quarter last year (4 quarters ago)
                if "Total Revenue" in quarterly_financials.index:
                    rev_latest = quarterly_financials.loc["Total Revenue"].iloc[0]
                    rev_prior_year = quarterly_financials.loc["Total Revenue"].iloc[4]
                    if rev_prior_year and rev_prior_year > 0:
                        sales_growth_yoy = float(((rev_latest - rev_prior_year) / rev_prior_year) * 100)
                        logger.info(f"YoY Quarterly Sales Growth calculated: {sales_growth_yoy:.2f}%")
            except Exception as ex:
                logger.debug(f"Could not calculate quarterly Sales Growth via index 0 vs 4: {str(ex)}")

            try:
                eps_row = "Diluted EPS" if "Diluted EPS" in quarterly_financials.index else "Basic EPS"
                if eps_row in quarterly_financials.index:
                    eps_latest = quarterly_financials.loc[eps_row].iloc[0]
                    eps_prior_year = quarterly_financials.loc[eps_row].iloc[4]
                    if eps_prior_year is not None and eps_prior_year != 0:
                        eps_growth_yoy = float(((eps_latest - eps_prior_year) / abs(eps_prior_year)) * 100)
                        logger.info(f"YoY Quarterly EPS Growth calculated: {eps_growth_yoy:.2f}%")
            except Exception as ex:
                logger.debug(f"Could not calculate quarterly EPS Growth via index 0 vs 4: {str(ex)}")

        # Fallback to annual statements if quarterly failed or columns were insufficient
        if sales_growth_yoy is None or eps_growth_yoy is None:
            logger.debug(f"Quarterly fallback. Fetching annual financials for {ticker_symbol}")
            financials = ticker.financials
            if financials is not None and not financials.empty:
                try:
                    if "Total Revenue" in financials.index and sales_growth_yoy is None:
                        rev_latest = financials.loc["Total Revenue"].iloc[0]
                        rev_prior = financials.loc["Total Revenue"].iloc[1]
                        if rev_prior and rev_prior > 0:
                            sales_growth_yoy = float(((rev_latest - rev_prior) / rev_prior) * 100)
                            logger.info(f"YoY Annual Sales Growth calculated: {sales_growth_yoy:.2f}%")
                except Exception as ex:
                    logger.debug(f"Could not calculate annual Sales Growth: {str(ex)}")
                    
                try:
                    eps_row = "Diluted EPS" if "Diluted EPS" in financials.index else "Basic EPS"
                    if eps_row in financials.index and eps_growth_yoy is None:
                        eps_latest = financials.loc[eps_row].iloc[0]
                        eps_prior = financials.loc[eps_row].iloc[1]
                        if eps_prior is not None and eps_prior != 0:
                            eps_growth_yoy = float(((eps_latest - eps_prior) / abs(eps_prior)) * 100)
                            logger.info(f"YoY Annual EPS Growth calculated: {eps_growth_yoy:.2f}%")
                except Exception as ex:
                    logger.debug(f"Could not calculate annual EPS Growth: {str(ex)}")

        # Clean NaNs and make sure defaults are correct
        metrics_dict = {
            "ticker": ticker_symbol,
            "current_price": current_price,
            "recent_volume": recent_volume,
            "avg_daily_dollar_volume": avg_daily_dollar_volume,
            "sales_growth_yoy": float(sales_growth_yoy) if sales_growth_yoy is not None and not np.isnan(sales_growth_yoy) else 0.0,
            "eps_growth_yoy": float(eps_growth_yoy) if eps_growth_yoy is not None and not np.isnan(eps_growth_yoy) else 0.0
        }
        
        logger.info(f"Completed metric calculations for {ticker_symbol} in {time.time() - start_time:.4f}s")
        return metrics_dict
        
    except Exception as e:
        logger.error(f"Error calculating metrics for ticker {ticker_symbol}: {str(e)}", exc_info=True)
        raise
