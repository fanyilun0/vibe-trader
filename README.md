# Vibe Trader

**LLM 驱动的量化交易系统 - BTC 自动化交易 AI Agent Bot**

基于 [vibe-trader-arti.md](docs/vibe-trader-arti.md) 架构文档构建的专业级加密货币自动化交易系统。

## 🌟 核心特性

- **🤖 AI 决策引擎**: 使用 Deepseek LLM 进行智能交易决策
- **📊 完整技术分析**: 集成 EMA, MACD, RSI, ATR 等多种技术指标
- **🛡️ 多层风险控制**: 严格的风险管理和安全检查机制
- **🔌 模块化架构**: 清晰的关注点分离,易于测试和扩展
- **📈 实时数据处理**: 从币安 API 获取实时市场数据
- **💾 状态持久化**: 完整的状态管理和历史记录
- **🎯 多平台支持**: 支持 Binance, Hype, Aster 和模拟交易

## 📐 系统架构

系统由四大核心模块组成:

```
┌─────────────────────────────────────────────────────────┐
│                    Vibe Trader System                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐      ┌────────────────┐             │
│  │  Data Ingestion│ ───▶ │ Data Processing│             │
│  │     Module     │      │   & Features   │             │
│  └────────────────┘      └────────────────┘             │
│         │                        │                       │
│         │                        ▼                       │
│         │              ┌────────────────┐                │
│         │              │  AI Decision   │                │
│         │              │      Core      │                │
│         │              └────────────────┘                │
│         │                        │                       │
│         │                        ▼                       │
│         │              ┌────────────────┐                │
│         │              │ Risk Management│                │
│         │              │    & Checks    │                │
│         │              └────────────────┘                │
│         │                        │                       │
│         │                        ▼                       │
│         │              ┌────────────────┐                │
│         └─────────────▶│   Execution    │                │
│                        │     Layer      │                │
│                        └────────────────┘                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 模块说明

1. **数据摄取模块** (`src/data_ingestion.py`)
   - 从币安 API 获取 K 线数据
   - 获取持仓量和资金费率
   - 获取账户信息和持仓

2. **数据处理与特征工程** (`src/data_processing.py`)
   - 计算技术指标 (EMA, MACD, RSI, ATR)
   - 数据清洗和格式化
   - 特征验证

3. **AI 决策核心** (`src/ai_decision.py`)
   - 构建结构化提示词
   - 调用 Deepseek LLM API
   - 解析和验证 JSON 决策

4. **抽象执行层** (`src/execution.py`)
   - 统一的执行接口
   - 支持多个交易平台
   - 模拟交易支持

5. **风险管理** (`src/risk_management.py`)
   - 仓位大小限制
   - 置信度阈值检查
   - 止损验证
   - 交易对白名单

6. **状态管理** (`src/state_manager.py`)
   - 持久化系统状态
   - 调用计数和交易历史
   - 性能指标记录

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- 币安账户 (用于数据获取和交易)
- Deepseek API 密钥

### 2. 安装

```bash
# 克隆仓库
git clone <repository-url>
cd vibe-trader

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

#### 3.1 创建环境变量文件

创建 `.env` 文件并配置 API 密钥:

```bash
# 币安 API 密钥
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Deepseek API 密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

⚠️ **安全提示**: 
- 切勿将 `.env` 文件提交到 Git
- 在币安账户中为 API 密钥设置 IP 白名单
- 建议先使用测试网进行测试

#### 3.2 修改配置 (可选)

配置通过 `config.py` 文件管理。如需自定义,编辑 `config.py`:

```python
# config.py

class TradingConfig:
    SYMBOLS = ['BTCUSDT']
    SCHEDULE_INTERVAL = 180  # 3分钟

class ExecutionConfig:
    PLATFORM = 'binance'
    PAPER_TRADING = True  # 建议先使用模拟交易测试

class RiskManagementConfig:
    MAX_POSITION_SIZE_PCT = 0.20  # 单笔最大仓位 20%
    MAX_OPEN_POSITIONS = 3
    MIN_CONFIDENCE = 0.75
```

查看当前配置:
```bash
python3 config.py
```

### 4. 验证环境配置

```bash
# 运行环境检查工具
python3 check_env.py
```

这将检查:
- ✅ .env 文件是否存在
- ✅ API 密钥是否正确配置
- ✅ 依赖包是否安装
- ✅ 配置文件是否有效

### 5. 运行

```bash
# 推荐: 使用 run.py 启动脚本 (自动处理路径和环境变量)
python3 run.py --once     # 仅运行一次周期 (测试)
python3 run.py            # 运行主循环 (持续交易)

# 或直接运行主程序
python3 -m src.main --once
python3 -m src.main
```

## 📊 提示词模板

系统使用结构化提示词向 LLM 提供市场数据。完整模板参见 [docs/template.md](docs/template.md)。

关键数据包括:

- **短期数据** (3分钟): 价格、EMA、MACD、RSI
- **长期数据** (4小时): EMA、ATR、成交量
- **衍生品数据**: 持仓量、资金费率
- **账户数据**: 余额、持仓、收益率

## 🛡️ 风险管理

系统实施多层风险控制:

### 1. 硬性限制
- ✅ 最大仓位大小: 20% (可配置)
- ✅ 最大持仓数量: 3 个
- ✅ 最低置信度: 0.75

### 2. 安全检查
- ✅ 交易对白名单验证
- ✅ 止损价格强制设置
- ✅ 止损价格合理性验证
- ✅ 失效条件必须设置

### 3. 价格保护
- ✅ 滑点检查
- ✅ 订单名义价值验证

⚠️ **重要**: 风险管理是最后一道防线,即使 AI 决策通过所有验证,也会进行最终安全检查。

## 🧪 模拟交易模式

系统默认启用模拟交易模式,适合:

- ✅ 测试策略
- ✅ 验证系统稳定性
- ✅ 回测历史数据
- ✅ 学习和研究

要启用实盘交易,需要:
1. 在 `config.yaml` 中设置 `execution.paper_trading: false`
2. 确保已完成充分测试
3. 设置适当的风险参数

## 📁 项目结构

```
vibe-trader/
├── config.py                # 主配置模块 ⭐
├── .env                     # 环境变量 (API 密钥)
├── env.example              # 环境变量示例
├── requirements.txt         # Python 依赖
├── README.md               # 本文件
├── run.py                  # 启动脚本 🚀
├── check_env.py            # 环境检查工具 🔍
├── .gitignore              # Git 忽略规则
├── docs/                   # 文档
│   ├── vibe-trader-arti.md # 架构蓝图
│   ├── template.md         # 提示词模板
│   ├── template-description.md
│   └── SETUP_GUIDE.md      # 设置指南
├── src/                    # 源代码
│   ├── __init__.py
│   ├── main.py            # 主程序入口
│   ├── data_ingestion.py  # 数据摄取模块
│   ├── data_processing.py # 数据处理模块
│   ├── ai_decision.py     # AI 决策核心
│   ├── execution.py       # 执行层
│   ├── risk_management.py # 风险管理
│   └── state_manager.py   # 状态管理
├── examples/               # 示例代码
│   └── example_usage.py   # 模块使用示例
├── data/                  # 数据文件 (自动创建)
│   └── state.json        # 系统状态
└── logs/                 # 日志文件 (自动创建)
    └── vibe_trader.log   # 运行日志
```

## 📖 详细文档

- [系统架构蓝图](docs/vibe-trader-arti.md) - 完整的技术架构文档
- [提示词模板](docs/template.md) - AI 使用的提示词结构
- [模板数据说明](docs/template-description.md) - 数据字段详细说明

## 🔗 相关链接

- [Binance API 文档](https://www.binance.com/en/binance-api)
- [Deepseek API 文档](https://api-docs.deepseek.com/zh-cn/)

## ⚙️ 高级配置

### 自定义配置参数

编辑 `config.py` 修改配置:

```python
# config.py

class TradingConfig:
    """交易配置"""
    SYMBOLS = ['BTCUSDT', 'ETHUSDT']  # 添加更多交易对
    SCHEDULE_INTERVAL = 300  # 改为5分钟

class RiskManagementConfig:
    """风险管理配置"""
    MAX_POSITION_SIZE_PCT = 0.15  # 降低仓位到15%
    MIN_CONFIDENCE = 0.80  # 提高置信度阈值
```

查看配置:
```bash
python3 config.py  # 查看配置摘要
```

### 自定义技术指标参数

编辑 `src/data_processing.py` 中的指标计算参数:

```python
# EMA 周期
df['ema_20'] = DataProcessor.calculate_ema(df, 20)

# MACD 参数
macd_data = DataProcessor.calculate_macd(
    df, 
    window_fast=12, 
    window_slow=26, 
    window_sign=9
)
```

### 自定义 AI 提示词

编辑 `src/ai_decision.py` 中的 `STATIC_INSTRUCTIONS`:

```python
STATIC_INSTRUCTIONS = """
你的自定义指令...
"""
```

## 🐛 故障排除

### 常见问题

#### 1. ModuleNotFoundError: No module named 'src'

**原因**: 从错误的目录运行程序

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/vibe-trader

# 使用推荐的启动方式
python3 run.py --once

# 或确保使用 -m 参数
python3 -m src.main --once
```

#### 2. 环境变量未加载

**原因**: .env 文件不存在或格式错误

**解决方案**:
```bash
# 1. 检查 .env 文件
ls -la .env

# 2. 如不存在,从示例创建
cp env.example .env

# 3. 编辑并填入真实 API 密钥
nano .env

# 4. 运行环境检查
python3 check_env.py
```

#### 3. API 连接失败

**解决方案**:
```bash
# 验证 API 密钥
python3 check_env.py

# 检查网络连接
ping api.binance.com

# 确认 IP 白名单设置 (在币安账户中)
```

#### 4. 数据处理错误

**解决方案**:
- 检查 K 线数据是否充足
- 验证技术指标计算是否正确
- 查看日志文件了解详细错误

#### 5. LLM 响应格式错误

**解决方案**:
- 检查 Deepseek API 配额
- 验证 API 密钥有效性
- 查看 LLM 原始响应日志

### 查看日志

```bash
# 实时查看日志
tail -f logs/vibe_trader.log

# 搜索错误
grep ERROR logs/vibe_trader.log

# 查看最近的决策
tail -100 logs/vibe_trader.log | grep "决策"
```

### 完整诊断

```bash
# 运行完整的环境检查
python3 check_env.py

# 这会检查:
# - .env 文件是否存在
# - API 密钥是否正确配置
# - 依赖包是否安装
# - 配置文件是否有效
# - 目录结构是否完整
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## ⚖️ 免责声明

本软件仅供学习和研究使用。加密货币交易存在高风险,可能导致资金损失。使用本软件进行实盘交易的所有风险由用户自行承担。开发者不对任何交易损失负责。

**强烈建议**:
- ✅ 先在模拟环境中充分测试
- ✅ 从小资金开始
- ✅ 设置合理的风险参数
- ✅ 持续监控系统运行

## 📄 许可证

MIT License

---

**构建于 2025 年,基于先进的 LLM 技术和量化交易理念** 🚀

