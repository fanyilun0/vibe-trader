# Vibe Trader 配置指南

## ⚠️ 重要提示：交易对符号格式

### 正确格式 ✅
Aster DEX API 使用 Binance 兼容的符号格式，**必须使用以下格式**：

```
BTCUSDT    ✅ 正确
ETHUSDT    ✅ 正确
SOLUSDT    ✅ 正确
BNBUSDT    ✅ 正确
ADAUSDT    ✅ 正确
```

### 错误格式 ❌
以下格式都是**错误的**，会导致 API 返回 400 Bad Request：

```
BTC-PERP   ❌ 错误（不要使用连字符）
BTC-USDT   ❌ 错误（不要使用连字符）
BTCUSD     ❌ 错误（必须是 USDT）
btcusdt    ❌ 错误（必须大写）
```

## 配置文件示例

### 基础配置（推荐新手）

```env
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_MODEL=deepseek-reasoner

# Aster DEX API
ASTER_API_KEY=your-key-here
ASTER_API_SECRET=your-secret-here
ASTER_API_PASSPHRASE=your-passphrase-here
ASTER_BASE_URL=https://fapi.asterdex.com

# 交易配置
TRADING_SYMBOLS=BTCUSDT
DEFAULT_LEVERAGE=3
MAX_LEVERAGE=5

# 风险管理（保守）
MAX_POSITION_SIZE_PERCENT=1.0
MAX_DRAWDOWN_PERCENT=5.0
RISK_PER_TRADE_PERCENT=0.5
MIN_ACCOUNT_EQUITY=100.0

# Bot 配置
LOOP_INTERVAL_SECONDS=300
PAPER_TRADING_MODE=true
ENABLE_STOP_LOSS=true
ENABLE_TAKE_PROFIT=true

LOG_LEVEL=INFO
```

### 进阶配置（多币种）

```env
# 交易多个币种
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT

DEFAULT_LEVERAGE=5
MAX_LEVERAGE=10

# 风险管理（进阶）
MAX_POSITION_SIZE_PERCENT=2.0
MAX_DRAWDOWN_PERCENT=10.0
RISK_PER_TRADE_PERCENT=1.0
MIN_ACCOUNT_EQUITY=500.0

LOOP_INTERVAL_SECONDS=180
```

## 常见错误及解决方案

### 错误 1: 400 Bad Request - symbol=BTC-PERP

**症状**:
```
Error fetching data for BTC-PERP: 400 Bad Request
```

**原因**: 使用了错误的交易对格式

**解决方案**:
1. 检查 `.env` 文件中的 `TRADING_SYMBOLS` 配置
2. 将 `BTC-PERP` 改为 `BTCUSDT`
3. 将 `ETH-PERP` 改为 `ETHUSDT`

**正确配置**:
```env
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
```

### 错误 2: 认证失败

**症状**:
```
Error: Aster API request failed: 401 Unauthorized
```

**原因**: API 密钥配置错误

**解决方案**:
1. 检查 `ASTER_API_KEY` 和 `ASTER_API_SECRET` 是否正确
2. 确保 API 密钥有足够的权限
3. 检查 API 密钥是否已过期

### 错误 3: 签名错误

**症状**:
```
Error: Signature for this request is not valid
```

**原因**: API 签名生成错误或时间戳不同步

**解决方案**:
1. 检查系统时间是否正确
2. 确保 `ASTER_API_SECRET` 配置正确
3. 检查网络连接是否稳定

## 验证配置

运行以下命令来验证配置是否正确：

```bash
python test_data_fetch.py
```

如果配置正确，你应该看到类似以下输出：

```
🧪 测试 Aster API 连接和数据获取
=====================================
✅ 使用 Aster DEX API 进行测试
📊 测试交易对: BTCUSDT

1️⃣  测试公开市场数据端点...
   🪙 测试交易对: BTCUSDT
      ├─ 获取 K线数据 (3m, 最近10根)...
      │  ✅ 成功获取 10 根K线
      ├─ 获取资金费率...
      │  ✅ 资金费率: 0.0001
      └─ 获取订单簿 (深度5)...
         ✅ 买单数: 5, 卖单数: 5
```

## 交易对列表

### Aster DEX 支持的主要交易对

| 交易对 | 说明 |
|--------|------|
| BTCUSDT | Bitcoin / USDT 永续合约 |
| ETHUSDT | Ethereum / USDT 永续合约 |
| BNBUSDT | BNB / USDT 永续合约 |
| SOLUSDT | Solana / USDT 永续合约 |
| ADAUSDT | Cardano / USDT 永续合约 |
| XRPUSDT | XRP / USDT 永续合约 |
| DOGEUSDT | Dogecoin / USDT 永续合约 |
| MATICUSDT | Polygon / USDT 永续合约 |
| DOTUSDT | Polkadot / USDT 永续合约 |
| AVAXUSDT | Avalanche / USDT 永续合约 |

**注意**: 具体支持的交易对以 Aster DEX 平台实际提供为准。建议先访问 https://app.asterdex.com 确认。

## 推荐配置方案

### 方案 1: 保守型（新手）
```env
TRADING_SYMBOLS=BTCUSDT
DEFAULT_LEVERAGE=3
MAX_POSITION_SIZE_PERCENT=1.0
RISK_PER_TRADE_PERCENT=0.5
PAPER_TRADING_MODE=true
```

### 方案 2: 平衡型
```env
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
DEFAULT_LEVERAGE=5
MAX_POSITION_SIZE_PERCENT=2.0
RISK_PER_TRADE_PERCENT=1.0
PAPER_TRADING_MODE=true
```

### 方案 3: 进取型（经验用户）
```env
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
DEFAULT_LEVERAGE=7
MAX_POSITION_SIZE_PERCENT=3.0
RISK_PER_TRADE_PERCENT=1.5
PAPER_TRADING_MODE=false  # ⚠️ 真实交易
```

## 安全建议

1. **始终先使用纸上交易模式**: `PAPER_TRADING_MODE=true`
2. **限制 API 权限**: 在 Aster DEX 后台限制 API 密钥的权限
3. **设置 IP 白名单**: 在 Aster DEX 后台设置 API 密钥的 IP 白名单
4. **定期更换密钥**: 建议每月更换一次 API 密钥
5. **不要分享密钥**: 永远不要将 API 密钥提交到 Git 仓库

## 相关文档

- [Aster API 完整文档](docs/aster-api-complete.md)
- [Aster API 快速参考](docs/aster-api.md)
- [快速开始指南](QUICKSTART_CN.md)

