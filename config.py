"""
Configuration module for the Vibe Trader bot.
Loads environment variables and provides centralized configuration access.
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration for the trading bot."""
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_TEMPERATURE: float = 0.2  # Low temperature for deterministic analysis
    
    # Aster DEX Configuration
    ASTER_API_KEY: str = os.getenv("ASTER_API_KEY", "")
    ASTER_API_SECRET: str = os.getenv("ASTER_API_SECRET", "")
    ASTER_API_PASSPHRASE: str = os.getenv("ASTER_API_PASSPHRASE", "")
    ASTER_BASE_URL: str = os.getenv("ASTER_BASE_URL", "https://fapi.asterdex.com")
    
    # Trading Configuration
    TRADING_SYMBOLS: List[str] = os.getenv("TRADING_SYMBOLS", "BTC-PERP,ETH-PERP").split(",")
    DEFAULT_LEVERAGE: int = int(os.getenv("DEFAULT_LEVERAGE", "5"))
    MAX_LEVERAGE: int = int(os.getenv("MAX_LEVERAGE", "10"))
    
    # Risk Management
    MAX_POSITION_SIZE_PERCENT: float = float(os.getenv("MAX_POSITION_SIZE_PERCENT", "2.0"))
    MAX_DRAWDOWN_PERCENT: float = float(os.getenv("MAX_DRAWDOWN_PERCENT", "10.0"))
    RISK_PER_TRADE_PERCENT: float = float(os.getenv("RISK_PER_TRADE_PERCENT", "1.0"))
    MIN_ACCOUNT_EQUITY: float = float(os.getenv("MIN_ACCOUNT_EQUITY", "100.0"))
    
    # Bot Configuration
    LOOP_INTERVAL_SECONDS: int = int(os.getenv("LOOP_INTERVAL_SECONDS", "300"))
    PAPER_TRADING_MODE: bool = os.getenv("PAPER_TRADING_MODE", "true").lower() == "true"
    ENABLE_STOP_LOSS: bool = os.getenv("ENABLE_STOP_LOSS", "true").lower() == "true"
    ENABLE_TAKE_PROFIT: bool = os.getenv("ENABLE_TAKE_PROFIT", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Data Configuration
    KLINE_LIMIT: int = 100  # Number of candles to fetch
    INTRADAY_INTERVAL: str = "3m"  # 3-minute intervals for intraday
    LONGTERM_INTERVAL: str = "4h"  # 4-hour intervals for long-term context
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        required_fields = [
            ("DEEPSEEK_API_KEY", cls.DEEPSEEK_API_KEY),
            ("ASTER_API_KEY", cls.ASTER_API_KEY),
            ("ASTER_API_SECRET", cls.ASTER_API_SECRET),
        ]
        
        missing_fields = [name for name, value in required_fields if not value]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True

