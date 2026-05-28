import os
import json
import logging
import time
import random
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger("komar.agent")

class AnalysisResponse(BaseModel):
    stock_category: str = Field(description="Explicitly categorize as CANSLIM Stock, Sales Grower, or Story Stock")
    company_brief: str = Field(description="A concise 2-sentence summary of the company and its core products/services.")
    key_strengths: list[str] = Field(description="A list containing 2-3 key strengths.")
    key_weaknesses: list[str] = Field(description="A list containing 2-3 key weaknesses.")
    fundamental_layer_details: str = Field(description="Analysis of Sales & EPS growth YoY against target thresholds (20%, 30%, 40%+)")
    story_layer_details: str = Field(description="Detective breakdown of the business model, products, and key future catalysts (AI, clean energy, SaaS, robotics, etc.)")
    sister_stocks_details: str = Field(description="Direct competitors or sister stocks in same sector globally/locally showing strong growth/momentum, and sector trend validation")
    liquidity_details: str = Field(description="Liquidity assessment comparing average daily dollar volume to Pratik Patel's minimum thresholds ($20M-$100M USD mature, $5M-$10M USD young micro-cap)")
    rating: int = Field(description="Pratik Patel rating score from 1 (poor fit) to 10 (perfect fit)")
    rating_breakdown: str = Field(description="Explain exactly why the rating out of 10 was given. Score each of these five dimensions (out of 2 points each): 1) YoY Sales Growth, 2) YoY EPS/Income Growth, 3) Catalyst & Secular Theme Power, 4) Sister Stock Support & Sector Momentum, 5) Liquidity & Institutional Size. Format as a clear, beautifully structured list showing points like '- YoY Sales Growth: 2/2' and summing up to the total score.")
    buying_range: str = Field(description="A suggested optimal buying price range in native currency (e.g. ₹480 - ₹510 or $185 - $195) based on technical setup, key SMAs, and support/resistance zones. Provide the native currency symbol (₹ or $) inside the range string.")
    buying_range_status: str = Field(description="Buying status of the current stock price relative to the buying range (e.g. 'IN BUY ZONE', 'AWAITING PULLBACK', or 'BREAKOUT BUY')")
    verdict: str = Field(description="Brief final verdict on whether the stock fits the Pratik Patel institutional accumulation profile")

def _get_secret(key: str, default: str = None) -> str:
    """
    Safely retrieves a secret from Streamlit's st.secrets if running in a Streamlit context,
    otherwise falls back to environment variables.
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

def _execute_gemini_call(client: genai.Client, model_name: str, system_instruction: str, prompt: str) -> dict:
    """
    Private helper to fire the content generation request to a specific Gemini model
    and return the parsed JSON dictionary.
    """
    start_time = time.time()
    logger.info(f"Firing request to Gemini model '{model_name}'")
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=AnalysisResponse,
            temperature=0.2
        )
    )
    
    elapsed = time.time() - start_time
    logger.info(f"Gemini analysis with model '{model_name}' completed successfully in {elapsed:.2f}s")
    
    result_dict = json.loads(response.text)
    logger.debug(f"Parsed response JSON successfully: {list(result_dict.keys())}")
    return result_dict

def generate_komar_analysis(name: str, country: str, stats: dict) -> dict:
    """
    Formulates a detailed research prompt applying the Julian Komar framework.
    Invokes Gemini with a structured JSON schema. Automatically handles
    rate limits (429 / resource exhausted) by falling back to gemini-2.5-flash.
    Retrieves the API key and model config using Streamlit secrets and fallback environment variables.
    """
    api_key = _get_secret("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable/secret is missing!")
        raise ValueError("GEMINI_API_KEY secret is not set. Please add it to your secrets.toml or .env file.")
        
    client = genai.Client(api_key=api_key)
    
    system_instruction = (
        "You are an expert stock market analyst applying seasoned trader Pratik Patel's "
        "fundamental and thematic research methodology. You act like a 'detective' to figure "
        "out exactly what big institutional investors see in a company's fundamentals and thematic story.\n\n"
        "Analyze the user-provided stock by detailing: \n"
        "0. Company Overview Profile: Provide a concise 2-sentence summary of the company and its operations (company_brief), and list 2-3 key strategic/financial strengths (key_strengths) and 2-3 key weaknesses (key_weaknesses).\n"
        "1. Fundamental Growth Layer: Evaluate YoY Sales/EPS growth figures against target thresholds (20%, 30%, 40%+). Categorize the stock as CANSLIM Stock, Sales Grower, or Story Stock.\n"
        "2. The Story Layer: Explain the business model, current success, and core future catalysts (AI, cloud, cyber, clean energy, biotech, etc.).\n"
        "3. Sister Stocks & Theme Alignment: List 3-4 competitor/sister stocks in the same country or globally also showing strong momentum. Confirm if the overall industry/theme is in high institutional demand.\n"
        "4. Institutional Quality Check (Liquidity): Compare average daily dollar volume to Patel's minimum thresholds ($20M-$100M USD mature, $5M-$10M USD young micro-cap). Assess if institutions can accumulate and exit safely.\n\n"
        "Provide a final verdict, a rating score from 1 to 10, and a rigorous rating breakdown scoring five key elements (2 points each) to explain exactly why this rating was given. "
        "Also factor in whether the stock is in a solid uptrend based on its 50-day and 200-day Simple Moving Averages. Keep descriptions analytical, insightful, and detailed. DO NOT use generic filler text."
    )
    
    # Format metrics beautifully
    formatted_vol = f"${stats['avg_daily_dollar_volume']:,.2f}"
    formatted_sales = f"{stats['sales_growth_yoy']:.2f}%"
    formatted_eps = f"{stats['eps_growth_yoy']:.2f}%"
    formatted_mcap = f"${stats['market_cap']:,.2f}"
    sma_status = (
        f"Trading ABOVE 50 SMA (${stats['sma_50']:.2f}) and ABOVE 200 SMA (${stats['sma_200']:.2f})" 
        if stats['is_above_50_sma'] and stats['is_above_200_sma'] 
        else f"SMA 50: ${stats['sma_50']:.2f} (Above: {stats['is_above_50_sma']}), SMA 200: ${stats['sma_200']:.2f} (Above: {stats['is_above_200_sma']})"
    )
    
    prompt = f"""
    Conduct a comprehensive detective-style fundamental & thematic analysis for:
    - Stock Name: {name}
    - Country: {country}
    - Resolved Ticker: {stats['ticker']}
    - Current Price: {stats['current_price']:.2f}
    - Market Cap (raw): {formatted_mcap}
    
    Calculated Quantitative Financial Metrics (Use these directly in your growth and liquidity evaluations):
    - YoY Sales Growth: {formatted_sales}
    - YoY EPS Growth: {formatted_eps}
    - Average Daily Dollar Volume (30-day window): {formatted_vol} USD equivalent
    - 30-Day Price Momentum / Return: {stats['price_return_30d']:.2f}%
    - Technical Trend (SMAs): {sma_status}
    
    Structure your analysis to follow Pratik Patel's framework exactly. Return your findings as a high-fidelity JSON object conforming to the response schema.
    """
    
    primary_model = _get_secret("GEMINI_MODEL", "gemini-2.5-flash").strip()
    
    # Construct the fallback chain dynamically based on the primary model
    fallback_chain = [primary_model]
    if "gemini-2.5-flash" not in fallback_chain:
        fallback_chain.append("gemini-2.5-flash")
    if "gemini-2.0-flash" not in fallback_chain:
        fallback_chain.append("gemini-2.0-flash")
    
    max_retries = 5
    base_delay = 2.0
    
    last_exception = None
    
    for model_name in fallback_chain:
        logger.info(f"Attempting analysis using model '{model_name}' in the fallback chain")
        for attempt in range(max_retries):
            try:
                return _execute_gemini_call(client, model_name, system_instruction, prompt)
            except Exception as e:
                err_msg = str(e).lower()
                is_rate_limit = any(x in err_msg for x in ["429", "resource_exhausted", "rate limit", "quota", "exhausted"])
                
                if is_rate_limit:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter: base_delay^attempt + jitter
                        delay = (base_delay ** attempt) + random.uniform(0.1, 1.0)
                        logger.warning(
                            f"Gemini API rate limit or quota exceeded on attempt {attempt+1}/{max_retries} "
                            f"for model '{model_name}'. Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.warning(
                            f"Model '{model_name}' exhausted all {max_retries} retries due to rate limits."
                        )
                        break  # Break inner loop, move to next model in fallback_chain
                else:
                    logger.error(f"Gemini API call failed with non-rate-limit exception: {str(e)}", exc_info=True)
                    raise e
                    
    # If we exit the fallback chain without returning, raise the last exception
    logger.error("All models in the fallback chain exhausted their retries due to rate limits.", exc_info=True)
    if last_exception:
        raise last_exception
    raise Exception("API Rate Limit Exceeded: All fallback models exhausted.")
