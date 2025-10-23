# Aster DEX Perpetual API 完整文档

> **官方文档**: https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation

## 基本信息

### 基础 URL
```
https://fapi.asterdex.com
```

### 通用规则
- 所有端点返回 JSON 格式数据
- 数据按升序返回：最早的在前，最新的在后
- 所有时间和时间戳字段以**毫秒**表示
- HTTP 状态码：
  - `200` - 成功
  - `4XX` - 客户端错误
  - `429` - 请求频率限制
  - `5XX` - 服务器错误

## 认证

### API 密钥
- 通过 `X-MBX-APIKEY` 请求头传递
- API 密钥和密钥区分大小写
- 需要妥善保管，避免泄露

### 签名机制 (TRADE 和 USER_DATA 端点)

签名使用 `HMAC SHA256` 算法生成：

```python
import hmac
import hashlib
import time

# 1. 构建查询字符串
timestamp = str(int(time.time() * 1000))
query_string = f"symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=1&price=50000&timestamp={timestamp}"

# 2. 生成签名
signature = hmac.new(
    api_secret.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# 3. 将签名添加到查询字符串
final_query = f"{query_string}&signature={signature}"
```

## 公开端点 (无需认证)

### 1. 获取交易所信息
```
GET /fapi/v1/exchangeInfo
```

**响应示例**:
```json
{
  "symbols": [
    {
      "symbol": "BTCUSDT",
      "pair": "BTCUSDT",
      "contractType": "PERPETUAL",
      "baseAsset": "BTC",
      "quoteAsset": "USDT",
      "status": "TRADING"
    }
  ]
}
```

### 2. 获取 K线数据 (蜡烛图)
```
GET /fapi/v1/klines
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号，如 `BTCUSDT` |
| interval | STRING | YES | K线时间间隔 |
| startTime | LONG | NO | 起始时间戳（毫秒） |
| endTime | LONG | NO | 结束时间戳（毫秒） |
| limit | INT | NO | 返回数量，默认 500，最大 1500 |

**interval 可选值**:
- `1m`, `3m`, `5m`, `15m`, `30m` - 分钟级别
- `1h`, `2h`, `4h`, `6h`, `8h`, `12h` - 小时级别
- `1d`, `3d` - 天级别
- `1w` - 周级别
- `1M` - 月级别

**响应格式**:
```json
[
  [
    1499040000000,      // 开盘时间
    "0.01634000",       // 开盘价
    "0.80000000",       // 最高价
    "0.01575800",       // 最低价
    "0.01577100",       // 收盘价
    "148976.11427815",  // 成交量
    1499644799999,      // 收盘时间
    "2434.19055334",    // 成交额
    308,                // 成交笔数
    "1756.87402397",    // 主动买入成交量
    "28.46694368",      // 主动买入成交额
    "0"                 // 忽略
  ]
]
```

### 3. 获取 24小时价格变化
```
GET /fapi/v1/ticker/24hr
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | NO | 交易对符号（不传则返回所有） |

### 4. 获取订单簿深度
```
GET /fapi/v1/depth
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号 |
| limit | INT | NO | 深度档位，默认 100，最大 1000 |

**响应示例**:
```json
{
  "lastUpdateId": 1027024,
  "bids": [
    ["4.00000000", "431.00000000"]  // [价格, 数量]
  ],
  "asks": [
    ["4.00000200", "12.00000000"]
  ]
}
```

### 5. 获取资金费率
```
GET /fapi/v1/fundingRate
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号 |
| startTime | LONG | NO | 起始时间 |
| endTime | LONG | NO | 结束时间 |
| limit | INT | NO | 默认 100，最大 1000 |

**响应示例**:
```json
[
  {
    "symbol": "BTCUSDT",
    "fundingRate": "0.00010000",
    "fundingTime": 1570608000000
  }
]
```

## 私有端点 (需要签名)

### 1. 下单
```
POST /fapi/v1/order
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号 |
| side | ENUM | YES | `BUY` 或 `SELL` |
| type | ENUM | YES | `LIMIT`, `MARKET`, `STOP`, `TAKE_PROFIT` |
| quantity | DECIMAL | YES | 下单数量 |
| price | DECIMAL | NO | 价格（LIMIT 订单必需） |
| timeInForce | ENUM | NO | `GTC`, `IOC`, `FOK` |
| positionSide | ENUM | NO | `BOTH`, `LONG`, `SHORT` |
| timestamp | LONG | YES | 时间戳（毫秒） |
| signature | STRING | YES | 签名 |

### 2. 撤销订单
```
DELETE /fapi/v1/order
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号 |
| orderId | LONG | NO | 订单 ID |
| origClientOrderId | STRING | NO | 客户端订单 ID |
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

### 3. 查询未成交订单
```
GET /fapi/v1/openOrders
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | NO | 交易对符号 |
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

### 4. 查询账户余额
```
GET /fapi/v2/balance
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

### 5. 查询账户信息
```
GET /fapi/v2/account
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

**响应示例**:
```json
{
  "totalWalletBalance": "10000.00000000",
  "availableBalance": "9500.00000000",
  "totalUnrealizedProfit": "0.00000000",
  "positions": [
    {
      "symbol": "BTCUSDT",
      "positionAmt": "0.001",
      "entryPrice": "50000.0",
      "markPrice": "51000.0",
      "unRealizedProfit": "1.0",
      "liquidationPrice": "45000.0",
      "leverage": "10",
      "notional": "51.0"
    }
  ]
}
```

### 6. 查询持仓信息
```
GET /fapi/v2/positionRisk
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | NO | 交易对符号 |
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

### 7. 调整杠杆倍数
```
POST /fapi/v1/leverage
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号 |
| leverage | INT | YES | 杠杆倍数 1-100 |
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

### 8. 调整保证金模式
```
POST /fapi/v1/marginType
```

**参数**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| symbol | STRING | YES | 交易对符号 |
| marginType | ENUM | YES | `ISOLATED` 或 `CROSSED` |
| timestamp | LONG | YES | 时间戳 |
| signature | STRING | YES | 签名 |

## 交易对符号格式

### 标准格式
- **正确**: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`
- **错误**: ~~`BTC-USDT`~~, ~~`BTC-PERP`~~, ~~`BTCUSD`~~

### 常用交易对
```
BTCUSDT   - Bitcoin / USDT 永续合约
ETHUSDT   - Ethereum / USDT 永续合约
BNBUSDT   - BNB / USDT 永续合约
SOLUSDT   - Solana / USDT 永续合约
ADAUSDT   - Cardano / USDT 永续合约
DOGEUSDT  - Dogecoin / USDT 永续合约
XRPUSDT   - XRP / USDT 永续合约
```

## 错误代码

| 错误代码 | 说明 |
|---------|------|
| -1000 | 未知错误 |
| -1001 | 服务器断开连接 |
| -1002 | 未授权 |
| -1003 | 请求过多 |
| -1021 | 时间戳超出范围 |
| -1022 | 签名无效 |
| -2010 | 新订单被拒绝 |
| -2011 | 撤销订单被拒绝 |

## 速率限制

- 使用权重系统：每个端点有不同的权重
- 超过限制会返回 HTTP 429
- 建议使用 WebSocket 流来减少 HTTP 请求

## Python 示例代码

### 获取 K线数据
```python
import requests

url = "https://fapi.asterdex.com/fapi/v1/klines"
params = {
    "symbol": "BTCUSDT",
    "interval": "3m",
    "limit": 100
}

response = requests.get(url, params=params)
klines = response.json()

# 解析 K线数据
for kline in klines:
    open_time = kline[0]
    open_price = float(kline[1])
    high = float(kline[2])
    low = float(kline[3])
    close = float(kline[4])
    volume = float(kline[5])
    print(f"Time: {open_time}, Close: {close}, Volume: {volume}")
```

### 下单示例
```python
import hmac
import hashlib
import time
import requests

api_key = "your_api_key"
api_secret = "your_api_secret"
base_url = "https://fapi.asterdex.com"

# 构建参数
timestamp = str(int(time.time() * 1000))
params = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "quantity": "0.001",
    "price": "50000",
    "timeInForce": "GTC",
    "timestamp": timestamp
}

# 生成查询字符串
query_string = "&".join([f"{k}={v}" for k, v in params.items()])

# 生成签名
signature = hmac.new(
    api_secret.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# 添加签名
query_string_with_sig = f"{query_string}&signature={signature}"

# 发送请求
headers = {
    'X-MBX-APIKEY': api_key,
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.post(
    f"{base_url}/fapi/v1/order?{query_string_with_sig}",
    headers=headers
)

print(response.json())
```

## 最佳实践

1. **错误处理**: 始终处理 API 错误响应
2. **速率限制**: 合理控制请求频率，避免被限制
3. **时间同步**: 确保本地时间与服务器时间同步
4. **安全性**: 
   - 不要在代码中硬编码 API 密钥
   - 使用环境变量或配置文件
   - 限制 API 密钥的 IP 白名单
5. **测试**: 先在纸上交易模式测试，确认无误后再使用真实资金

## 相关链接

- 官方文档: https://docs.asterdex.com/product/aster-perpetual-pro/api/api-documentation
- GitHub 仓库: https://github.com/AsterDEX/api-doc
- API 管理页面: https://app.asterdex.com/api

