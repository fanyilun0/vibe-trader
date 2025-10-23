"""
Signal Generation Core
Uses DeepSeek LLM to analyze market data and generate trading signals.
"""
import json
from typing import Dict, Optional, Any
from openai import OpenAI
from config import Config


class SignalGenerator:
    """Generates trading signals using DeepSeek LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the signal generator.
        
        Args:
            api_key: DeepSeek API key (defaults to config)
            model: DeepSeek model name (defaults to config)
        """
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.model = model or Config.DEEPSEEK_MODEL
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=Config.DEEPSEEK_BASE_URL
        )
    
    def get_signal(self, market_data: Dict) -> Dict[str, Any]:
        """
        Generate trading signal from market data.
        
        Args:
            market_data: Structured market data from DataAggregator
            
        Returns:
            Trading signal dict with action, reasoning, entry, stop_loss, take_profit
        """
        # Construct the prompt
        prompt = self._construct_prompt(market_data)
        
        # Query DeepSeek
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert quantitative analyst specializing in high-frequency trading of cryptocurrency perpetual futures. Your task is to analyze market data and provide precise, actionable trading signals."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=Config.DEEPSEEK_TEMPERATURE
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            signal = self._parse_response(response_text)
            
            return signal
            
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            # Return a HOLD signal on error
            return {
                'action': 'HOLD',
                'symbol': None,
                'reasoning': f"Error generating signal: {str(e)}",
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'confidence': 0.0,
                'leverage': 1
            }
    
    def _construct_prompt(self, market_data: Dict) -> str:
        """
        Construct the LLM prompt from market data.
        Uses the template structure from template.md.
        
        Args:
            market_data: Market data dict
            
        Returns:
            Formatted prompt string
        """
        metadata = market_data.get('metadata', {})
        coins_data = market_data.get('coins_data', {})
        account_info = market_data.get('account_info', {})
        
        # Build the prompt following the template structure
        prompt_parts = []
        
        # Header
        prompt_parts.append(f"""It has been {metadata.get('minutes_trading', 0)} minutes since you started trading.
The current time is {metadata.get('current_timestamp', 'N/A')} and you've been invoked {metadata.get('invocation_count', 0)} times.

Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha.
ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST
Timeframes note: Intraday series are provided at {Config.INTRADAY_INTERVAL} intervals. Long-term context uses {Config.LONGTERM_INTERVAL} intervals.

CURRENT MARKET STATE FOR ALL COINS
""")
        
        # Add data for each coin
        for symbol, coin_data in coins_data.items():
            prompt_parts.append(self._format_coin_data(symbol, coin_data))
        
        # Add account information
        prompt_parts.append(self._format_account_info(account_info))
        
        # Add trading instructions
        prompt_parts.append(self._get_trading_instructions())
        
        return "\n".join(prompt_parts)
    
    def _format_coin_data(self, symbol: str, data: Dict) -> str:
        """Format data for a single coin following template.md structure."""
        intraday = data.get('intraday', {})
        longterm = data.get('longterm', {})
        intraday_ind = intraday.get('indicators', {})
        longterm_ind = longterm.get('indicators', {})
        current_ind = intraday_ind.get('current', {})
        longterm_current = longterm_ind.get('current', {})
        
        # Format price lists (show last 20 values for brevity)
        prices = intraday.get('prices', [])
        prices_str = str(prices[-20:]) if len(prices) > 20 else str(prices)
        
        # Get indicator lists
        ema20_list = intraday_ind.get('ema20', [])
        ema20_str = str([round(x, 2) if x and not str(x) == 'nan' else None for x in ema20_list[-20:]]) if ema20_list else "[]"
        
        macd_list = intraday_ind.get('macd', [])
        macd_str = str([round(x, 2) if x and not str(x) == 'nan' else None for x in macd_list[-20:]]) if macd_list else "[]"
        
        rsi7_list = intraday_ind.get('rsi7', [])
        rsi7_str = str([round(x, 2) if x and not str(x) == 'nan' else None for x in rsi7_list[-20:]]) if rsi7_list else "[]"
        
        rsi14_list = intraday_ind.get('rsi14', [])
        rsi14_str = str([round(x, 2) if x and not str(x) == 'nan' else None for x in rsi14_list[-20:]]) if rsi14_list else "[]"
        
        longterm_macd = longterm_ind.get('macd', [])
        longterm_macd_str = str([round(x, 2) if x and not str(x) == 'nan' else None for x in longterm_macd[-10:]]) if longterm_macd else "[]"
        
        longterm_rsi14 = longterm_ind.get('rsi14', [])
        longterm_rsi14_str = str([round(x, 2) if x and not str(x) == 'nan' else None for x in longterm_rsi14[-10:]]) if longterm_rsi14 else "[]"
        
        return f"""
ALL {symbol} DATA
current_price = {data.get('current_price', 0.0):.2f}, current_ema20 = {current_ind.get('ema20', 0.0):.2f}, current_macd = {current_ind.get('macd', 0.0):.2f}, current_rsi (7 period) = {current_ind.get('rsi7', 0.0):.2f}

In addition, here is the latest {symbol} open interest and funding rate for perps:
Open Interest: Latest: {data.get('open_interest', {}).get('latest', 0.0)} Average: {data.get('open_interest', {}).get('average', 0.0)}
Funding Rate: {data.get('funding_rate', 0.0):.6f}

Intraday series ({intraday.get('interval', Config.INTRADAY_INTERVAL)} interval, oldest → latest):
Mid prices: {prices_str}
EMA indicators (20-period): {ema20_str}
MACD indicators: {macd_str}
RSI indicators (7-Period): {rsi7_str}
RSI indicators (14-Period): {rsi14_str}

Additional Intraday Indicators:
Bollinger Bands: Upper={current_ind.get('bb_upper', 0.0):.2f}, Middle={current_ind.get('bb_middle', 0.0):.2f}, Lower={current_ind.get('bb_lower', 0.0):.2f}
VWAP: {current_ind.get('vwap', 0.0):.2f}
ADX (14-period): {current_ind.get('adx', 0.0):.2f}

Longer-term context ({longterm.get('interval', Config.LONGTERM_INTERVAL)} timeframe):
20-Period EMA: {longterm_current.get('ema20', 0.0):.2f} vs. 50-Period EMA: {longterm_current.get('ema50', 0.0):.2f}
3-Period ATR: {longterm_current.get('atr3', 0.0):.2f} vs. 14-Period ATR: {longterm_current.get('atr14', 0.0):.2f}
MACD indicators: {longterm_macd_str}
RSI indicators (14-Period): {longterm_rsi14_str}
"""
    
    def _format_account_info(self, account_info: Dict) -> str:
        """Format account information following template.md structure."""
        positions = account_info.get('positions', [])
        positions_str = json.dumps(positions, indent=2) if positions else "No open positions"
        
        return f"""
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {account_info.get('total_return_percent', 0.0):.2f}%
Available Cash: ${account_info.get('available_cash', 0.0):.2f}
Current Account Value: ${account_info.get('account_value', 0.0):.2f}
Sharpe Ratio: {account_info.get('sharpe_ratio', 0.0):.2f}

Current live positions & performance:
{positions_str}
"""
    
    def _get_trading_instructions(self) -> str:
        """Get the trading instructions for the LLM."""
        return """
TRADING INSTRUCTIONS

Your task is to analyze the above market data and determine the optimal trading action.

ANALYSIS FRAMEWORK:
1. Trend Analysis: Examine EMA crossovers, price action relative to moving averages
2. Momentum: Evaluate RSI levels (oversold <30, overbought >70), MACD crossovers and divergences
3. Volatility: Consider ATR for position sizing, Bollinger Band width and price position
4. Volume Profile: Analyze VWAP relative to current price
5. Trend Strength: Use ADX (>25 indicates strong trend)
6. Funding Rate: Consider cost of holding positions (negative funding favors shorts, positive favors longs)
7. Risk Management: Always define stop-loss levels based on ATR and key support/resistance

DECISION PROCESS:
- Think step-by-step through your analysis
- Consider multiple timeframes (intraday vs long-term)
- Evaluate confluence of signals (multiple indicators agreeing)
- Factor in current positions and available capital
- Only take high-conviction trades (confidence > 0.7)

RISK RULES (MANDATORY):
- Maximum position size: {max_position}% of account value
- Risk per trade: {risk_per_trade}% of account value
- Stop-loss MUST be defined for every LONG or SHORT action
- Take-profit should be at least 1.5x the distance to stop-loss (minimum 1.5:1 reward/risk)
- Consider funding rate impact for longer holding periods
- Leverage should be inversely proportional to volatility (high ATR = lower leverage)

OUTPUT FORMAT:
You must provide your analysis step-by-step, then output ONLY a JSON object in the following format:

{{
  "action": "LONG" | "SHORT" | "HOLD" | "CLOSE",
  "symbol": "BTC-PERP" | "ETH-PERP" | "SOL-PERP" | null,
  "reasoning": "Your detailed step-by-step analysis explaining the decision",
  "entry_price": <expected entry price as float, or null>,
  "stop_loss": <stop loss price as float, or null>,
  "take_profit": <take profit price as float, or null>,
  "confidence": <confidence level 0.0 to 1.0>,
  "leverage": <recommended leverage 1-{max_leverage}>
}}

IMPORTANT:
- For HOLD or CLOSE actions, set symbol, entry_price, stop_loss, take_profit to null
- CLOSE action closes ALL positions for the specified symbol
- confidence should reflect your conviction (only trade if > 0.7)
- reasoning must be detailed and show your step-by-step logical process
- stop_loss is MANDATORY for LONG/SHORT actions
""".format(
            max_position=Config.MAX_POSITION_SIZE_PERCENT,
            risk_per_trade=Config.RISK_PER_TRADE_PERCENT,
            max_leverage=Config.MAX_LEVERAGE
        )
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract the trading signal JSON.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed signal dict
        """
        try:
            # Try to find JSON in the response
            # Look for content between { and }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                signal = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['action', 'symbol', 'reasoning']
                if all(field in signal for field in required_fields):
                    # Ensure proper types
                    signal['action'] = str(signal['action']).upper()
                    signal.setdefault('entry_price', None)
                    signal.setdefault('stop_loss', None)
                    signal.setdefault('take_profit', None)
                    signal.setdefault('confidence', 0.5)
                    signal.setdefault('leverage', Config.DEFAULT_LEVERAGE)
                    
                    return signal
            
            # If JSON parsing fails, return HOLD
            return {
                'action': 'HOLD',
                'symbol': None,
                'reasoning': f"Failed to parse valid signal from response: {response_text[:200]}",
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'confidence': 0.0,
                'leverage': 1
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {
                'action': 'HOLD',
                'symbol': None,
                'reasoning': f"JSON parsing error: {str(e)}",
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'confidence': 0.0,
                'leverage': 1
            }

