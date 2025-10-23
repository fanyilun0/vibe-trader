"""
Data Aggregator Module
Fetches and normalizes market data from Aster DEX, calculates technical indicators.
"""
from typing import Dict, List, Optional
import time
from aster_client import AsterClient
from indicators import TechnicalIndicators
from config import Config


class DataAggregator:
    """Aggregates market data and calculates technical indicators."""
    
    def __init__(self, aster_client: Optional[AsterClient] = None):
        """
        Initialize the data aggregator.
        
        Args:
            aster_client: AsterClient instance (creates new if not provided)
        """
        self.client = aster_client or AsterClient()
        self.indicators = TechnicalIndicators()
        self.start_time = time.time()
        self.invocation_count = 0
    
    def fetch_all_data(self, symbols: Optional[List[str]] = None) -> Dict:
        """
        Fetch all required data for multiple symbols.
        
        Args:
            symbols: List of symbols to fetch (defaults to Config.TRADING_SYMBOLS)
            
        Returns:
            Structured data dict ready for LLM prompt
        """
        self.invocation_count += 1
        
        if symbols is None:
            symbols = Config.TRADING_SYMBOLS
        
        # Calculate runtime
        minutes_trading = int((time.time() - self.start_time) / 60)
        current_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        
        # Fetch account information
        try:
            account_info = self._fetch_account_info()
        except Exception as e:
            print(f"Warning: Could not fetch account info: {e}")
            account_info = {
                'total_return_percent': 0.0,
                'available_cash': 0.0,
                'account_value': 0.0,
                'sharpe_ratio': 0.0,
                'positions': []
            }
        
        # Fetch data for each symbol
        coins_data = {}
        for symbol in symbols:
            try:
                coin_data = self._fetch_symbol_data(symbol)
                coins_data[symbol] = coin_data
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                continue
        
        # Construct the complete data structure
        return {
            'metadata': {
                'minutes_trading': minutes_trading,
                'current_timestamp': current_timestamp,
                'invocation_count': self.invocation_count
            },
            'coins_data': coins_data,
            'account_info': account_info
        }
    
    def _fetch_symbol_data(self, symbol: str) -> Dict:
        """
        Fetch comprehensive data for a single symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dict containing all market data and indicators for the symbol
        """
        # Fetch intraday k-lines (3-minute interval)
        intraday_klines = self.client.get_klines(
            symbol=symbol,
            interval=Config.INTRADAY_INTERVAL,
            limit=Config.KLINE_LIMIT
        )
        intraday_ohlcv = self.indicators.parse_klines(intraday_klines)
        
        # Fetch long-term k-lines (4-hour interval)
        longterm_klines = self.client.get_klines(
            symbol=symbol,
            interval=Config.LONGTERM_INTERVAL,
            limit=50  # Fewer candles for long-term view
        )
        longterm_ohlcv = self.indicators.parse_klines(longterm_klines)
        
        # Fetch funding rate
        try:
            funding_data = self.client.get_funding_rate(symbol)
            funding_rate = funding_data.get('fundingRate', 0.0)
        except:
            funding_rate = 0.0
        
        # Fetch order book for spread analysis
        try:
            order_book = self.client.get_order_book(symbol, limit=10)
        except:
            order_book = {'bids': [], 'asks': []}
        
        # Calculate intraday indicators
        intraday_indicators = self._calculate_indicators(intraday_ohlcv)
        
        # Calculate long-term indicators
        longterm_indicators = self._calculate_indicators(longterm_ohlcv)
        
        # Get current price (last close)
        current_price = intraday_ohlcv['close'][-1] if intraday_ohlcv['close'] else 0.0
        
        # Calculate open interest metrics
        open_interest_latest = 0.0  # Would need specific API endpoint
        open_interest_average = 0.0
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'funding_rate': funding_rate,
            'open_interest': {
                'latest': open_interest_latest,
                'average': open_interest_average
            },
            'order_book': {
                'bids': order_book.get('bids', [])[:5],
                'asks': order_book.get('asks', [])[:5]
            },
            'intraday': {
                'interval': Config.INTRADAY_INTERVAL,
                'prices': intraday_ohlcv['close'],
                'volumes': intraday_ohlcv['volume'],
                'indicators': intraday_indicators
            },
            'longterm': {
                'interval': Config.LONGTERM_INTERVAL,
                'indicators': longterm_indicators
            }
        }
    
    def _calculate_indicators(self, ohlcv: Dict[str, List[float]]) -> Dict:
        """
        Calculate all technical indicators from OHLCV data.
        
        Args:
            ohlcv: Dict with open, high, low, close, volume
            
        Returns:
            Dict of calculated indicators
        """
        close = ohlcv['close']
        high = ohlcv['high']
        low = ohlcv['low']
        volume = ohlcv['volume']
        
        # Calculate EMA
        ema20 = self.indicators.calculate_ema(close, 20)
        ema50 = self.indicators.calculate_ema(close, 50)
        
        # Calculate RSI
        rsi7 = self.indicators.calculate_rsi(close, 7)
        rsi14 = self.indicators.calculate_rsi(close, 14)
        
        # Calculate MACD
        macd, signal, histogram = self.indicators.calculate_macd(close)
        
        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.indicators.calculate_bollinger_bands(close)
        
        # Calculate ATR
        atr3 = self.indicators.calculate_atr(high, low, close, 3)
        atr14 = self.indicators.calculate_atr(high, low, close, 14)
        
        # Calculate VWAP
        vwap = self.indicators.calculate_vwap(high, low, close, volume)
        
        # Calculate ADX
        adx = self.indicators.calculate_adx(high, low, close, 14)
        
        # Get current values (last in series)
        current_idx = -1
        
        return {
            'ema20': ema20,
            'ema50': ema50,
            'rsi7': rsi7,
            'rsi14': rsi14,
            'macd': macd,
            'macd_signal': signal,
            'macd_histogram': histogram,
            'bollinger_bands': {
                'upper': bb_upper,
                'middle': bb_middle,
                'lower': bb_lower
            },
            'atr3': atr3,
            'atr14': atr14,
            'vwap': vwap,
            'adx': adx,
            # Current values for quick access
            'current': {
                'ema20': ema20[current_idx] if ema20 else None,
                'ema50': ema50[current_idx] if ema50 else None,
                'rsi7': rsi7[current_idx] if rsi7 else None,
                'rsi14': rsi14[current_idx] if rsi14 else None,
                'macd': macd[current_idx] if macd else None,
                'macd_signal': signal[current_idx] if signal else None,
                'macd_histogram': histogram[current_idx] if histogram else None,
                'bb_upper': bb_upper[current_idx] if bb_upper else None,
                'bb_middle': bb_middle[current_idx] if bb_middle else None,
                'bb_lower': bb_lower[current_idx] if bb_lower else None,
                'atr3': atr3[current_idx] if atr3 else None,
                'atr14': atr14[current_idx] if atr14 else None,
                'vwap': vwap[current_idx] if vwap else None,
                'adx': adx[current_idx] if adx else None
            }
        }
    
    def _fetch_account_info(self) -> Dict:
        """
        Fetch account balance and position information.
        
        Returns:
            Dict with account metrics
        """
        # Get account balances
        balances = self.client.get_account_balances()
        
        # Get current positions
        positions = self.client.get_positions()
        
        # Calculate account metrics
        total_equity = 0.0
        available_cash = 0.0
        
        if isinstance(balances, dict):
            total_equity = float(balances.get('totalEquity', 0.0))
            available_cash = float(balances.get('availableBalance', 0.0))
        
        # Format positions
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                'symbol': pos.get('symbol', ''),
                'side': pos.get('side', ''),
                'size': float(pos.get('size', 0.0)),
                'entry_price': float(pos.get('entryPrice', 0.0)),
                'mark_price': float(pos.get('markPrice', 0.0)),
                'liquidation_price': float(pos.get('liquidationPrice', 0.0)),
                'unrealized_pnl': float(pos.get('unrealizedPnl', 0.0)),
                'leverage': int(pos.get('leverage', 1))
            })
        
        return {
            'total_return_percent': 0.0,  # Would need to track initial capital
            'available_cash': available_cash,
            'account_value': total_equity,
            'sharpe_ratio': 0.0,  # Would need historical returns to calculate
            'positions': formatted_positions
        }

