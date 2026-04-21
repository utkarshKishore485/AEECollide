import time
from backend.config import OPENAI_API_KEY
import json

# Circuit breaker for quota errors
_last_quota_error_time = 0
QUOTA_ERROR_COOLDOWN = 600 # 10 minutes

def generate_operator_briefing(lmp: float, gas_price: float, spread: float, regime_name: str, confidence: int, forecast_summary: str) -> str:
    """Generate a real-time operator briefing using OpenAI GPT-4o."""
    global _last_quota_error_time

    if not OPENAI_API_KEY:
        return _fallback_briefing(spread, regime_name, confidence, forecast_summary)

    # Check circuit breaker
    if time.time() - _last_quota_error_time < QUOTA_ERROR_COOLDOWN:
        return _fallback_briefing(spread, regime_name, confidence, forecast_summary)
    prompt = f"""
You are an expert energy dispatch AI acting as the intelligence behind a Bloomberg Terminal-style grid operator dashboard.
Your job is to read the current real-time market data and write a concise, plain-English 3-4 sentence directive to a data center operator managing a Behind-The-Meter (BTM) gas generator.

MARKET CONTEXT:
- Current Regime: {regime_name} (Confidence: {confidence}%)
- Current ERCOT LMP: ${lmp:.2f}/MWh
- Current Waha Gas Price: ${gas_price:.2f}/MMBtu
- Current Generation Spread (LMP - Gen Cost): ${spread:.2f}/MWh. If positive, GENERATE. If negative, IMPORT from grid.
- Next 72-Hour Forecast Summary: {forecast_summary}

RULES:
- Be extremely brief and direct (3-4 sentences max).
- Do not use conversational filler (No "Here is the summary" or "Based on the data"). This is a control room terminal.
- Explicitly state the recommended action: either "sustain generation" (if running the generator is profitable) or "import from grid" (if buying from the grid is cheaper).
- Contextualize the forecast. If a wind glut is coming and spreads will go negative, warn the operator to prepare to switch to grid power.
"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Dispatch IQ, an AI grid operator system."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        
        # If it's a quota error, trigger cooldown
        if "insufficient_quota" in str(e).lower() or "429" in str(e):
            _last_quota_error_time = time.time()
            print("🚀 OpenAI Quota exceeded. Entering 10-minute cooldown.")

        # Fallback to local template if API fails
        return _fallback_briefing(spread, regime_name, confidence, forecast_summary)

def _fallback_briefing(spread, regime_name, confidence, forecast_summary):
    action = "sustain generation" if spread > 0 else "import from grid"
    return (
        f"You are currently in a {regime_name} regime with {confidence}% confidence. "
        f"Grid prices are {'elevated' if spread > 15 else 'moderate'} and "
        f"{'expected to remain above' if spread > 0 else 'currently below'} your generation cost. "
        f"{forecast_summary} "
        f"Recommended action: {action}."
    )
