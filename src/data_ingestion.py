"""
数据摄取模块 (Data Ingestion Module)

负责从币安 API 获取所有必需的原始市场数据和账户信息。
该模块不对数据进行任何转换或解读,只负责可靠地检索原始数据。
"""

import os
import time
from typing import Dict, List, Any, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging

logger = logging.getLogger(__name__)


class BinanceDataIngestion:
    """币安数据摄取客户端"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化币安客户端
        
        Args:
            api_key: API密钥
            api_secret: API私钥
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # 初始化币安客户端
        self.client = Client(api_key, api_secret, testnet=testnet)
        
        # 设置为期货API
        if not testnet:
            self.client.FUTURES_URL = 'https://fapi.binance.com'
        
        logger.info(f"币安数据摄取客户端初始化完成 (testnet={testnet})")
    
    def _retry_request(self, func, max_retries: int = 3, backoff_factor: float = 2.0):
        """
        带指数退避的重试机制
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            backoff_factor: 退避因子
            
        Returns:
            函数执行结果
        """
        for attempt in range(max_retries):
            try:
                return func()
            except BinanceAPIException as e:
                if e.code in [429, 418]:  # 速率限制
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"遇到速率限制,等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"请求失败: {e}, 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                raise
        
        raise Exception(f"重试 {max_retries} 次后仍然失败")
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        limit: int = 100
    ) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号 (如 'BTCUSDT')
            interval: K线时间间隔 (如 '3m', '4h')
            limit: 获取的K线数量
            
        Returns:
            K线数据列表,每个元素包含 [时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]
        """
        logger.debug(f"获取K线数据: {symbol} {interval} limit={limit}")
        
        def _get():
            return self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
        
        return self._retry_request(_get)
    
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        获取最新持仓量
        
        Args:
            symbol: 交易对符号
            
        Returns:
            持仓量数据字典
        """
        logger.debug(f"获取持仓量: {symbol}")
        
        def _get():
            return self.client.futures_open_interest(symbol=symbol)
        
        return self._retry_request(_get)
    
    def get_open_interest_hist(
        self, 
        symbol: str, 
        period: str = '5m', 
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取历史持仓量数据
        
        Args:
            symbol: 交易对符号
            period: 时间周期 (如 '5m', '15m', '30m', '1h', ...)
            limit: 数据点数量
            
        Returns:
            历史持仓量数据列表
        """
        logger.debug(f"获取历史持仓量: {symbol} period={period} limit={limit}")
        
        def _get():
            return self.client.futures_open_interest_hist(
                symbol=symbol,
                period=period,
                limit=limit
            )
        
        return self._retry_request(_get)
    
    def get_funding_rate(self, symbol: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        获取资金费率
        
        Args:
            symbol: 交易对符号
            limit: 获取数量
            
        Returns:
            资金费率历史数据列表
        """
        logger.debug(f"获取资金费率: {symbol} limit={limit}")
        
        def _get():
            return self.client.futures_funding_rate(
                symbol=symbol,
                limit=limit
            )
        
        return self._retry_request(_get)
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息字典,包含余额、持仓等
        """
        logger.debug("获取账户信息")
        
        def _get():
            return self.client.futures_account()
        
        return self._retry_request(_get)
    
    def get_all_market_data(
        self, 
        symbol: str,
        short_interval: str = '3m',
        long_interval: str = '4h',
        short_limit: int = 100,
        long_limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取单个币种的所有市场数据
        
        Args:
            symbol: 交易对符号
            short_interval: 短期时间框架
            long_interval: 长期时间框架
            short_limit: 短期K线数量
            long_limit: 长期K线数量
            
        Returns:
            包含所有市场数据的字典
        """
        logger.info(f"获取 {symbol} 的所有市场数据")
        
        data = {}
        
        # 获取短期K线数据
        data['short_term_klines'] = self.get_klines(symbol, short_interval, short_limit)
        
        # 获取长期K线数据
        data['long_term_klines'] = self.get_klines(symbol, long_interval, long_limit)
        
        # 获取持仓量
        data['open_interest'] = self.get_open_interest(symbol)
        
        # 获取历史持仓量 (用于计算平均值)
        data['open_interest_hist'] = self.get_open_interest_hist(symbol, period='5m', limit=30)
        
        # 获取资金费率
        data['funding_rate'] = self.get_funding_rate(symbol, limit=1)
        
        return data
    
    def get_account_data(self) -> Dict[str, Any]:
        """
        获取账户数据并提取关键信息
        
        Returns:
            包含账户余额和持仓的字典
        """
        logger.info("获取账户数据")
        
        account_info = self.get_account_info()
        
        # 提取关键账户信息
        account_data = {
            'total_wallet_balance': float(account_info.get('totalWalletBalance', 0)),
            'total_margin_balance': float(account_info.get('totalMarginBalance', 0)),
            'available_balance': float(account_info.get('availableBalance', 0)),
            'total_unrealized_profit': float(account_info.get('totalUnrealizedProfit', 0)),
            'assets': [],
            'positions': []
        }
        
        # 提取资产信息
        for asset in account_info.get('assets', []):
            if float(asset.get('walletBalance', 0)) > 0:
                account_data['assets'].append({
                    'asset': asset.get('asset'),
                    'wallet_balance': float(asset.get('walletBalance', 0)),
                    'available_balance': float(asset.get('availableBalance', 0)),
                })
        
        # 提取持仓信息 (仅非零持仓)
        for position in account_info.get('positions', []):
            position_amt = float(position.get('positionAmt', 0))
            if position_amt != 0:
                account_data['positions'].append({
                    'symbol': position.get('symbol'),
                    'position_amt': position_amt,
                    'entry_price': float(position.get('entryPrice', 0)),
                    'mark_price': float(position.get('markPrice', 0)),
                    'unrealized_profit': float(position.get('unRealizedProfit', 0)),
                    'leverage': int(position.get('leverage', 1)),
                    'liquidation_price': float(position.get('liquidationPrice', 0)),
                    'position_side': position.get('positionSide', 'BOTH'),
                })
        
        return account_data


def create_binance_client(config: Dict[str, Any]) -> BinanceDataIngestion:
    """
    根据配置创建币安数据摄取客户端
    
    Args:
        config: 配置字典
        
    Returns:
        BinanceDataIngestion 实例
    """
    binance_config = config.get('binance', {})
    
    # 从环境变量获取API密钥
    api_key_env = binance_config.get('api_key_env', 'BINANCE_API_KEY')
    api_secret_env = binance_config.get('api_secret_env', 'BINANCE_API_SECRET')
    
    api_key = os.getenv(api_key_env)
    api_secret = os.getenv(api_secret_env)
    
    if not api_key or not api_secret:
        raise ValueError(f"未找到币安API密钥,请设置环境变量 {api_key_env} 和 {api_secret_env}")
    
    testnet = binance_config.get('testnet', False)
    
    return BinanceDataIngestion(api_key, api_secret, testnet)

