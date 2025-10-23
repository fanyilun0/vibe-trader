# Vibe Trader 使用指南

这份指南将帮助您快速开始使用 Vibe Trader 自动交易机器人。

## 目录

1. [快速开始](#快速开始)
2. [配置说明](#配置说明)
3. [运行机器人](#运行机器人)
4. [理解输出](#理解输出)
5. [风险管理](#风险管理)
6. [常见问题](#常见问题)

## 快速开始

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/yourusername/vibe-trader.git
cd vibe-trader

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 TA-Lib (技术分析库)
# macOS:
brew install ta-lib

# Ubuntu/Debian:
sudo apt-get install libta-lib-dev

# Windows: 下载预编译包
# https://github.com/mrjbq7/ta-lib#windows
```

### 2. 配置环境变量

复制 `.env.example` 文件并填入您的 API 密钥：

```bash
cp .env.example .env
nano .env
```

必须配置的项：
- `DEEPSEEK_API_KEY`: 您的 DeepSeek API 密钥
- `ASTER_API_KEY`: Aster DEX API Key
- `ASTER_API_SECRET`: Aster DEX API Secret

### 3. 测试运行（纸上交易模式）

```bash
# 默认以纸上交易模式运行
python main.py
```

## 配置说明

### DeepSeek 配置

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-reasoner
```

- **DEEPSEEK_API_KEY**: 从 [DeepSeek Platform](https://platform.deepseek.com) 获取
- **DEEPSEEK_MODEL**: 使用 `deepseek-reasoner` 以获得最佳分析能力

### Aster DEX 配置

```env
ASTER_API_KEY=your_api_key
ASTER_API_SECRET=your_api_secret
ASTER_API_PASSPHRASE=your_passphrase  # 可选
ASTER_BASE_URL=https://fapi.asterdex.com
```

从 Aster DEX 平台获取 API 凭证：
1. 登录 Aster DEX
2. 进入账户设置 → API 管理
3. 创建新的 API Key
4. 确保勾选"交易"权限

### 交易配置

```env
# 交易的币种（逗号分隔）
TRADING_SYMBOLS=BTC-PERP,ETH-PERP,SOL-PERP

# 默认和最大杠杆
DEFAULT_LEVERAGE=5
MAX_LEVERAGE=10
```

### 风险管理配置

这些是最重要的安全参数：

```env
# 单笔交易最大仓位（占账户权益百分比）
MAX_POSITION_SIZE_PERCENT=2.0

# 最大回撤百分比（触发后自动平仓所有仓位）
MAX_DRAWDOWN_PERCENT=10.0

# 单笔交易风险（占账户权益百分比）
RISK_PER_TRADE_PERCENT=1.0

# 最小账户权益（低于此值停止交易）
MIN_ACCOUNT_EQUITY=100.0
```

**强烈建议**：
- 新手使用 `MAX_POSITION_SIZE_PERCENT=1.0`
- 设置 `MAX_DRAWDOWN_PERCENT=5.0` 作为保护
- 从 `RISK_PER_TRADE_PERCENT=0.5` 开始

### 机器人运行配置

```env
# 策略评估间隔（秒）
LOOP_INTERVAL_SECONDS=300

# 纸上交易模式（true=模拟，false=真实交易）
PAPER_TRADING_MODE=true

# 启用止损和止盈
ENABLE_STOP_LOSS=true
ENABLE_TAKE_PROFIT=true
```

## 运行机器人

### 纸上交易模式（推荐）

```bash
# 默认模式，不会执行真实交易
python main.py
```

这个模式下：
- ✅ 获取真实市场数据
- ✅ 调用 DeepSeek 生成信号
- ✅ 执行所有分析和风险检查
- ❌ **不会**执行真实交易
- 📊 在控制台显示模拟交易信息

### 真实交易模式（谨慎使用）

```bash
# 使用 --live 标志启动真实交易
python main.py --live
```

系统会要求您确认：
```
⚠️  WARNING: LIVE TRADING MODE ENABLED
You are about to run the bot in LIVE mode with real money.
Type 'I ACCEPT THE RISK' to continue:
```

**警告**：只有在您：
1. 已经在纸上交易模式下充分测试
2. 完全理解风险管理参数
3. 准备承担可能的损失

### 停止机器人

按 `Ctrl+C` 优雅地停止机器人。系统会：
1. 完成当前操作
2. 显示最终统计数据
3. 安全退出

**注意**：停止机器人**不会**自动平仓。现有仓位将保持开启状态。

## 理解输出

### 迭代周期

每个交易周期包含 5 个步骤：

```
================================================================================
ITERATION #1 - 2025-10-22 10:30:00
================================================================================

📊 Step 1: Fetching market data...
✅ Fetched data for 3 symbols

🧠 Step 2: Generating trading signal with DeepSeek...
📋 Signal Generated:
  Action: LONG
  Symbol: BTC-PERP
  Confidence: 85.00%
  Entry: 67500.00
  Stop Loss: 66800.00
  Take Profit: 68550.00

🛡️  Step 3: Risk management validation...
✅ Trade approved: LONG BTC-PERP

⚡ Step 4: Executing trade...
[PAPER] Closing LONG position: ...
✅ Execution successful

👀 Step 5: Monitoring positions...
RISK MONITORING
Account Equity: $10000.00
Total Return: +2.50%
Current Drawdown: 0.50%
Open Positions: 1
```

### 信号解读

- **LONG**: 做多（买入）
- **SHORT**: 做空（卖出）
- **HOLD**: 保持当前状态，不操作
- **CLOSE**: 平仓指定币种的所有仓位

### 置信度

DeepSeek 为每个信号提供置信度（0.0-1.0）：
- **> 0.7**: 高置信度，可以交易
- **0.5-0.7**: 中等置信度，机器人会拒绝
- **< 0.5**: 低置信度，机器人会拒绝

## 风险管理

### 自动风险控制

机器人有多层自动风险控制：

#### 1. 仓位大小控制
根据账户权益和止损距离自动计算仓位大小：
```
仓位名义价值 = (账户权益 × 风险百分比) / 价格风险百分比
```

#### 2. 最大回撤保护
当账户权益从峰值回撤超过设定百分比时：
- 🚨 **立即平仓所有仓位**
- 🛑 **停止接受新交易**

#### 3. 止损强制执行
- 所有 LONG/SHORT 信号必须包含止损价
- 机器人会拒绝没有止损的交易
- 自动在交易所设置止损单

#### 4. 盈亏比检查
- 最小盈亏比要求：1.5:1
- 即：潜在盈利必须至少是风险的 1.5 倍

#### 5. 仓位集中度限制
- 防止过多资金同时暴露在市场中
- 最大总仓位：账户权益的 10%（2% × 5个仓位）

### 手动风险控制

您应该：
1. **定期监控**：检查机器人输出和账户状态
2. **设置警报**：在手机上设置推送通知
3. **准备干预**：了解如何手动平仓
4. **记录表现**：追踪盈亏和策略有效性

## 常见问题

### Q: 机器人需要一直运行吗？
**A**: 是的，机器人需要持续运行以监控市场和管理仓位。建议使用云服务器（如 AWS、Azure）托管。

### Q: 可以同时运行多个实例吗？
**A**: 不建议。多个实例可能会产生冲突的交易信号，导致意外的仓位。

### Q: DeepSeek API 费用是多少？
**A**: 
- `deepseek-reasoner`: 输入 $0.55/M tokens, 输出 $2.19/M tokens
- 每次信号生成约 2000-5000 tokens
- 5 分钟间隔运行，每天约 $1-3

### Q: 如何处理网络错误？
**A**: 机器人内置了错误处理：
- 单次错误：记录日志，继续下一轮
- DeepSeek API 失败：返回 HOLD 信号
- Aster API 失败：跳过当前迭代

### Q: 资金费率如何影响策略？
**A**: 
- 数据聚合器会获取资金费率
- DeepSeek 会在分析中考虑资金费率
- 高额负资金费率可能导致机器人避免做多

### Q: 可以自定义 DeepSeek 提示词吗？
**A**: 可以！编辑 `signal_generator.py` 中的 `_get_trading_instructions()` 方法来调整策略指令。

### Q: 如何回测策略？
**A**: LLM 机器人的回测很困难，因为：
- LLM 输出不是完全确定的
- 历史重放不等于实时分析
  
建议使用**前向测试**：在纸上交易模式下运行数周，记录表现。

### Q: 支持哪些技术指标？
**A**: 当前支持：
- EMA (20, 50)
- RSI (7, 14)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2σ)
- ATR (3, 14)
- VWAP
- ADX (14)

可以在 `indicators.py` 中添加更多指标。

### Q: 如何优化性能？
**A**: 
1. 调整 `LOOP_INTERVAL_SECONDS` (更长=更少 API 调用)
2. 减少 `TRADING_SYMBOLS` (关注更少币种)
3. 调整 `KLINE_LIMIT` (更少历史数据)
4. 使用本地缓存（需要自行实现）

## 支持与社区

- **问题反馈**: 在 GitHub Issues 中报告
- **功能建议**: 在 GitHub Discussions 中讨论
- **安全问题**: 私密发送到项目维护者邮箱

## 免责声明

此软件按"原样"提供，不提供任何形式的保证。作者不对使用此机器人产生的任何损失负责。加密货币交易涉及重大风险，请谨慎操作。

---

**祝交易愉快！记得先用纸上交易模式测试！** 📈🤖

