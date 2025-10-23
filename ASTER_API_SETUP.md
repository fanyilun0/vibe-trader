# Aster API 配置和测试指南

## 📝 概述

本文档说明如何配置和测试 Aster DEX API 连接，以及如何获取所需的交易数据。

## 🔧 API 端点修复说明

根据 [Aster API 官方文档](https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation)，我们已经修复了以下端点：

### 修复的端点路径

| 功能 | 原路径 (错误) | 新路径 (正确) |
|------|--------------|--------------|
| K线数据 | `/api/v3/klines` | `/fapi/v1/klines` |
| 账户信息 | `/api/v3/accounts` | `/fapi/v2/account` |
| 账户余额 | `/api/v3/accounts` | `/fapi/v2/balance` |
| 持仓信息 | `/api/v3/positions` | `/fapi/v2/positionRisk` |
| 资金费率 | `/api/v3/fundingRate` | `/fapi/v1/fundingRate` |
| 订单簿 | `/api/v3/depth` | `/fapi/v1/depth` |
| 24小时ticker | `/api/v3/ticker` | `/fapi/v1/ticker/24hr` |
| 下单 | `/api/v3/orders` | `/fapi/v1/order` |
| 取消订单 | `/api/v3/orders/{id}` | `/fapi/v1/order` |
| 查询订单 | `/api/v3/openOrders` | `/fapi/v1/openOrders` |
| 设置杠杆 | `/api/v3/leverage` | `/fapi/v1/leverage` |
| 设置保证金 | `/api/v3/marginType` | `/fapi/v1/marginType` |

### 签名方式修复

Aster API 使用 Binance 风格的签名方式：

1. **请求头格式**：
   - `X-MBX-APIKEY`: API Key
   - 不需要 `API-SIGN`、`API-TIMESTAMP` 等自定义头部

2. **签名方法**：
   - 将所有参数按字母序排列
   - 添加 `timestamp` 参数
   - 使用 HMAC-SHA256 生成签名
   - 将签名作为 `signature` 参数添加到查询字符串

3. **交易对格式**：
   - 使用 `BTCUSDT` 而不是 `BTC-PERP`
   - 使用 `ETHUSDT` 而不是 `ETH-PERP`

## 🚀 快速开始

### 1. 获取 API 密钥

1. 访问 [Aster DEX](https://app.asterdex.com)
2. 登录你的账户
3. 进入 API 管理页面
4. 创建新的 API Key 和 Secret
5. **重要**：妥善保管你的 API Secret，不要泄露给他人

### 2. 配置环境变量

创建或编辑 `.env` 文件：

```bash
# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Aster DEX API Configuration
ASTER_API_KEY=your_aster_api_key_here
ASTER_API_SECRET=your_aster_api_secret_here
ASTER_BASE_URL=https://fapi.asterdex.com

# Trading Configuration
# 注意：使用 BTCUSDT 格式，不是 BTC-PERP
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
DEFAULT_LEVERAGE=5

# Bot Configuration
PAPER_TRADING_MODE=true
USE_MOCK_API=false  # 设置为 false 使用真实 API
LOOP_INTERVAL_SECONDS=300
```

### 3. 测试 API 连接

#### 方式 1: 使用 Mock API（不需要真实 API Key）

```bash
# 使用模拟数据测试
USE_MOCK_API=true uv run test_data_fetch.py
```

#### 方式 2: 使用真实 API

```bash
# 确保 .env 文件中设置了正确的 API Key 和 Secret
# 且 USE_MOCK_API=false
uv run test_data_fetch.py
```

### 4. 运行交易机器人

```bash
# Paper Trading 模式（模拟交易，不会真实下单）
uv run main.py

# Live Trading 模式（真实交易，需要确认）
uv run main.py --live
```

## 📊 可获取的数据

根据 `template-description.md` 的要求，系统会获取以下数据：

### 1. 总体状态数据
- ✅ `minutes_trading`: 交易开始至今的总分钟数
- ✅ `current_timestamp`: 当前时间戳
- ✅ `invocation_count`: 程序调用次数

### 2. 各币种市场数据

#### 当前状态指标
- ✅ `current_price`: 最新中间价
- ✅ `current_ema20`: 20周期 EMA
- ✅ `current_macd`: MACD 指标值
- ✅ `current_rsi_7_period`: 7周期 RSI

#### 衍生品市场数据
- ✅ `latest_open_interest`: 最新持仓量
- ✅ `average_open_interest`: 平均持仓量
- ✅ `funding_rate`: 资金费率

#### 短期（Intraday）时间序列数据
- ✅ `mid_prices_list`: 中间价序列
- ✅ `ema20_list`: 20周期 EMA 序列
- ✅ `macd_list`: MACD 指标序列
- ✅ `rsi_7_period_list`: 7周期 RSI 序列
- ✅ `rsi_14_period_list`: 14周期 RSI 序列

#### 长期（4小时）时间序列数据
- ✅ `long_term_ema20` vs. `long_term_ema50`
- ✅ `long_term_atr3` vs. `long_term_atr14`
- ✅ `long_term_current_volume` vs. `long_term_average_volume`
- ✅ `long_term_macd_list`
- ✅ `long_term_rsi_14_period_list`

### 3. 账户信息与表现
- ✅ `total_return_percent`: 总回报率
- ✅ `available_cash`: 可用现金
- ✅ `account_value`: 账户总价值
- ✅ `sharpe_ratio`: 夏普比率
- ✅ `list_of_position_dictionaries`: 持仓信息列表
  - symbol: 交易对符号
  - quantity: 持仓数量
  - entry_price: 开仓价格
  - current_price: 当前价格
  - liquidation_price: 强平价格
  - unrealized_pnl: 未实现盈亏
  - leverage: 杠杆倍数

## 🎨 数据输出示例

运行测试脚本后，会在控制台看到美化的数据输出：

```
====================================================================================================
📊 市场数据总览 (Market Data Overview)
====================================================================================================

⏰ 时间信息:
   当前时间: 2025-10-23 14:03:48
   运行时长: 0 分钟
   调用次数: 1

💰 账户信息:
   账户总值: $10000.00
   可用资金: $10000.00
   总回报率: 0.00%
   夏普比率: 0.00

📈 持仓信息: 无持仓

💎 交易对数据 (2 个交易对):

────────────────────────────────────────────────────────────────────────────────────
🪙 BTCUSDT
────────────────────────────────────────────────────────────────────────────────────

   💵 价格信息:
      当前价格: $65000.00
      资金费率: 0.000100

   📈 短期技术指标 (3m 周期):
      EMA20: $64800.00
      EMA50: $64500.00
      RSI(7): 65.23
      RSI(14): 58.91
      MACD: 120.45
      ...

   📊 长期技术指标 (4h 周期):
      EMA20: $64000.00
      EMA50: $63500.00
      ...
```

## ⚠️ 注意事项

1. **API 限速**：Aster API 有请求频率限制，请不要过于频繁地调用
2. **交易对格式**：必须使用 `BTCUSDT` 格式，不要使用 `BTC-PERP`
3. **纸上交易模式**：建议先在 Paper Trading 模式下测试，确保一切正常后再开启真实交易
4. **API 权限**：确保 API Key 有足够的权限（读取账户、交易等）
5. **资金安全**：
   - 不要在代码中硬编码 API Key
   - 使用环境变量管理敏感信息
   - 定期轮换 API Key
   - 设置 IP 白名单（如果 Aster 支持）

## 🔍 故障排查

### 问题 1: 404 错误

**症状**: `404 Client Error: Not Found for url: https://fapi.asterdex.com/api/v3/...`

**解决方案**: 
- 已修复：端点路径已更新为正确的 `/fapi/v1/` 和 `/fapi/v2/` 前缀
- 检查你的代码是否使用了最新版本的 `aster_client.py`

### 问题 2: 认证失败

**症状**: `401 Unauthorized` 或签名错误

**解决方案**:
1. 检查 API Key 和 Secret 是否正确
2. 确保没有额外的空格或换行符
3. 验证 API Key 是否已激活且未过期
4. 检查 API Key 权限设置

### 问题 3: 交易对不存在

**症状**: 无法获取 `BTC-PERP` 的数据

**解决方案**:
- 使用 `BTCUSDT` 而不是 `BTC-PERP`
- 在 `.env` 文件中更新 `TRADING_SYMBOLS=BTCUSDT,ETHUSDT`

### 问题 4: 数据为空

**症状**: 获取的数据为空或 None

**解决方案**:
1. 检查网络连接
2. 使用 Mock API 模式测试代码逻辑：`USE_MOCK_API=true uv run test_data_fetch.py`
3. 查看 Aster API 状态页面，确认服务正常

## 📚 相关资源

- [Aster API 官方文档](https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation)
- [Aster GitHub API 文档](https://github.com/asterdex/api-docs)
- [项目 README](./README.md)
- [快速开始指南](./QUICKSTART.md)

## 🆘 获取帮助

如果遇到问题：
1. 检查本文档的故障排查部分
2. 查看 Aster 官方文档
3. 在项目 Issues 中搜索类似问题
4. 提交新的 Issue 并附上详细的错误信息

