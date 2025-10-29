"""
数据摄取模块 (Data Ingestion Module)

负责从币安 API 获取所有必需的原始市场数据和账户信息。
该模块不对数据进行任何转换或解读,只负责可靠地检索原始数据。
"""

import os
import time
import requests
from typing import Dict, List, Any, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging

logger = logging.getLogger(__name__)


class BinanceDataIngestion:
    """币安数据摄取客户端"""
    
    def __init__(
        self, 
        api_key: str, 
        api_secret: str, 
        testnet: bool = False,
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        skip_connection_test: bool = False
    ):
        """
        初始化币安客户端
        
        Args:
            api_key: API密钥
            api_secret: API私钥
            testnet: 是否使用测试网
            proxies: 代理配置字典 {'http': 'http://host:port', 'https': 'http://host:port'}
            timeout: 请求超时时间（秒）
            skip_connection_test: 是否跳过连接测试（默认False，建议仅在确认代理工作时使用）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.proxies = proxies or {}
        self.timeout = timeout
        self.skip_connection_test = skip_connection_test
        
        # 初始化币安客户端
        self.client = Client(api_key, api_secret, testnet=testnet)
        
        # 设置为期货API (默认已经是正确的，不需要修改)
        # if not testnet:
        #     self.client.FUTURES_URL = 'https://fapi.binance.com/fapi'
        
        # 设置超时
        self.client.session.timeout = timeout
        
        # 配置代理 (必须在最后设置，确保不被其他配置覆盖)
        if self.proxies:
            self.client.session.proxies = self.proxies  # 使用直接赋值而不是update
            # 隐藏敏感信息（如认证信息）
            proxy_info = {}
            for key, url in self.proxies.items():
                # 隐藏可能的用户名密码
                if '@' in url:
                    # 格式: protocol://username:password@host:port
                    parts = url.split('@')
                    proxy_info[key] = f"{parts[0].split('://')[0]}://***@{parts[1]}"
                else:
                    proxy_info[key] = url
            logger.info(f"✓ 已配置代理: {proxy_info}")
        
        logger.info(f"币安数据摄取客户端初始化完成 (testnet={testnet}, timeout={timeout}s)")
        
        # 测试连接
        if not skip_connection_test:
            self._test_connection()
        else:
            logger.warning("⚠️  已跳过连接测试")
    
    def _test_connection(self):
        """
        测试与币安 API 的连接（仅测试公开市场数据接口）
        
        尝试获取服务器时间和K线数据以验证连接是否正常
        注意：不测试需要账户权限的接口
        """
        try:
            logger.info("正在测试币安 API 连接（仅公开市场数据）...")
            
            # 测试简单的公开 API 调用
            server_time = self.client.get_server_time()
            logger.info(f"✅ 现货 API 连接成功 (服务器时间: {server_time['serverTime']})")
            
            # 测试期货 API 连接（使用公开的市场数据接口）
            try:
                logger.info("正在测试期货市场数据 API...")
                # 使用最简单的公开接口：获取K线数据
                klines = self.client.futures_klines(symbol='BTCUSDT', interval='1m', limit=1)
                if klines:
                    logger.info(f"✅ 期货市场数据 API 连接成功")
                    logger.info("📊 系统将以只读模式运行（仅获取市场数据）")
            except BinanceAPIException as e:
                if '403' in str(e) or 'Forbidden' in str(e):
                    logger.warning("⚠️  期货 API 返回 403 错误")
                    logger.warning("这可能是代理问题或 IP 被限制")
                    logger.warning("建议:")
                    logger.warning("  1. 检查代理是否正常工作 (运行: uv run python tests/test_proxy_direct.py)")
                    logger.warning("  2. 尝试更换代理服务器")
                    logger.warning("  3. 检查币安 API 的 IP 白名单设置")
                    logger.warning("  4. 或者暂时跳过连接测试，直接运行 (风险自负)")
                    raise
                else:
                    raise
            
        except BinanceAPIException as e:
            error_msg = self._parse_binance_error(e)
            logger.error(f"❌ 币安 API 连接失败: {error_msg}")
            
            # 提供解决方案建议
            self._suggest_solutions(e)
            
            raise Exception(f"无法连接到币安 API: {error_msg}")
            
        except Exception as e:
            logger.error(f"❌ 网络连接测试失败: {e}")
            logger.error("请检查网络连接和防火墙设置")
            raise
    
    def _parse_binance_error(self, error: BinanceAPIException) -> str:
        """
        解析币安 API 错误信息
        
        Args:
            error: 币安 API 异常对象
            
        Returns:
            格式化的错误信息
        """
        error_text = str(error)
        
        # 检查是否是 HTML 403 错误
        if '403 Forbidden' in error_text or '<html>' in error_text:
            return "403 Forbidden - IP 访问被拒绝"
        
        # 检查是否是速率限制
        if error.code in [429, 418]:
            return f"速率限制错误 (代码: {error.code})"
        
        # 检查是否是权限错误
        if error.code == -2015:
            return "API 密钥无效或权限不足"
        
        return f"API 错误 (代码: {error.code}): {error.message}"
    
    def _suggest_solutions(self, error: BinanceAPIException):
        """
        根据错误类型提供解决方案建议
        
        Args:
            error: 币安 API 异常对象
        """
        error_text = str(error)
        
        logger.info("\n" + "=" * 60)
        logger.info("🔧 可能的解决方案:")
        logger.info("=" * 60)
        
        # 403 错误的解决方案
        if '403 Forbidden' in error_text or '<html>' in error_text:
            logger.info("1. IP 访问限制问题:")
            logger.info("   - 您的 IP 可能被币安限制访问")
            logger.info("   - 解决方案 A: 使用代理服务器")
            logger.info("     在 .env 文件中添加:")
            logger.info("     BINANCE_PROXY_URL=http://127.0.0.1:7890")
            logger.info("     (或使用其他代理: https://..., socks5://...)")
            logger.info("")
            logger.info("   - 解决方案 B: 在币安 API 设置中添加 IP 白名单")
            logger.info("     登录币安账户 -> API 管理 -> 编辑 API -> IP 访问限制")
            logger.info("")
            logger.info("   - 解决方案 C: 使用 VPN 或更换网络环境")
            logger.info("")
            logger.info("   - 解决方案 D: 使用币安测试网进行测试")
            logger.info("     在 config.py 中设置 TESTNET = True")
        
        # 速率限制错误
        elif error.code in [429, 418]:
            logger.info("1. 请求频率过高:")
            logger.info("   - 减少请求频率")
            logger.info("   - 增加调度间隔 (SCHEDULE_INTERVAL)")
            logger.info("   - 使用 WebSocket 代替 REST API")
        
        # API 密钥错误
        elif error.code == -2015:
            logger.info("1. API 密钥问题:")
            logger.info("   - 检查 .env 文件中的 BINANCE_API_KEY 和 BINANCE_API_SECRET")
            logger.info("   - 确保 API 密钥具有必要的权限（期货交易权限）")
            logger.info("   - 确认 API 密钥未过期")
        
        logger.info("=" * 60 + "\n")
    
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
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return func()
                
            except BinanceAPIException as e:
                last_error = e
                error_text = str(e)
                
                # 403 错误不重试，直接抛出
                if '403 Forbidden' in error_text or '<html>' in error_text:
                    logger.error(f"遇到 403 错误，无法访问币安 API")
                    self._suggest_solutions(e)
                    raise
                
                # 速率限制错误，重试
                if e.code in [429, 418]:
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"遇到速率限制 (尝试 {attempt + 1}/{max_retries})，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                
                # 其他 API 错误
                logger.error(f"币安 API 错误: {self._parse_binance_error(e)}")
                raise
                
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"网络请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    logger.warning(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"网络请求失败: {e}")
                raise
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    logger.warning(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                raise
        
        # 所有重试都失败
        logger.error(f"重试 {max_retries} 次后仍然失败")
        if last_error:
            raise last_error
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
        获取账户信息（已禁用 - 需要账户权限）
        
        Returns:
            空字典（功能已禁用）
        """
        logger.warning("⚠️  get_account_info() 已被禁用 - 此功能需要账户权限")
        logger.warning("如需使用账户功能，请在币安 API 设置中启用相应权限")
        return {}
    
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
        获取账户数据并提取关键信息（已禁用 - 需要账户权限）
        
        Returns:
            包含模拟账户数据的字典（仅用于兼容性）
        """
        logger.warning("⚠️  get_account_data() 已被禁用 - 此功能需要账户权限")
        logger.info("返回模拟账户数据以保持系统运行")
        
        # 返回模拟数据以保持系统兼容性
        account_data = {
            'total_wallet_balance': 0.0,
            'total_margin_balance': 0.0,
            'available_balance': 0.0,
            'total_unrealized_profit': 0.0,
            'assets': [],
            'positions': []
        }
        
        return account_data


def create_binance_client() -> BinanceDataIngestion:
    """
    根据配置创建币安数据摄取客户端
    
    Returns:
        BinanceDataIngestion 实例
    """
    from config import BinanceConfig
    
    if not BinanceConfig.validate():
        raise ValueError("币安 API 密钥未正确配置,请检查 .env 文件")
    
    # 获取代理配置
    proxies = BinanceConfig.get_proxy_dict()
    
    return BinanceDataIngestion(
        api_key=BinanceConfig.API_KEY,
        api_secret=BinanceConfig.API_SECRET,
        testnet=BinanceConfig.TESTNET,
        proxies=proxies,
        timeout=BinanceConfig.REQUEST_TIMEOUT,
        skip_connection_test=BinanceConfig.SKIP_CONNECTION_TEST
    )

