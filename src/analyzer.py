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
    "tata power": "TATAPOWER.NS",
    "tata": "TATAPOWER.NS",
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
        
    # Clean up spaces in symbols (e.g. 'TATA POWER.NS' -> 'TATAPOWER.NS')
    resolved = resolved.replace(" ", "")
    
    logger.info(f"Resolved name '{name_clean}' ({country}) to ticker '{resolved}' in {time.time() - start_time:.4f}s")
    return resolved

def calculate_eva_mva(ticker: yf.Ticker, market_cap: float, ticker_symbol: str) -> dict:
    """
    Computes EVA and MVA metrics from yfinance balance sheet and financials dynamically.
    Provides crash-proof defaults and safety bounds if data is sparse or missing.
    """
    logger.info(f"Calculating EVA and MVA for {ticker_symbol}")
    is_india = ticker_symbol.upper().endswith(".NS") or ticker_symbol.upper().endswith(".BO")
    
    # 1. Total Book Value of Equity
    book_value_equity = None
    balance_sheet = None
    try:
        balance_sheet = ticker.balance_sheet
    except Exception as ex:
        logger.debug(f"Failed to fetch balance sheet for {ticker_symbol}: {str(ex)}")
        
    if balance_sheet is not None and not balance_sheet.empty:
        idx_lower = [str(x).lower().strip() for x in balance_sheet.index]
        for term in ["stockholders equity", "total stockholder equity", "common stock equity", "shareholders equity", "total equity"]:
            if term in idx_lower:
                try:
                    match_idx = idx_lower.index(term)
                    val = balance_sheet.iloc[match_idx].iloc[0]
                    if val is not None and not pd.isna(val) and val != 0:
                        book_value_equity = float(val)
                        break
                except Exception:
                    pass
                    
    if book_value_equity is None or book_value_equity <= 0:
        book_value_equity = market_cap * 0.45 # standard 45% equity-to-market-cap ratio fallback
        logger.info(f"Using default book value of equity fallback: {book_value_equity:.2f}")
        
    # 2. Total Debt
    total_debt = 0.0
    try:
        total_debt = float(ticker.info.get("totalDebt", 0.0))
    except Exception:
        pass
        
    if total_debt == 0.0 and balance_sheet is not None and not balance_sheet.empty:
        idx_lower = [str(x).lower().strip() for x in balance_sheet.index]
        debt_val = 0.0
        for term in ["long term debt", "short term debt", "short long term debt", "current debt", "total debt"]:
            if term in idx_lower:
                try:
                    match_idx = idx_lower.index(term)
                    val = balance_sheet.iloc[match_idx].iloc[0]
                    if val is not None and not pd.isna(val):
                        debt_val += float(val)
                except Exception:
                    pass
        if debt_val > 0:
            total_debt = debt_val
            
    # 3. Cash and Cash Equivalents
    total_cash = 0.0
    try:
        total_cash = float(ticker.info.get("totalCash", 0.0))
    except Exception:
        pass
        
    if total_cash == 0.0 and balance_sheet is not None and not balance_sheet.empty:
        idx_lower = [str(x).lower().strip() for x in balance_sheet.index]
        for term in ["cash and cash equivalents", "cash", "cash equivalents"]:
            if term in idx_lower:
                try:
                    match_idx = idx_lower.index(term)
                    val = balance_sheet.iloc[match_idx].iloc[0]
                    if val is not None and not pd.isna(val):
                        total_cash = float(val)
                        break
                except Exception:
                    pass
                    
    # 4. Invested Capital
    invested_capital = total_debt + book_value_equity - total_cash
    if invested_capital <= 0:
        invested_capital = book_value_equity # Fallback to equity
        
    # 5. EBIT (Operating Income)
    ebit = None
    financials = None
    try:
        financials = ticker.financials
    except Exception as ex:
        logger.debug(f"Failed to fetch financials for {ticker_symbol}: {str(ex)}")
        
    if financials is not None and not financials.empty:
        idx_lower = [str(x).lower().strip() for x in financials.index]
        for term in ["ebit", "operating income", "operating income or loss"]:
            if term in idx_lower:
                try:
                    match_idx = idx_lower.index(term)
                    val = financials.iloc[match_idx].iloc[0]
                    if val is not None and not pd.isna(val):
                        ebit = float(val)
                        break
                except Exception:
                    pass
                    
    if ebit is None:
        # Fallback based on revenue if possible
        revenue = None
        if financials is not None and not financials.empty:
            idx_lower = [str(x).lower().strip() for x in financials.index]
            if "total revenue" in idx_lower:
                try:
                    match_idx = idx_lower.index("total revenue")
                    val = financials.iloc[match_idx].iloc[0]
                    if val is not None and not pd.isna(val):
                        revenue = float(val)
                except Exception:
                    pass
        if revenue and revenue > 0:
            ebit = revenue * 0.12 # assume 12% operating margin
        else:
            ebit = market_cap * 0.06 # assume 6% EBIT yield
            
    # 6. Effective Tax Rate
    tax_rate = 0.25 if not is_india else 0.30
    if financials is not None and not financials.empty:
        idx_lower = [str(x).lower().strip() for x in financials.index]
        tax_provision = 0.0
        pretax_income = 0.0
        
        try:
            if "tax provision" in idx_lower:
                match_idx = idx_lower.index("tax provision")
                val = financials.iloc[match_idx].iloc[0]
                if val is not None and not pd.isna(val):
                    tax_provision = float(val)
            if "pretax income" in idx_lower:
                match_idx = idx_lower.index("pretax income")
                val = financials.iloc[match_idx].iloc[0]
                if val is not None and not pd.isna(val):
                    pretax_income = float(val)
        except Exception:
            pass
            
        if pretax_income > 0 and tax_provision >= 0:
            calculated_rate = tax_provision / pretax_income
            if 0.0 <= calculated_rate <= 0.45:
                tax_rate = calculated_rate
                
    nopat = ebit * (1 - tax_rate)
    
    # 7. WACC
    rf = 0.045 if not is_india else 0.07 # 4.5% US, 7% India
    beta = 1.0
    try:
        info_beta = ticker.info.get("beta")
        if info_beta is not None and float(info_beta) > 0:
            beta = float(info_beta)
    except Exception:
        pass
        
    re = rf + beta * 0.055 # Risk-free + Beta * 5.5% Market Risk Premium
    
    # Cost of Debt
    rd = 0.06 if not is_india else 0.085 # 6% US, 8.5% India
    if financials is not None and not financials.empty and total_debt > 0:
        idx_lower = [str(x).lower().strip() for x in financials.index]
        if "interest expense" in idx_lower:
            try:
                match_idx = idx_lower.index("interest expense")
                interest_val = financials.iloc[match_idx].iloc[0]
                if interest_val is not None and not pd.isna(interest_val):
                    interest_val = abs(float(interest_val))
                    calculated_rd = interest_val / total_debt
                    if 0.01 <= calculated_rd <= 0.20:
                        rd = calculated_rd
            except Exception:
                pass
                
    total_value = market_cap + total_debt
    if total_value > 0:
        we = market_cap / total_value
        wd = total_debt / total_value
    else:
        we = 1.0
        wd = 0.0
        
    wacc = we * re + wd * rd * (1 - tax_rate)
    # Bound WACC logically
    wacc = max(0.05, min(0.18, wacc))
    
    # 8. EVA & MVA
    eva = nopat - (invested_capital * wacc)
    mva = market_cap - book_value_equity
    
    logger.info(f"Calculated EVA: {eva:,.2f}, MVA: {mva:,.2f} for {ticker_symbol}")
    return {
        "eva_native": float(eva),
        "mva_native": float(mva)
    }

def calculate_market_phase(history: pd.DataFrame, current_price: float, slope_threshold: float = 0.5, price_buffer: float = 5.0) -> str:
    """
    Classifies the stock into one of 4 market phases based on daily closing prices
    and the 200-period Simple Moving Average (SMA200).
    Parameterizes the thresholds so they are easily adjustable.
    """
    logger.info("Calculating market phase classification")
    
    if len(history) < 200:
        logger.warning("History is too short to calculate SMA200. Defaulting phase to Accumulation.")
        return "Accumulation"
        
    # Calculate SMA200
    close_prices = history["Close"]
    sma_200 = close_prices.rolling(window=200).mean()
    
    current_sma = float(sma_200.iloc[-1])
    if pd.isna(current_sma):
        # Rolling mean might have NaNs if history is short or contains NaNs
        # Try to calculate SMA manually from available data
        available_close = close_prices.dropna()
        if len(available_close) >= 200:
            current_sma = float(available_close.iloc[-200:].mean())
        else:
            current_sma = float(available_close.mean())
            
    # Get SMA200 20 days ago
    sma_20d_ago = current_sma
    if len(sma_200) >= 20:
        val = sma_200.iloc[-20]
        if not pd.isna(val):
            sma_20d_ago = float(val)
            
    # Calculate Slope (Rate of Change) of SMA200 over the last 20 days
    if sma_20d_ago > 0:
        slope = ((current_sma - sma_20d_ago) / sma_20d_ago) * 100
    else:
        slope = 0.0
        
    # Calculate price diff relative to SMA200 in %
    price_diff_pct = ((current_price - current_sma) / current_sma) * 100
    
    logger.info(f"Market Phase inputs - SMA200: {current_sma:.2f}, Slope: {slope:.3f}%, Price Diff: {price_diff_pct:.2f}%")
    
    # Check if slope is flat (between -slope_threshold and +slope_threshold)
    is_flat_slope = -slope_threshold <= slope <= slope_threshold
    
    # Check if price is within the buffer of SMA200
    is_within_buffer = -price_buffer <= price_diff_pct <= price_buffer
    
    if is_flat_slope and is_within_buffer:
        # We need to distinguish Accumulation (occurs after a downtrend)
        # from Distribution (occurs after an uptrend)
        # We check the prior trend of the SMA200 (e.g. from 80 days ago to 20 days ago)
        prior_sma = current_sma
        if len(sma_200) >= 80:
            val = sma_200.iloc[-80]
            if not pd.isna(val):
                prior_sma = float(val)
        elif len(sma_200) > 20:
            val = sma_200.iloc[0]
            if not pd.isna(val):
                prior_sma = float(val)
                
        if sma_20d_ago < prior_sma:
            return "Accumulation"
        else:
            return "Distribution"
            
    elif slope > slope_threshold and current_price > current_sma:
        return "Uptrend"
        
    elif slope < -slope_threshold and current_price < current_sma:
        return "Downtrend"
        
    else:
        # Graceful fallbacks if we are in transitional states
        if current_price > current_sma:
            return "Uptrend" if slope >= 0 else "Accumulation"
        else:
            return "Downtrend" if slope <= 0 else "Distribution"

# Simple caching system to avoid hitting Yahoo Finance repeatedly during Streamlit re-runs
# We cache up to 128 tickers
@lru_cache(maxsize=128)
def calculate_metrics(ticker_symbol: str) -> dict:
    """
    Fetches real-time stock price, 250-day historical data, and financial statements
    from yfinance. Computes Moving Averages (50/200 SMA), 30-day return,
    Market Cap, Average Daily Dollar Volume, and YoY Sales/EPS Growth.
    """
    start_time = time.time()
    logger.info(f"Starting metric calculations for ticker '{ticker_symbol}'")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # --- 1. Fetch Price History & Technical Indicators (last 250 trading days) ---
        logger.debug(f"Fetching 250d history for {ticker_symbol}")
        history_full = ticker.history(period="250d")
        if history_full.empty:
            logger.error(f"yfinance returned empty price history for {ticker_symbol}")
            raise ValueError(f"Could not fetch historical data for ticker '{ticker_symbol}'")
            
        current_price = float(history_full["Close"].iloc[-1])
        recent_volume = int(history_full["Volume"].iloc[-1])
        
        # Last 30 trading days for short-term liquidity calculations and chart
        history_30d = history_full.iloc[-30:].copy()
        history_30d["dollar_volume"] = history_30d["Close"] * history_30d["Volume"]
        avg_daily_volume_native = float(history_30d["dollar_volume"].mean())
        
        # Convert daily volume to USD for standard Komar checks
        avg_daily_dollar_volume = avg_daily_volume_native
        if ticker_symbol.upper().endswith(".NS") or ticker_symbol.upper().endswith(".BO"):
            avg_daily_dollar_volume = avg_daily_volume_native / 83.0
        
        # Compute Simple Moving Averages (SMA)
        sma_50 = None
        sma_200 = None
        is_above_50_sma = False
        is_above_200_sma = False
        
        if len(history_full) >= 50:
            sma_50 = float(history_full["Close"].iloc[-50:].mean())
            is_above_50_sma = current_price > sma_50
            
        if len(history_full) >= 200:
            sma_200 = float(history_full["Close"].iloc[-200:].mean())
            is_above_200_sma = current_price > sma_200
            
        # Compute 30-day Price Performance / Return (exactly 30 calendar days lookback aligned to nearest trading day)
        price_return_30d = 0.0
        if not history_full.empty:
            latest_date = history_full.index[-1]
            first_date = history_full.index[0]
            if (latest_date - first_date).days >= 30:
                target_date = latest_date - pd.Timedelta(days=30)
                closest_idx = history_full.index.get_indexer([target_date], method="nearest")[0]
                if closest_idx != -1:
                    price_30d_ago = float(history_full["Close"].iloc[closest_idx])
                    if price_30d_ago > 0:
                        price_return_30d = float(((current_price - price_30d_ago) / price_30d_ago) * 100)
        
        logger.info(f"Successfully calculated liquidity and technical indicators for {ticker_symbol}.")

        # --- 2. Fetch Market Cap from Ticker Info ---
        market_cap_native = 0.0
        try:
            logger.debug(f"Fetching market cap from info dictionary for {ticker_symbol}")
            market_cap_native = float(ticker.info.get("marketCap", 0.0))
        except Exception as ex:
            logger.debug(f"Failed to fetch market cap from info dict: {str(ex)}")

        market_cap_usd = market_cap_native
        if ticker_symbol.upper().endswith(".NS") or ticker_symbol.upper().endswith(".BO"):
            market_cap_usd = market_cap_native / 83.0

        # --- 3. Fetch Growth Metrics (YoY Sales / EPS) ---
        sales_growth_yoy = None
        eps_growth_yoy = None
        
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

        # Calculate EVA and MVA metrics dynamically
        try:
            eva_mva_results = calculate_eva_mva(ticker, market_cap_native, ticker_symbol)
        except Exception as ex:
            logger.error(f"Failed to calculate EVA/MVA for {ticker_symbol}: {str(ex)}")
            eva_mva_results = {"eva_native": 0.0, "mva_native": 0.0}

        # Calculate 4 Market Phases dynamically
        try:
            market_phase = calculate_market_phase(history_full, current_price)
        except Exception as ex:
            logger.error(f"Failed to calculate market phase for {ticker_symbol}: {str(ex)}")
            market_phase = "Accumulation"

        # Clean NaNs and make sure defaults are correct
        metrics_dict = {
            "ticker": ticker_symbol,
            "current_price": current_price,
            "recent_volume": recent_volume,
            "avg_daily_dollar_volume": avg_daily_dollar_volume,
            "avg_daily_volume_native": avg_daily_volume_native,
            "sales_growth_yoy": float(sales_growth_yoy) if sales_growth_yoy is not None and not np.isnan(sales_growth_yoy) else 0.0,
            "eps_growth_yoy": float(eps_growth_yoy) if eps_growth_yoy is not None and not np.isnan(eps_growth_yoy) else 0.0,
            "market_cap": market_cap_native,
            "market_cap_usd": market_cap_usd,
            "sma_50": sma_50 if sma_50 is not None else current_price,
            "sma_200": sma_200 if sma_200 is not None else current_price,
            "is_above_50_sma": is_above_50_sma,
            "is_above_200_sma": is_above_200_sma,
            "price_return_30d": price_return_30d,
            "eva_native": eva_mva_results["eva_native"],
            "mva_native": eva_mva_results["mva_native"],
            "market_phase": market_phase
        }
        
        logger.info(f"Completed metric calculations for {ticker_symbol} in {time.time() - start_time:.4f}s")
        return metrics_dict
    except Exception as e:
        logger.error(f"Error calculating metrics for ticker {ticker_symbol}: {str(e)}", exc_info=True)
        raise

# Force-clear cache on module load to prevent persistent stale cache issues in Streamlit processes
try:
    calculate_metrics.cache_clear()
    logger.info("Successfully flushed calculate_metrics lru_cache")
except Exception as ex:
    logger.debug(f"Failed to clear cache: {str(ex)}")
