"""
Technical Indicators Calculator
Computes various technical indicators for trading signal generation.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional


class TechnicalIndicators:
    """Calculate technical indicators from price data."""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: List of prices
            period: EMA period
            
        Returns:
            List of EMA values
        """
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        df = pd.DataFrame({'price': prices})
        ema = df['price'].ewm(span=period, adjust=False).mean()
        return ema.tolist()
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: List of prices
            period: RSI period (default: 14)
            
        Returns:
            List of RSI values (0-100)
        """
        if len(prices) < period + 1:
            return [np.nan] * len(prices)
        
        df = pd.DataFrame({'price': prices})
        delta = df['price'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.tolist()
    
    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: List of prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            Tuple of (macd, signal, histogram)
        """
        df = pd.DataFrame({'price': prices})
        
        ema_fast = df['price'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['price'].ewm(span=slow_period, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return macd.tolist(), signal.tolist(), histogram.tolist()
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[List[float], List[float], List[float]]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: List of prices
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        df = pd.DataFrame({'price': prices})
        
        middle = df['price'].rolling(window=period).mean()
        std = df['price'].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper.tolist(), middle.tolist(), lower.tolist()
    
    @staticmethod
    def calculate_atr(
        high: List[float],
        low: List[float],
        close: List[float],
        period: int = 14
    ) -> List[float]:
        """
        Calculate Average True Range.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of close prices
            period: ATR period
            
        Returns:
            List of ATR values
        """
        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close
        })
        
        df['h-l'] = df['high'] - df['low']
        df['h-pc'] = abs(df['high'] - df['close'].shift(1))
        df['l-pc'] = abs(df['low'] - df['close'].shift(1))
        
        df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        atr = df['tr'].rolling(window=period).mean()
        
        return atr.tolist()
    
    @staticmethod
    def calculate_vwap(
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float]
    ) -> List[float]:
        """
        Calculate Volume Weighted Average Price.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of close prices
            volume: List of volumes
            
        Returns:
            List of VWAP values
        """
        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_volume'] = df['typical_price'] * df['volume']
        
        vwap = df['tp_volume'].cumsum() / df['volume'].cumsum()
        
        return vwap.tolist()
    
    @staticmethod
    def calculate_adx(
        high: List[float],
        low: List[float],
        close: List[float],
        period: int = 14
    ) -> List[float]:
        """
        Calculate Average Directional Index.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of close prices
            period: ADX period
            
        Returns:
            List of ADX values
        """
        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close
        })
        
        # Calculate +DM and -DM
        df['h-ph'] = df['high'] - df['high'].shift(1)
        df['pl-l'] = df['low'].shift(1) - df['low']
        
        df['+dm'] = np.where((df['h-ph'] > df['pl-l']) & (df['h-ph'] > 0), df['h-ph'], 0)
        df['-dm'] = np.where((df['pl-l'] > df['h-ph']) & (df['pl-l'] > 0), df['pl-l'], 0)
        
        # Calculate TR
        df['h-l'] = df['high'] - df['low']
        df['h-pc'] = abs(df['high'] - df['close'].shift(1))
        df['l-pc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        
        # Smooth +DM, -DM, and TR
        atr = df['tr'].rolling(window=period).mean()
        pos_di = 100 * (df['+dm'].rolling(window=period).mean() / atr)
        neg_di = 100 * (df['-dm'].rolling(window=period).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.tolist()
    
    @staticmethod
    def parse_klines(klines: List[List]) -> Dict[str, List[float]]:
        """
        Parse k-line data into OHLCV format.
        
        Args:
            klines: Raw k-line data from API
            
        Returns:
            Dict with keys: timestamp, open, high, low, close, volume
        """
        if not klines:
            return {
                'timestamp': [],
                'open': [],
                'high': [],
                'low': [],
                'close': [],
                'volume': []
            }
        
        # Assuming kline format: [timestamp, open, high, low, close, volume, ...]
        return {
            'timestamp': [k[0] for k in klines],
            'open': [float(k[1]) for k in klines],
            'high': [float(k[2]) for k in klines],
            'low': [float(k[3]) for k in klines],
            'close': [float(k[4]) for k in klines],
            'volume': [float(k[5]) for k in klines] if len(klines[0]) > 5 else [0.0] * len(klines)
        }

