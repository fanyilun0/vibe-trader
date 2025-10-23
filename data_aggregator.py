"""
Data Aggregator Module
Fetches and normalizes market data from Aster DEX, calculates technical indicators.
"""
from typing import Dict, List, Optional
import time
import json
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
        # Get account info (includes balances and positions)
        try:
            account_data = self.client.get_account_info()
            
            # Calculate total equity and available balance
            total_equity = float(account_data.get('totalWalletBalance', 0.0))
            available_cash = float(account_data.get('availableBalance', 0.0))
            
            # Get positions from account data
            positions_data = account_data.get('positions', [])
            
        except Exception as e:
            print(f"Warning: Could not fetch account info from /fapi/v2/account: {e}")
            # Fallback: try separate balance and position endpoints
            try:
                balances = self.client.get_account_balances()
                positions_data = self.client.get_positions()
                
                # Calculate from balance array
                total_equity = sum(float(b.get('balance', 0.0)) for b in balances if isinstance(b, dict))
                available_cash = sum(float(b.get('availableBalance', 0.0)) for b in balances if isinstance(b, dict))
            except Exception as e2:
                print(f"Warning: Could not fetch balances/positions: {e2}")
                return {
                    'total_return_percent': 0.0,
                    'available_cash': 0.0,
                    'account_value': 0.0,
                    'sharpe_ratio': 0.0,
                    'positions': []
                }
        
        # Format positions
        formatted_positions = []
        for pos in positions_data:
            # Only include positions with non-zero amount
            pos_amt = float(pos.get('positionAmt', 0.0))
            if pos_amt != 0:
                formatted_positions.append({
                    'symbol': pos.get('symbol', ''),
                    'side': 'LONG' if pos_amt > 0 else 'SHORT',
                    'size': abs(pos_amt),
                    'entry_price': float(pos.get('entryPrice', 0.0)),
                    'mark_price': float(pos.get('markPrice', 0.0)),
                    'liquidation_price': float(pos.get('liquidationPrice', 0.0)),
                    'unrealized_pnl': float(pos.get('unRealizedProfit', 0.0)),
                    'leverage': int(pos.get('leverage', 1)),
                    'notional': float(pos.get('notional', 0.0))
                })
        
        return {
            'total_return_percent': 0.0,  # Would need to track initial capital
            'available_cash': available_cash,
            'account_value': total_equity,
            'sharpe_ratio': 0.0,  # Would need historical returns to calculate
            'positions': formatted_positions
        }
    
    def print_market_data(self, market_data: Dict):
        """
        Print market data in a beautiful, readable format.
        
        Args:
            market_data: The complete market data structure
        """
        print("\n" + "="*100)
        print("📊 市场数据总览 (Market Data Overview)")
        print("="*100)
        
        # Print metadata
        metadata = market_data.get('metadata', {})
        print(f"\n⏰ 时间信息:")
        print(f"   当前时间: {metadata.get('current_timestamp', 'N/A')}")
        print(f"   运行时长: {metadata.get('minutes_trading', 0)} 分钟")
        print(f"   调用次数: {metadata.get('invocation_count', 0)}")
        
        # Print account info
        account_info = market_data.get('account_info', {})
        print(f"\n💰 账户信息:")
        print(f"   账户总值: ${account_info.get('account_value', 0):.2f}")
        print(f"   可用资金: ${account_info.get('available_cash', 0):.2f}")
        print(f"   总回报率: {account_info.get('total_return_percent', 0):.2f}%")
        print(f"   夏普比率: {account_info.get('sharpe_ratio', 0):.2f}")
        
        # Print positions
        positions = account_info.get('positions', [])
        if positions:
            print(f"\n📈 持仓信息 ({len(positions)} 个持仓):")
            for pos in positions:
                print(f"\n   {pos.get('symbol', 'N/A')} - {pos.get('side', 'N/A')}")
                print(f"      持仓量: {pos.get('size', 0):.4f}")
                print(f"      开仓价: ${pos.get('entry_price', 0):.2f}")
                print(f"      当前价: ${pos.get('mark_price', 0):.2f}")
                print(f"      强平价: ${pos.get('liquidation_price', 0):.2f}")
                print(f"      未实现盈亏: ${pos.get('unrealized_pnl', 0):.2f}")
                print(f"      杠杆: {pos.get('leverage', 1)}x")
        else:
            print(f"\n📈 持仓信息: 无持仓")
        
        # Print coin data
        coins_data = market_data.get('coins_data', {})
        print(f"\n💎 交易对数据 ({len(coins_data)} 个交易对):")
        
        for symbol, data in coins_data.items():
            print(f"\n{'─'*100}")
            print(f"🪙 {symbol}")
            print(f"{'─'*100}")
            
            # Current price and funding
            print(f"\n   💵 价格信息:")
            print(f"      当前价格: ${data.get('current_price', 0):.2f}")
            print(f"      资金费率: {data.get('funding_rate', 0):.6f}")
            
            # Open interest
            oi = data.get('open_interest', {})
            print(f"\n   📊 持仓量:")
            print(f"      最新持仓量: {oi.get('latest', 0):.2f}")
            print(f"      平均持仓量: {oi.get('average', 0):.2f}")
            
            # Order book
            order_book = data.get('order_book', {})
            bids = order_book.get('bids', [])[:3]
            asks = order_book.get('asks', [])[:3]
            if bids or asks:
                print(f"\n   📖 订单簿 (Top 3):")
                if asks:
                    print(f"      卖单 (Asks):")
                    for ask in reversed(asks):
                        if len(ask) >= 2:
                            print(f"         ${float(ask[0]):.2f} × {float(ask[1]):.4f}")
                if bids:
                    print(f"      买单 (Bids):")
                    for bid in bids:
                        if len(bid) >= 2:
                            print(f"         ${float(bid[0]):.2f} × {float(bid[1]):.4f}")
            
            # Intraday indicators
            intraday = data.get('intraday', {})
            ind = intraday.get('indicators', {})
            current = ind.get('current', {})
            
            if current:
                print(f"\n   📈 短期技术指标 ({intraday.get('interval', '3m')} 周期):")
                if current.get('ema20') is not None:
                    print(f"      EMA20: ${current.get('ema20', 0):.2f}")
                if current.get('ema50') is not None:
                    print(f"      EMA50: ${current.get('ema50', 0):.2f}")
                if current.get('rsi7') is not None:
                    print(f"      RSI(7): {current.get('rsi7', 0):.2f}")
                if current.get('rsi14') is not None:
                    print(f"      RSI(14): {current.get('rsi14', 0):.2f}")
                if current.get('macd') is not None:
                    print(f"      MACD: {current.get('macd', 0):.4f}")
                    print(f"      MACD Signal: {current.get('macd_signal', 0):.4f}")
                    print(f"      MACD Histogram: {current.get('macd_histogram', 0):.4f}")
                if current.get('bb_upper') is not None:
                    print(f"      布林带上轨: ${current.get('bb_upper', 0):.2f}")
                    print(f"      布林带中轨: ${current.get('bb_middle', 0):.2f}")
                    print(f"      布林带下轨: ${current.get('bb_lower', 0):.2f}")
                if current.get('atr14') is not None:
                    print(f"      ATR(14): ${current.get('atr14', 0):.2f}")
                if current.get('adx') is not None:
                    print(f"      ADX: {current.get('adx', 0):.2f}")
            
            # Longterm indicators
            longterm = data.get('longterm', {})
            lt_ind = longterm.get('indicators', {})
            lt_current = lt_ind.get('current', {})
            
            if lt_current:
                print(f"\n   📊 长期技术指标 ({longterm.get('interval', '4h')} 周期):")
                if lt_current.get('ema20') is not None:
                    print(f"      EMA20: ${lt_current.get('ema20', 0):.2f}")
                if lt_current.get('ema50') is not None:
                    print(f"      EMA50: ${lt_current.get('ema50', 0):.2f}")
                if lt_current.get('rsi14') is not None:
                    print(f"      RSI(14): {lt_current.get('rsi14', 0):.2f}")
                if lt_current.get('macd') is not None:
                    print(f"      MACD: {lt_current.get('macd', 0):.4f}")
                if lt_current.get('atr3') is not None:
                    print(f"      ATR(3): ${lt_current.get('atr3', 0):.2f}")
                if lt_current.get('atr14') is not None:
                    print(f"      ATR(14): ${lt_current.get('atr14', 0):.2f}")
            
            # Price and volume data
            prices = intraday.get('prices', [])
            volumes = intraday.get('volumes', [])
            if prices and volumes:
                print(f"\n   📉 价格和成交量统计 (最近 {len(prices)} 根K线):")
                print(f"      价格范围: ${min(prices):.2f} - ${max(prices):.2f}")
                print(f"      平均价格: ${sum(prices)/len(prices):.2f}")
                print(f"      平均成交量: {sum(volumes)/len(volumes):.2f}")
        
        print(f"\n{'='*100}\n")

