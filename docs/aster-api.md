# Aster API 快速参考

## 官方文档
https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation

## 关键信息

### 交易对符号格式（重要！）
✅ **正确格式**: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`  
❌ **错误格式**: `BTC-PERP`, `BTC-USDT`, `BTCUSD`

### 基础 URL
```
https://fapi.asterdex.com
```

### 常用端点

#### 1. K线数据（公开）
```
GET /fapi/v1/klines
参数:
  - symbol: BTCUSDT (必需)
  - interval: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M (必需)
  - limit: 默认 500, 最大 1500
```

#### 2. 资金费率（公开）
```
GET /fapi/v1/fundingRate
参数:
  - symbol: BTCUSDT (必需)
```

#### 3. 订单簿深度（公开）
```
GET /fapi/v1/depth
参数:
  - symbol: BTCUSDT (必需)
  - limit: 默认 100, 最大 1000
```

#### 4. 账户信息（需签名）
```
GET /fapi/v2/account
参数:
  - timestamp: 毫秒时间戳 (必需)
  - signature: HMAC SHA256 签名 (必需)
头部:
  - X-MBX-APIKEY: 你的API密钥
```

#### 5. 持仓信息（需签名）
```
GET /fapi/v2/positionRisk
参数:
  - symbol: BTCUSDT (可选)
  - timestamp: 毫秒时间戳 (必需)
  - signature: HMAC SHA256 签名 (必需)
```

### 签名方式
```python
import hmac
import hashlib
import time

timestamp = str(int(time.time() * 1000))
query_string = f"symbol=BTCUSDT&timestamp={timestamp}"
signature = hmac.new(
    api_secret.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

## 完整文档
详见: [docs/aster-api-complete.md](./aster-api-complete.md)