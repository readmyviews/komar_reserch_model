import os
import json
import logging
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import anthropic

load_dotenv()

# Configure logging
logger = logging.getLogger("komar.agent")

class AnalysisResponse(BaseModel):
    stock_category: str = Field(description="Explicitly categorize as CANSLIM Stock, Sales Grower, or Story Stock")
    fundamental_layer_details: str = Field(description="Analysis of Sales & EPS growth YoY against target thresholds (20%, 30%, 40%+)")
    story_layer_details: str = Field(description="Detective breakdown of the business model, products, and key future catalysts (AI, clean energy, SaaS, robotics, etc.)")
    sister_stocks_details: str = Field(description="Direct competitors or sister stocks in same sector globally/locally showing strong growth/momentum, and sector trend validation")
    liquidity_details: str = Field(description="Liquidity assessment comparing average daily dollar volume to Julian Komar's minimum thresholds ($20M-$100M USD mature, $5M-$10M USD young micro-cap)")
    rating: int = Field(description="Julian Komar rating score from 1 (poor fit) to 10 (perfect fit)")
    rating_breakdown: str = Field(description="Explain exactly why the rating out of 10 was given. Score each of these five dimensions (out of 2 points each): 1) YoY Sales Growth, 2) YoY EPS/Income Growth, 3) Catalyst & Secular Theme Power, 4) Sister Stock Support & Sector Momentum, 5) Liquidity & Institutional Size. Format as a clear, beautifully structured list showing points like '- YoY Sales Growth: 2/2' and summing up to the total score.")
    buying_range: str = Field(description="A suggested optimal buying price range in native currency (e.g. ₹480 - ₹510 or $185 - $195) based on technical setup, key SMAs, and support/resistance zones. Provide the native currency symbol (₹ or $) inside the range string.")
    buying_range_status: str = Field(description="Buying status of the current stock price relative to the buying range (e.g. 'IN BUY ZONE', 'AWAITING PULLBACK', or 'BREAKOUT BUY')")
    verdict: str = Field(description="Brief final verdict on whether the stock fits the Julian Komar institutional accumulation profile")

def _run_anthropic_analysis(name: str, country: str, stats: dict) -> dict:
    """
    Formulates the qualitative prompt and fires it to Anthropic Claude.
    Guarantees structured schema output by using forced tool calling.
    Handles extended thinking configurations for compatible models.
    """
    start_time = time.time()
    logger.info(f"Initiating Anthropic detective analysis for stock '{name}' ({country})")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is missing!")
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Please add it to your .env file.")
        
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
    
    system_instruction = (
        "You are an expert stock market analyst applying seasoned trader Julian Komar's "
        "fundamental and thematic research methodology. You act like a 'detective' to figure "
        "out exactly what big institutional investors see in a company's fundamentals and thematic story.\n\n"
        "Analyze the user-provided stock by detailing: \n"
        "1. Fundamental Growth Layer: Evaluate YoY Sales/EPS growth figures against target thresholds (20%, 30%, 40%+). Categorize the stock as CANSLIM Stock, Sales Grower, or Story Stock.\n"
        "2. The Story Layer: Explain the business model, current success, and core future catalysts (AI, cloud, cyber, clean energy, biotech, etc.).\n"
        "3. Sister Stocks & Theme Alignment: List 3-4 competitor/sister stocks in the same country or globally also showing strong momentum. Confirm if the overall industry/theme is in high institutional demand.\n"
        "4. Institutional Quality Check (Liquidity): Compare average daily dollar volume to Komar's minimum thresholds ($20M-$100M USD mature, $5M-$10M USD young micro-cap). Assess if institutions can accumulate and exit safely.\n\n"
        "Provide a final verdict, a rating score from 1 to 10, and a rigorous rating breakdown scoring five key elements (2 points each) to explain exactly why this rating was given. "
        "Also factor in whether the stock is in a solid uptrend based on its 50-day and 200-day Simple Moving Averages. Keep descriptions analytical, insightful, and detailed. DO NOT use generic filler text."
    )
    
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
    
    Structure your analysis to follow Julian Komar's framework exactly. Return your findings as a structured analysis payload using the forced tool schema.
    """
    
    tool_definition = {
        "name": "analyze_stock",
        "description": "Returns the structured qualitative research report matching the Julian Komar framework schema.",
        "input_schema": AnalysisResponse.model_json_schema()
    }
    
    thinking_budget_str = os.getenv("ANTHROPIC_THINKING_BUDGET", "1024")
    try:
        thinking_budget = int(thinking_budget_str)
    except ValueError:
        thinking_budget = 1024
        
    client = anthropic.Anthropic(api_key=api_key)
    
    thinking_enabled = False
    if thinking_budget > 0 and ("claude-3-7" in model_name or "claude-3.7" in model_name or "claude-4" in model_name or "claude-v" in model_name or "thinking" in model_name):
        thinking_enabled = True
        
    kwargs = {
        "model": model_name,
        "system": system_instruction,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [tool_definition],
        "tool_choice": {"type": "tool", "name": "analyze_stock"}
    }
    
    if thinking_enabled:
        logger.info(f"Firing Anthropic Request with Thinking enabled (budget={thinking_budget} tokens) using model: '{model_name}'")
        kwargs["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        }
        kwargs["max_tokens"] = thinking_budget + 4000
    else:
        logger.info(f"Firing Anthropic Request with Thinking disabled using model: '{model_name}'")
        kwargs["max_tokens"] = 4000
        
    response = client.messages.create(**kwargs)
    
    tool_use_block = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "analyze_stock":
            tool_use_block = block
            break
            
    if not tool_use_block:
        logger.error("Claude did not invoke the forced tool 'analyze_stock'")
        raise ValueError("Anthropic LLM did not return a structured analysis tool block.")
        
    elapsed = time.time() - start_time
    logger.info(f"Anthropic analysis completed successfully in {elapsed:.2f}s")
    return tool_use_block.input

def generate_komar_analysis(name: str, country: str, stats: dict) -> dict:
    """
    Formulates a detailed research prompt applying the Julian Komar framework to the stock.
    Delegates to Gemini or Anthropic based on LLM_PROVIDER.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    
    if provider == "anthropic":
        return _run_anthropic_analysis(name, country, stats)
        
    # Gemini flow fallback
    start_time = time.time()
    logger.info(f"Initiating Gemini detective analysis for stock '{name}' ({country})")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is missing!")
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your .env file.")
        
    try:
        logger.debug("Initializing Google GenAI Client")
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "You are an expert stock market analyst applying seasoned trader Julian Komar's "
            "fundamental and thematic research methodology. You act like a 'detective' to figure "
            "out exactly what big institutional investors see in a company's fundamentals and thematic story.\n\n"
            "Analyze the user-provided stock by detailing: \n"
            "1. Fundamental Growth Layer: Evaluate YoY Sales/EPS growth figures against target thresholds (20%, 30%, 40%+). Categorize the stock as CANSLIM Stock, Sales Grower, or Story Stock.\n"
            "2. The Story Layer: Explain the business model, current success, and core future catalysts (AI, cloud, cyber, clean energy, biotech, etc.).\n"
            "3. Sister Stocks & Theme Alignment: List 3-4 competitor/sister stocks in the same country or globally also showing strong momentum. Confirm if the overall industry/theme is in high institutional demand.\n"
            "4. Institutional Quality Check (Liquidity): Compare average daily dollar volume to Komar's minimum thresholds ($20M-$100M USD mature, $5M-$10M USD young micro-cap). Assess if institutions can accumulate and exit safely.\n\n"
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
        
        Structure your analysis to follow Julian Komar's framework exactly. Return your findings as a high-fidelity JSON object conforming to the response schema.
        """
        
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        logger.info(f"Firing request to model '{model_name}' for ticker '{stats['ticker']}'")
        
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
        logger.info(f"Gemini analysis completed successfully in {elapsed:.2f}s")
        
        result_dict = json.loads(response.text)
        logger.debug(f"Parsed response JSON successfully: {list(result_dict.keys())}")
        return result_dict
        
    except Exception as e:
        logger.error(f"Error executing Gemini detective analysis for '{name}': {str(e)}", exc_info=True)
        raise
