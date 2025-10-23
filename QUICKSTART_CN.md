# 🚀 快速开始指南

## 📋 目录
1. [环境准备](#环境准备)
2. [API 配置](#api-配置)
3. [测试数据获取](#测试数据获取)
4. [运行交易机器人](#运行交易机器人)
5. [常见问题](#常见问题)

## 环境准备

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 2. 验证安装

```bash
python --version  # 应该是 Python 3.8+
```

## API 配置

### 方式 1: 使用 Mock API（无需真实 API Key，适合测试）

在 `.env` 文件中设置：
```bash
USE_MOCK_API=true
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
```

### 方式 2: 使用真实 Aster API

1. 获取 API Key：
   - 访问 https://app.asterdex.com
   - 登录并进入 API 管理
   - 创建新的 API Key 和 Secret

2. 配置环境变量（在 `.env` 文件中）：
```bash
# Aster API 配置
ASTER_API_KEY=你的API_Key
ASTER_API_SECRET=你的API_Secret
ASTER_BASE_URL=https://fapi.asterdex.com

# 交易配置（注意：使用 BTCUSDT 格式，不是 BTC-PERP）
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
DEFAULT_LEVERAGE=5

# 机器人配置
PAPER_TRADING_MODE=true
USE_MOCK_API=false  # 使用真实 API
LOOP_INTERVAL_SECONDS=300

# DeepSeek API（用于信号生成）
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

## 测试数据获取

### 🎬 快速演示（推荐）

运行演示脚本，查看一次完整的数据获取和输出：

```bash
uv run demo_data_output.py
```

这将展示：
- ✅ 账户信息
- ✅ 持仓信息
- ✅ 所有交易对的市场数据
- ✅ 技术指标（EMA、RSI、MACD、布林带等）
- ✅ 订单簿深度
- ✅ 价格和成交量统计

### 🧪 完整 API 测试

测试所有 API 端点：

```bash
# 使用 Mock API 测试
USE_MOCK_API=true uv run test_data_fetch.py

# 使用真实 API 测试
uv run test_data_fetch.py
```

测试内容：
1. ✅ 公开市场数据端点（K线、资金费率、订单簿）
2. ✅ 需要认证的账户端点（账户信息、持仓）
3. ✅ 完整数据聚合功能
4. ✅ 美化数据输出

## 运行交易机器人

### Paper Trading 模式（模拟交易）

```bash
uv run main.py
```

这将：
- 📊 每 5 分钟获取一次市场数据
- 🧠 使用 DeepSeek AI 生成交易信号
- 🛡️ 进行风险管理检查
- 📝 记录所有操作（不会真实下单）

### Live Trading 模式（真实交易）

⚠️ **警告**：这将使用真实资金进行交易！

```bash
uv run main.py --live
```

系统会要求你确认：
```
⚠️  WARNING: LIVE TRADING MODE ENABLED
You are about to run the bot in LIVE mode with real money.
This involves substantial risk of loss.

Type 'I ACCEPT THE RISK' to continue:
```

## 📊 数据输出示例

运行演示脚本后，你会看到类似这样的输出：

```
====================================================================================================
📊 市场数据总览 (Market Data Overview)
====================================================================================================

⏰ 时间信息:
   当前时间: 2025-10-23 14:06:43
   运行时长: 0 分钟
   调用次数: 1

💰 账户信息:
   账户总值: $10000.00
   可用资金: $10000.00
   总回报率: 0.00%
   夏普比率: 0.00

📈 持仓信息: 无持仓

💎 交易对数据 (2 个交易对):

────────────────────────────────────────────────────────────────────────────────
🪙 BTCUSDT
────────────────────────────────────────────────────────────────────────────────

   💵 价格信息:
      当前价格: $65000.00
      资金费率: 0.000100

   📈 短期技术指标 (3m 周期):
      EMA20: $64800.00
      EMA50: $64500.00
      RSI(7): 65.23
      RSI(14): 58.91
      MACD: 120.45
      MACD Signal: 95.30
      MACD Histogram: 25.15
      布林带上轨: $65500.00
      布林带中轨: $64800.00
      布林带下轨: $64100.00
      ATR(14): $450.00
      ADX: 25.30

   📊 长期技术指标 (4h 周期):
      EMA20: $64000.00
      EMA50: $63500.00
      RSI(14): 62.50
      MACD: 250.00
      ATR(3): $380.00
      ATR(14): $420.00

   📉 价格和成交量统计 (最近 100 根K线):
      价格范围: $63000.00 - $66000.00
      平均价格: $64500.00
      平均成交量: 1250.50
```

## 🛠️ 可用脚本

| 脚本 | 功能 | 用途 |
|------|------|------|
| `demo_data_output.py` | 数据获取演示 | 快速查看数据输出格式 |
| `test_data_fetch.py` | API 连接测试 | 测试所有 API 端点 |
| `main.py` | 交易机器人主程序 | 运行完整的交易系统 |

## 🎯 获取的数据清单

### ✅ 总体状态数据
- 运行时长（分钟）
- 当前时间戳
- 调用次数

### ✅ 市场数据（每个交易对）

#### 价格指标
- 当前价格
- 20周期 EMA
- 50周期 EMA
- 7周期 RSI
- 14周期 RSI
- MACD（含信号线和柱状图）
- 布林带（上、中、下轨）
- ATR（3周期和14周期）
- ADX（趋势强度）
- VWAP（成交量加权平均价）

#### 市场深度
- 订单簿（买单和卖单深度）
- 最佳买卖价

#### 衍生品数据
- 资金费率
- 持仓量（最新和平均）

#### 时间序列数据
- 短期（3分钟）：价格、成交量、所有技术指标
- 长期（4小时）：价格、成交量、所有技术指标

### ✅ 账户数据
- 账户总价值
- 可用余额
- 总回报率
- 夏普比率
- 持仓列表
  - 交易对
  - 方向（多/空）
  - 持仓量
  - 开仓价
  - 当前价
  - 强平价
  - 未实现盈亏
  - 杠杆倍数

## 常见问题

### Q1: 显示 404 错误怎么办？

**A**: 确保使用最新代码。之前的 API 端点路径有误，现已修复：
- ❌ 旧: `/api/v3/klines`
- ✅ 新: `/fapi/v1/klines`

### Q2: 如何切换交易对？

**A**: 在 `.env` 文件中修改：
```bash
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
```

**注意**：必须使用 `BTCUSDT` 格式，不是 `BTC-PERP`

### Q3: 如何修改数据获取间隔？

**A**: 在 `.env` 文件中设置：
```bash
LOOP_INTERVAL_SECONDS=300  # 5分钟
```

### Q4: API Key 验证失败怎么办？

**A**: 检查：
1. API Key 和 Secret 是否正确
2. API Key 是否已激活
3. API Key 权限是否足够（需要读取账户、交易权限）
4. 是否有 IP 限制

### Q5: 如何只测试数据获取，不运行交易？

**A**: 使用演示脚本：
```bash
uv run demo_data_output.py
```

或者使用 Mock API 模式测试：
```bash
USE_MOCK_API=true uv run main.py
```

### Q6: 没有 API Key 可以测试吗？

**A**: 可以！使用 Mock API 模式：
```bash
USE_MOCK_API=true uv run demo_data_output.py
```

## 📚 更多文档

- [ASTER_API_SETUP.md](./ASTER_API_SETUP.md) - Aster API 详细配置指南
- [CHANGES_SUMMARY.md](./CHANGES_SUMMARY.md) - API 修复总结
- [template-description.md](./template-description.md) - 数据模板说明
- [README.md](./README.md) - 项目总览

## 🆘 获取帮助

遇到问题？
1. 查看 [故障排查指南](./ASTER_API_SETUP.md#故障排查)
2. 运行测试脚本诊断：`uv run test_data_fetch.py`
3. 查看 [Aster API 官方文档](https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation)

## 🎉 快速开始总结

1. **演示数据输出**（无需配置）：
   ```bash
   uv run demo_data_output.py
   ```

2. **测试 API 连接**（需要配置 API Key）：
   ```bash
   uv run test_data_fetch.py
   ```

3. **运行交易机器人**（Paper Trading 模式）：
   ```bash
   uv run main.py
   ```

就这么简单！🚀

