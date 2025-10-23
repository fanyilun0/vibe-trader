# Vibe Trader - 快速入门指南

## 🚀 5 分钟快速开始

### 步骤 1: 克隆并安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/vibe-trader.git
cd vibe-trader

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 TA-Lib
# macOS:
brew install ta-lib

# Ubuntu/Debian:
# sudo apt-get install libta-lib-dev
```

### 步骤 2: 配置 API 密钥

创建 `.env` 文件：

```bash
cat > .env << EOF
# DeepSeek API (必需)
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# Aster DEX API (必需)
ASTER_API_KEY=your-aster-key-here
ASTER_API_SECRET=your-aster-secret-here

# 交易配置
TRADING_SYMBOLS=BTC-PERP,ETH-PERP
DEFAULT_LEVERAGE=3
MAX_LEVERAGE=5

# 风险控制（重要！）
MAX_POSITION_SIZE_PERCENT=1.0
MAX_DRAWDOWN_PERCENT=5.0
RISK_PER_TRADE_PERCENT=0.5

# 运行模式
PAPER_TRADING_MODE=true
LOOP_INTERVAL_SECONDS=300
EOF
```

**获取 API 密钥：**

1. **DeepSeek**: 访问 [platform.deepseek.com](https://platform.deepseek.com)，注册并创建 API Key
2. **Aster DEX**: 登录 Aster DEX，进入 账户设置 → API 管理 → 创建 API Key

### 步骤 3: 测试配置

```bash
# 运行示例脚本测试连接
python example.py
```

应该看到：
- ✓ 成功连接到 Aster API
- ✓ 获取市场数据
- ✓ 计算技术指标

### 步骤 4: 纸上交易（推荐先运行至少 1 周）

```bash
# 启动纸上交易模式
python main.py
```

观察机器人运行：
```
🤖 Initializing Vibe Trader...
✅ Initialization complete
Mode: PAPER TRADING
Symbols: BTC-PERP, ETH-PERP

🚀 VIBE TRADER STARTED
================================================================================
ITERATION #1 - 2025-10-22 14:30:00
================================================================================

📊 Step 1: Fetching market data...
✅ Fetched data for 2 symbols

🧠 Step 2: Generating trading signal with DeepSeek...
📋 Signal Generated:
  Action: LONG
  Symbol: BTC-PERP
  Confidence: 82.00%
  ...
```

### 步骤 5: 真实交易（仅在充分测试后）

```bash
# 启动真实交易（需要确认）
python main.py --live
```

## 📊 了解输出

### 信号类型

- **LONG**: 做多（买入看涨）
- **SHORT**: 做空（卖出看跌）
- **HOLD**: 无操作
- **CLOSE**: 平仓

### 置信度阈值

- **≥ 70%**: 机器人会执行交易
- **< 70%**: 机器人会拒绝交易

### 风险指标

机器人会实时显示：
- **账户权益**: 当前总资产
- **总回报**: 累计盈亏百分比
- **当前回撤**: 从峰值的下跌幅度
- **持仓数量**: 当前开仓数

## ⚙️ 关键配置解释

### 风险管理（最重要！）

```env
# 单笔交易最大仓位
MAX_POSITION_SIZE_PERCENT=1.0  # 账户的 1%

# 最大回撤限制（触发自动平仓）
MAX_DRAWDOWN_PERCENT=5.0  # 从峰值回撤 5%

# 单笔交易风险
RISK_PER_TRADE_PERCENT=0.5  # 每笔最多亏损账户的 0.5%
```

**新手推荐值**：
- `MAX_POSITION_SIZE_PERCENT=1.0`（保守）
- `MAX_DRAWDOWN_PERCENT=5.0`（安全）
- `RISK_PER_TRADE_PERCENT=0.5`（谨慎）

**进阶交易者**：
- `MAX_POSITION_SIZE_PERCENT=2.0`
- `MAX_DRAWDOWN_PERCENT=10.0`
- `RISK_PER_TRADE_PERCENT=1.0`

### 交易频率

```env
# 策略评估间隔（秒）
LOOP_INTERVAL_SECONDS=300  # 每 5 分钟评估一次
```

**建议**：
- 新手：300-600 秒（5-10 分钟）
- 进阶：180-300 秒（3-5 分钟）
- 高频：60-120 秒（1-2 分钟，费用更高）

### 杠杆设置

```env
DEFAULT_LEVERAGE=3  # 默认 3x
MAX_LEVERAGE=5      # 最大 5x
```

**警告**：杠杆放大收益也放大风险！
- 新手：1-3x
- 中级：3-5x
- 高级：5-10x（极高风险）

## 🛡️ 安全检查清单

在启动真实交易前，确保：

- [ ] 已在纸上交易模式运行至少 1 周
- [ ] 理解所有风险参数的含义
- [ ] 设置了合理的 `MAX_DRAWDOWN_PERCENT`
- [ ] 从小额资金开始（如 $100-500）
- [ ] 启用了 `ENABLE_STOP_LOSS=true`
- [ ] 监控设置完成（手机通知等）
- [ ] 有应急计划（知道如何手动平仓）

## 🆘 紧急情况处理

### 立即停止机器人

```bash
# 按 Ctrl+C
# 或在另一个终端：
pkill -f "python main.py"
```

**注意**：停止机器人不会自动平仓！

### 手动平仓所有仓位

方法 1: 使用 Aster DEX 网页界面
- 登录 Aster DEX
- 进入"仓位"页面
- 点击"一键平仓"

方法 2: 使用 Python 脚本
```python
from aster_client import AsterClient

client = AsterClient()
positions = client.get_positions()

for pos in positions:
    symbol = pos['symbol']
    size = float(pos['size'])
    side = 'SELL' if pos['side'] == 'LONG' else 'BUY'
    
    client.place_order(
        symbol=symbol,
        side=side,
        order_type='MARKET',
        size=size
    )
    print(f"Closed {symbol}")
```

## 📈 性能监控

### 查看交易历史

机器人会在内存中保存交易记录：

```python
from execution_engine import ExecutionEngine

engine = ExecutionEngine()
# 运行机器人后...
print(f"总交易次数: {len(engine.trade_history)}")
for trade in engine.trade_history[-5:]:  # 最近 5 笔
    print(trade)
```

### 导出日志（建议）

```bash
# 启动时重定向输出到文件
python main.py > logs/trading_$(date +%Y%m%d).log 2>&1 &
```

### 实时监控（推荐）

使用 `screen` 或 `tmux` 在服务器上持续运行：

```bash
# 使用 screen
screen -S vibe-trader
python main.py
# 按 Ctrl+A 然后 D 脱离会话

# 重新连接
screen -r vibe-trader
```

## 🔧 故障排查

### 问题: "Configuration error: Missing required configuration"

**解决**：检查 `.env` 文件，确保设置了：
- `DEEPSEEK_API_KEY`
- `ASTER_API_KEY`
- `ASTER_API_SECRET`

### 问题: "ModuleNotFoundError: No module named 'talib'"

**解决**：安装 TA-Lib 系统库
```bash
# macOS
brew install ta-lib
pip install ta-lib

# Ubuntu
sudo apt-get install libta-lib-dev
pip install ta-lib
```

### 问题: "Aster API request failed"

**解决**：
1. 检查 API 密钥是否正确
2. 检查网络连接
3. 验证 API 权限（需要"交易"权限）
4. 检查 Aster DEX 服务状态

### 问题: DeepSeek 返回低置信度信号

**正常**！这是风险控制的一部分。机器人在不确定时会选择 HOLD。

### 问题: 所有交易都被风险管理拒绝

**检查**：
- 是否设置了过于严格的风险参数？
- 账户权益是否低于 `MIN_ACCOUNT_EQUITY`？
- 是否已经达到最大回撤？

## 📚 下一步

1. **阅读完整文档**: `docs/USAGE.md`
2. **了解数据结构**: `docs/DATA_TEMPLATE.md`
3. **学习 API**: `docs/aster-api.md`
4. **自定义策略**: 修改 `signal_generator.py` 中的提示词

## ⚠️ 免责声明

- 加密货币交易涉及重大风险
- 机器人基于 AI，不保证盈利
- 永远不要投资超过您能承受损失的资金
- 作者不对任何损失负责

---

**祝交易顺利！记住：从小额开始，先测试，后实战！** 🚀📈

