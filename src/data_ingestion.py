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
from binance.exceptions import BinanceAPIException, BinanceRequestException
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
        
        # 记录不可用的API（测试网限制）
        self.unavailable_apis = set()
        self._testnet_warning_shown = False
        
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
        
        # 检查是否是空响应错误
        if 'Invalid Response:' in error_text:
            return "API 返回无效响应（可能是空响应或非 JSON 格式）"
        
        # 检查是否有 code 属性（BinanceRequestException 可能没有）
        if not hasattr(error, 'code'):
            return f"API 错误: {error_text}"
        
        # 检查是否是速率限制
        if error.code in [429, 418]:
            return f"速率限制错误 (代码: {error.code})"
        
        # 检查是否是权限错误
        if error.code == -2015:
            return "API 密钥无效或权限不足"
        
        # 检查是否有 message 属性
        if hasattr(error, 'message'):
            return f"API 错误 (代码: {error.code}): {error.message}"
        else:
            return f"API 错误 (代码: {error.code}): {error_text}"
    
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
        elif hasattr(error, 'code') and error.code in [429, 418]:
            logger.info("1. 请求频率过高:")
            logger.info("   - 减少请求频率")
            logger.info("   - 增加调度间隔 (SCHEDULE_INTERVAL)")
            logger.info("   - 使用 WebSocket 代替 REST API")
        
        # API 密钥错误
        elif hasattr(error, 'code') and error.code == -2015:
            logger.info("1. API 密钥问题:")
            logger.info("   - 检查 .env 文件中的 BINANCE_API_KEY 和 BINANCE_API_SECRET")
            logger.info("   - 确保 API 密钥具有必要的权限（期货交易权限）")
            logger.info("   - 确认 API 密钥未过期")
        
        logger.info("=" * 60 + "\n")
    
    def _retry_request(self, func, max_retries: int = 3, backoff_factor: float = 2.0, allow_empty: bool = False):
        """
        带指数退避的重试机制
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            backoff_factor: 退避因子
            allow_empty: 是否允许空响应（某些测试网API可能返回空）
            
        Returns:
            函数执行结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return func()
                
            except (BinanceAPIException, BinanceRequestException) as e:
                last_error = e
                error_text = str(e)
                
                # 403 错误不重试，直接抛出
                if '403 Forbidden' in error_text or '<html>' in error_text:
                    logger.error(f"遇到 403 错误，无法访问币安 API")
                    self._suggest_solutions(e)
                    raise
                
                # 检查是否是空响应错误（常见于测试网）
                # 判断方式：错误信息包含 "Invalid Response:" 且后面是空白
                if 'Invalid Response:' in error_text:
                    # 提取 "Invalid Response:" 后面的内容
                    parts = error_text.split('Invalid Response:')
                    if len(parts) > 1:
                        response_content = parts[1].strip()
                        # 如果响应内容为空，说明是空响应
                        if not response_content:
                            # 记录API不可用
                            api_name = str(func).split()[1] if len(str(func).split()) > 1 else 'unknown'
                            self.unavailable_apis.add(api_name)
                            
                            if allow_empty:
                                # 只在第一次显示测试网限制警告
                                if self.testnet and not self._testnet_warning_shown:
                                    logger.warning("⚠️ 测试网限制：部分API（如持仓量、资金费率历史）返回空响应")
                                    logger.warning("这是测试网的正常限制，不影响核心交易功能")
                                    self._testnet_warning_shown = True
                                logger.debug(f"API {api_name} 返回空响应，返回空数据")
                                return [] if 'hist' in str(func) else {}
                            else:
                                logger.warning(f"API 返回空响应 (尝试 {attempt + 1}/{max_retries})")
                                if attempt < max_retries - 1:
                                    wait_time = backoff_factor ** attempt
                                    logger.warning(f"等待 {wait_time} 秒后重试...")
                                    time.sleep(wait_time)
                                    continue
                                # 最后一次尝试仍失败，返回空数据而不是抛异常
                                logger.warning("多次重试后仍返回空响应，返回空数据")
                                return [] if 'hist' in str(func) else {}
                
                # 速率限制错误，重试
                if hasattr(e, 'code') and e.code in [429, 418]:
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
        # 如果已知此API不可用，直接返回空数据
        if 'futures_open_interest' in self.unavailable_apis:
            logger.debug(f"跳过持仓量API（已知在测试网不可用）")
            return {}
        
        logger.debug(f"获取持仓量: {symbol}")
        
        def _get():
            return self.client.futures_open_interest(symbol=symbol)
        
        # 允许空响应（测试网此接口可能不可用）
        return self._retry_request(_get, allow_empty=True)
    
    def get_open_interest_hist(
        self, 
        symbol: str, 
        period: str = '5m', 
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取历史持仓量数据
        
        注意: 币安测试网不支持此API,会返回空响应。这是正常的测试网限制。
        
        Args:
            symbol: 交易对符号
            period: 时间周期 (如 '5m', '15m', '30m', '1h', ...)
            limit: 数据点数量
            
        Returns:
            历史持仓量数据列表
        """
        # 如果已知此API不可用，直接返回空列表
        if 'futures_open_interest_hist' in self.unavailable_apis:
            logger.debug(f"跳过历史持仓量API（已知在测试网不可用）")
            return []
        
        logger.debug(f"获取历史持仓量: {symbol} period={period} limit={limit}")
        
        def _get():
            # 使用U本位合约的持仓量历史API
            # 参考文档: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/Open-Interest-Statistics
            return self.client.futures_open_interest_hist(
                symbol=symbol,
                period=period,
                limit=limit
            )
        
        # 允许空响应（测试网此接口可能不可用）
        return self._retry_request(_get, allow_empty=True)
    
    def get_funding_rate(self, symbol: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        获取资金费率
        
        Args:
            symbol: 交易对符号
            limit: 获取数量
            
        Returns:
            资金费率历史数据列表
        """
        # 如果已知此API不可用，直接返回空列表
        if 'futures_funding_rate' in self.unavailable_apis:
            logger.debug(f"跳过资金费率API（已知在测试网不可用）")
            return []
        
        logger.debug(f"获取资金费率: {symbol} limit={limit}")
        
        def _get():
            return self.client.futures_funding_rate(
                symbol=symbol,
                limit=limit
            )
        
        # 允许空响应（测试网此接口可能不可用）
        return self._retry_request(_get, allow_empty=True)
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息（期货账户）
        
        Returns:
            账户信息字典
        """
        logger.debug("获取期货账户信息...")
        
        def _get():
            return self.client.futures_account()
        
        try:
            return self._retry_request(_get)
        except BinanceAPIException as e:
            logger.error(f"获取账户信息失败: {e}")
            logger.warning("如需使用账户功能，请在币安 API 设置中启用账户权限")
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
        获取账户数据并提取关键信息（期货账户）
        
        Returns:
            包含账户数据的字典
        """
        logger.debug("获取期货账户数据...")
        
        try:
            account_info = self.get_account_info()
            
            if not account_info:
                logger.warning("账户信息为空，返回默认值")
                return {
                    'total_wallet_balance': 0.0,
                    'total_margin_balance': 0.0,
                    'available_balance': 0.0,
                    'total_unrealized_profit': 0.0,
                    'total_maintenance_margin': 0.0,
                    'assets': [],
                    'positions': []
                }
            
            # 提取账户余额信息
            # 
            # 余额数据说明（币安期货账户）：
            # 1. total_wallet_balance（钱包余额）：
            #    - 账户的初始本金，不包含未实现盈亏
            #    - 计算公式：充值总额 - 提现总额 + 已实现盈亏
            #    - 用途：作为初始余额记录，用于计算总收益率
            # 
            # 2. total_margin_balance（保证金余额/账户总权益）：
            #    - 账户的实际总权益，包含未实现盈亏
            #    - 计算公式：total_wallet_balance + total_unrealized_profit
            #    - 用途：反映账户当前的真实价值
            # 
            # 3. available_balance（可用余额）：
            #    - 扣除已占用保证金后，可用于开新仓的余额
            #    - 计算公式：total_margin_balance - 已占用保证金 - 维持保证金
            #    - 说明：当有持仓时，此值会显著小于 total_margin_balance
            #    - 用途：用于判断是否有足够余额开新仓
            # 
            # 4. total_unrealized_profit（未实现盈亏）：
            #    - 所有持仓的未实现盈亏总和
            #    - 计算公式：sum((标记价格 - 开仓价格) * 持仓数量)
            #    - 用途：反映当前持仓的浮动盈亏
            # 
            # 5. total_maintenance_margin（维持保证金）：
            #    - 维持所有持仓所需的最低保证金
            #    - 说明：当 total_margin_balance < total_maintenance_margin 时会被强制平仓
            #    - 用途：用于监控爆仓风险
            #
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
            total_margin_balance = float(account_info.get('totalMarginBalance', 0))
            available_balance = float(account_info.get('availableBalance', 0))
            total_unrealized_profit = float(account_info.get('totalUnrealizedProfit', 0))
            total_maintenance_margin = float(account_info.get('totalMaintMargin', 0))
            
            # 提取资产列表
            assets = []
            for asset in account_info.get('assets', []):
                if float(asset.get('walletBalance', 0)) > 0:
                    assets.append({
                        'asset': asset.get('asset'),
                        'wallet_balance': float(asset.get('walletBalance', 0)),
                        'unrealized_profit': float(asset.get('unrealizedProfit', 0)),
                        'margin_balance': float(asset.get('marginBalance', 0)),
                        'available_balance': float(asset.get('availableBalance', 0))
                    })
            
            # 提取持仓列表（仅保留有持仓的）
            positions = []
            for pos in account_info.get('positions', []):
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    positions.append({
                        'symbol': pos.get('symbol'),
                        'position_amt': position_amt,
                        'entry_price': float(pos.get('entryPrice', 0)),
                        'mark_price': float(pos.get('markPrice', 0)),
                        'liquidation_price': float(pos.get('liquidationPrice', 0)),
                        'unrealized_profit': float(pos.get('unRealizedProfit', 0)),
                        'leverage': int(pos.get('leverage', 1)),
                        'position_side': pos.get('positionSide', 'BOTH')
                    })
            
            account_data = {
                'total_wallet_balance': total_wallet_balance,
                'total_margin_balance': total_margin_balance,
                'available_balance': available_balance,
                'total_unrealized_profit': total_unrealized_profit,
                'total_maintenance_margin': total_maintenance_margin,  # 添加维持保证金
                'assets': assets,
                'positions': positions
            }
            
            logger.info(f"✅ 账户信息获取成功: 余额=${total_wallet_balance:.2f}, 持仓数={len(positions)}")
            
            return account_data
            
        except Exception as e:
            logger.error(f"获取账户数据失败: {e}")
            return {
                'total_wallet_balance': 0.0,
                'total_margin_balance': 0.0,
                'available_balance': 0.0,
                'total_unrealized_profit': 0.0,
                'total_maintenance_margin': 0.0,
                'assets': [],
                'positions': []
            }


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
    
    # 获取正确的 API 凭证（testnet 或主网）
    api_key, api_secret = BinanceConfig.get_api_credentials()
    
    logger.info(f"初始化币安客户端 (testnet={BinanceConfig.TESTNET})")
    
    return BinanceDataIngestion(
        api_key=api_key,
        api_secret=api_secret,
        testnet=BinanceConfig.TESTNET,
        proxies=proxies,
        timeout=BinanceConfig.REQUEST_TIMEOUT,
        skip_connection_test=BinanceConfig.SKIP_CONNECTION_TEST
    )

