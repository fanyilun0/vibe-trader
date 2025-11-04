"""
Vibe Trader 配置模块

从环境变量加载配置并提供给其他模块使用
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 加载环境变量
env_file = PROJECT_ROOT / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"⚠️  警告: .env 文件不存在于 {env_file}")


# ============================================
# 币安 API 配置
# ============================================
class BinanceConfig:
    """币安 API 配置"""
    
    API_KEY = os.getenv('BINANCE_API_KEY', '')
    API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    BASE_URL = 'https://fapi.binance.com'  # U本位永续合约
    TESTNET = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'  # 是否使用测试网
    
    # 测试网配置
    TESTNET_API_KEY = os.getenv('BINANCE_TESTNET_API_KEY', '')
    TESTNET_API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET', '')
    
    # 代理配置 (如果需要通过代理访问)
    # 支持完整 URL 格式: http://127.0.0.1:7890 或 socks5://127.0.0.1:1080
    PROXY_URL = os.getenv('BINANCE_PROXY_URL', '')
    
    # 是否跳过连接测试 (仅在确认代理工作且初始化测试失败时使用)
    SKIP_CONNECTION_TEST = os.getenv('BINANCE_SKIP_CONNECTION_TEST', 'false').lower() == 'true'
    
    # 超时设置
    REQUEST_TIMEOUT = int(os.getenv('BINANCE_REQUEST_TIMEOUT', '30'))
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        # 如果使用测试网，验证测试网密钥
        if cls.TESTNET:
            if not cls.TESTNET_API_KEY or not cls.TESTNET_API_SECRET:
                return False
            if cls.TESTNET_API_KEY.startswith('your_') or cls.TESTNET_API_SECRET.startswith('your_'):
                return False
            return True
        
        # 否则验证主网密钥
        if not cls.API_KEY or not cls.API_SECRET:
            return False
        if cls.API_KEY.startswith('your_') or cls.API_SECRET.startswith('your_'):
            return False
        return True
    
    @classmethod
    def get_api_credentials(cls) -> tuple:
        """获取当前使用的API凭证"""
        if cls.TESTNET:
            return cls.TESTNET_API_KEY, cls.TESTNET_API_SECRET
        return cls.API_KEY, cls.API_SECRET
    
    @classmethod
    def get_proxy_dict(cls) -> Dict[str, str]:
        """获取代理配置字典"""
        if cls.PROXY_URL:
            return {
                'http': cls.PROXY_URL,
                'https': cls.PROXY_URL
            }
        return {}


# ============================================
# Deepseek API 配置
# ============================================
class DeepseekConfig:
    """Deepseek API 配置"""
    
    API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    BASE_URL = 'https://api.deepseek.com'
    MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-reasoner')  # 默认使用 deepseek-reasoner
    MAX_TOKENS = int(os.getenv('DEEPSEEK_MAX_TOKENS', '8000'))
    TEMPERATURE = float(os.getenv('DEEPSEEK_TEMPERATURE', '0.1'))  # 默认 0.1，更确定性的输出
    TIMEOUT = int(os.getenv('DEEPSEEK_TIMEOUT', '120'))  # 请求超时时间（秒）
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        if not cls.API_KEY:
            return False
        if cls.API_KEY.startswith('your_'):
            return False
        return True


# ============================================
# 提示词模板配置
# ============================================
class PromptConfig:
    """提示词模板配置"""
    
    # 提示词模板目录
    TEMPLATE_DIR = PROJECT_ROOT / 'prompt-template'
    
    # 系统提示词文件路径（可通过环境变量覆盖）
    SYSTEM_PROMPT_FILE = os.getenv(
        'SYSTEM_PROMPT_FILE',
        str(TEMPLATE_DIR / 'nof1_system_prompt_cn.md')
    )
    
    # 用户提示词模板文件路径（可通过环境变量覆盖）
    USER_PROMPT_TEMPLATE_FILE = os.getenv(
        'USER_PROMPT_TEMPLATE_FILE',
        str(TEMPLATE_DIR / 'user_prompt_cn.md')
    )
    
    
    @classmethod
    def validate(cls) -> bool:
        """验证提示词文件是否存在"""
        system_file = Path(cls.SYSTEM_PROMPT_FILE)
        # 至少一个系统提示词文件需要存在
        if not system_file.exists() :
            return False
        
        return True
    
    @classmethod
    def get_system_prompt_path(cls) -> Path:
        """获取系统提示词文件路径（优先使用主文件，否则使用备用文件）"""
        system_file = Path(cls.SYSTEM_PROMPT_FILE)
        
        if system_file.exists():
            return system_file
        else:
            raise FileNotFoundError(f"系统提示词文件不存在: {cls.SYSTEM_PROMPT_FILE}")
    
    @classmethod
    def get_user_prompt_template_path(cls) -> Path:
        """获取用户提示词模板文件路径"""
        return Path(cls.USER_PROMPT_TEMPLATE_FILE)


# ============================================
# 交易配置
# ============================================
class TradingConfig:
    """交易配置"""
    
    # 交易对列表
    SYMBOLS: List[str] = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'BNBUSDT']
    
    # 数据采集时间框架
    SHORT_TERM_TIMEFRAME = '3m'  # 短期时间框架 (3分钟)
    LONG_TERM_TIMEFRAME = '4h'   # 长期时间框架 (4小时)
    
    # 数据窗口大小
    SHORT_TERM_LIMIT = 100  # 短期K线数量
    LONG_TERM_LIMIT = 100   # 长期K线数量
    
    # 调度间隔 (秒)
    SCHEDULE_INTERVAL = 600  # 每10分钟执行一次
    
    @classmethod
    def get_timeframes(cls) -> Dict[str, str]:
        """获取时间框架配置"""
        return {
            'short_term': cls.SHORT_TERM_TIMEFRAME,
            'long_term': cls.LONG_TERM_TIMEFRAME
        }
    
    @classmethod
    def get_data_windows(cls) -> Dict[str, int]:
        """获取数据窗口配置"""
        return {
            'short_term_limit': cls.SHORT_TERM_LIMIT,
            'long_term_limit': cls.LONG_TERM_LIMIT
        }


# ============================================
# 执行平台配置
# ============================================
class ExecutionConfig:
    """执行平台配置"""
    
    PLATFORM = os.getenv('EXECUTION_PLATFORM', 'binance')  # 可选: binance, hype, aster
    
    # 其他平台 API 配置
    HYPE_API_KEY = os.getenv('HYPE_API_KEY', '')
    HYPE_API_SECRET = os.getenv('HYPE_API_SECRET', '')
    
    ASTER_API_KEY = os.getenv('ASTER_API_KEY', '')
    ASTER_API_SECRET = os.getenv('ASTER_API_SECRET', '')


# ============================================
# 风险管理配置
# ============================================
class RiskManagementConfig:
    """风险管理配置"""
    
    # 最大单笔订单占账户价值百分比
    MAX_POSITION_SIZE_PCT = 0.20  # 20%
    
    # 最大持仓数量
    MAX_OPEN_POSITIONS = 3
    
    # 最低决策置信度阈值
    MIN_CONFIDENCE = 0.75  # 75%
    
    # 允许交易的币种白名单
    ALLOWED_SYMBOLS: List[str] = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'BNBUSDT']
    
    # 最大价格滑点百分比
    MAX_PRICE_SLIPPAGE_PCT = 0.02  # 2%
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'max_position_size_pct': cls.MAX_POSITION_SIZE_PCT,
            'max_open_positions': cls.MAX_OPEN_POSITIONS,
            'min_confidence': cls.MIN_CONFIDENCE,
            'allowed_symbols': cls.ALLOWED_SYMBOLS,
            'max_price_slippage_pct': cls.MAX_PRICE_SLIPPAGE_PCT
        }


# ============================================
# 日志配置
# ============================================
class LoggingConfig:
    """日志配置"""
    
    # 从环境变量读取日志级别，默认为INFO
    # 可设置为: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = str(PROJECT_ROOT / 'logs' / 'vibe_trader.log')
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    
    # 日志格式
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


# ============================================
# 状态持久化配置
# ============================================
class StateConfig:
    """状态持久化配置"""
    
    STATE_FILE = str(PROJECT_ROOT / 'data' / 'state.json')
    BACKUP_ENABLED = True


# ============================================
# 统一配置对象
# ============================================
class Config:
    """统一配置对象 - 提供给其他模块使用"""
    
    # 项目信息
    PROJECT_ROOT = PROJECT_ROOT
    VERSION = '0.1.1'
    
    # 各子配置
    binance = BinanceConfig
    deepseek = DeepseekConfig
    prompt = PromptConfig
    trading = TradingConfig
    execution = ExecutionConfig
    risk_management = RiskManagementConfig
    logging = LoggingConfig
    state = StateConfig
    
    @classmethod
    def validate_all(cls) -> tuple[bool, List[str]]:
        """
        验证所有配置
        
        Returns:
            (是否全部有效, 错误信息列表)
        """
        errors = []
        
        # 验证币安配置
        if not cls.binance.validate():
            errors.append("币安 API 密钥未正确配置")
        
        # 验证 Deepseek 配置
        if not cls.deepseek.validate():
            errors.append("Deepseek API 密钥未正确配置")
        
        # 验证提示词配置
        if not cls.prompt.validate():
            errors.append("提示词模板文件未找到")
        
        # 验证交易对配置
        if not cls.trading.SYMBOLS:
            errors.append("交易对列表为空")
        
        return len(errors) == 0, errors
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        转换为字典格式 (用于兼容旧代码)
        
        Returns:
            配置字典
        """
        return {
            'binance': {
                'api_key_env': 'BINANCE_API_KEY',
                'api_secret_env': 'BINANCE_API_SECRET',
                'base_url': cls.binance.BASE_URL,
                'testnet': cls.binance.TESTNET
            },
            'deepseek': {
                'api_key_env': 'DEEPSEEK_API_KEY',
                'base_url': cls.deepseek.BASE_URL,
                'model': cls.deepseek.MODEL,
                'max_tokens': cls.deepseek.MAX_TOKENS,
                'temperature': cls.deepseek.TEMPERATURE,
                'timeout': cls.deepseek.TIMEOUT
            },
            'prompt': {
                'template_dir': str(cls.prompt.TEMPLATE_DIR),
                'system_prompt_file': cls.prompt.SYSTEM_PROMPT_FILE,
                'user_prompt_template_file': cls.prompt.USER_PROMPT_TEMPLATE_FILE,
            },
            'trading': {
                'symbols': cls.trading.SYMBOLS,
                'timeframes': cls.trading.get_timeframes(),
                'data_windows': cls.trading.get_data_windows(),
                'schedule_interval': cls.trading.SCHEDULE_INTERVAL
            },
            'execution': {
                'platform': cls.execution.PLATFORM
            },
            'risk_management': cls.risk_management.to_dict(),
            'logging': {
                'level': cls.logging.LEVEL,
                'log_file': cls.logging.LOG_FILE,
                'max_bytes': cls.logging.MAX_BYTES,
                'backup_count': cls.logging.BACKUP_COUNT
            },
            'state': {
                'state_file': cls.state.STATE_FILE,
                'backup_enabled': cls.state.BACKUP_ENABLED
            }
        }
    
    @classmethod
    def print_summary(cls):
        """打印配置摘要"""
        print("\n" + "=" * 60)
        print("Vibe Trader 配置摘要")
        print("=" * 60)
        
        print(f"\n📦 项目版本: {cls.VERSION}")
        print(f"📁 项目根目录: {cls.PROJECT_ROOT}")
        
        print(f"\n💱 交易配置:")
        print(f"  - 交易对: {', '.join(cls.trading.SYMBOLS)}")
        print(f"  - 短期时间框架: {cls.trading.SHORT_TERM_TIMEFRAME}")
        print(f"  - 长期时间框架: {cls.trading.LONG_TERM_TIMEFRAME}")
        print(f"  - 调度间隔: {cls.trading.SCHEDULE_INTERVAL} 秒")
        
        print(f"\n🔐 API 配置:")
        print(f"  - 币安 API: {'✓ 已配置' if cls.binance.validate() else '✗ 未配置'}")
        print(f"  - 币安测试网: {'✓ 已启用' if cls.binance.TESTNET else '✗ 未启用'}")
        print(f"  - Deepseek API: {'✓ 已配置' if cls.deepseek.validate() else '✗ 未配置'}")
        
        print(f"\n📝 提示词配置:")
        print(f"  - 模板目录: {cls.prompt.TEMPLATE_DIR}")
        print(f"  - 系统提示词: {'✓ 已配置' if cls.prompt.validate() else '✗ 未找到'}")
        try:
            system_prompt_path = cls.prompt.get_system_prompt_path()
            print(f"  - 使用文件: {system_prompt_path.name}")
        except FileNotFoundError:
            print(f"  - 使用文件: 未找到")
        
        print(f"\n🎯 执行配置:")
        print(f"  - 平台: {cls.execution.PLATFORM}")
        if cls.execution.PLATFORM == 'binance':
            print(f"  - 模式: {'测试网 (模拟交易)' if cls.binance.TESTNET else '主网 (实盘交易!)'}")
        
        print(f"\n🛡️ 风险管理:")
        print(f"  - 最大仓位: {cls.risk_management.MAX_POSITION_SIZE_PCT * 100}%")
        print(f"  - 最大持仓数: {cls.risk_management.MAX_OPEN_POSITIONS}")
        print(f"  - 最低置信度: {cls.risk_management.MIN_CONFIDENCE * 100}%")
        print(f"  - 允许交易: {', '.join(cls.risk_management.ALLOWED_SYMBOLS)}")
        
        print(f"\n📝 日志配置:")
        print(f"  - 日志级别: {cls.logging.LEVEL}")
        print(f"  - 日志文件: {cls.logging.LOG_FILE}")
        
        print("\n" + "=" * 60 + "\n")


# ============================================
# 快捷访问
# ============================================

# 创建全局配置实例
config = Config()

# 导出常用配置 (方便其他模块导入)
BINANCE_API_KEY = BinanceConfig.API_KEY
BINANCE_API_SECRET = BinanceConfig.API_SECRET
DEEPSEEK_API_KEY = DeepseekConfig.API_KEY

TRADING_SYMBOLS = TradingConfig.SYMBOLS
SCHEDULE_INTERVAL = TradingConfig.SCHEDULE_INTERVAL

MAX_POSITION_SIZE_PCT = RiskManagementConfig.MAX_POSITION_SIZE_PCT
MIN_CONFIDENCE = RiskManagementConfig.MIN_CONFIDENCE


# ============================================
# 初始化检查
# ============================================

def check_config():
    """检查配置有效性"""
    is_valid, errors = Config.validate_all()
    
    if not is_valid:
        print("\n⚠️  配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        print("\n请检查 .env 文件配置")
        return False
    
    return True


# 如果直接运行此文件,打印配置摘要
if __name__ == '__main__':
    Config.print_summary()
    
    # 验证配置
    if check_config():
        print("✅ 配置验证通过!\n")
    else:
        print("\n❌ 配置验证失败!\n")

