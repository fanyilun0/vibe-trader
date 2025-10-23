# Aster DEX API 文档

本文档提供 Aster DEX Perpetual Futures API v3 的快速参考指南。

## API 基础信息

- **Base URL**: `https://fapi.asterdex.com`
- **认证方式**: HMAC-SHA256 签名
- **请求头**:
  - `API-KEY`: 您的 API Key
  - `API-SIGN`: 请求签名
  - `API-TIMESTAMP`: 请求时间戳（毫秒）
  - `API-PASSPHRASE`: API 密码短语（可选）

## 签名生成

签名算法：
```python
prehash_string = f"{timestamp}{method.upper()}{path}{body}"
signature = hmac.new(
    api_secret.encode('utf-8'),
    prehash_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

## 公开端点（无需签名）

### 获取所有市场
- **端点**: `GET /api/v3/contracts`
- **参数**: 无
- **返回**: 所有可用合约列表

### 获取行情数据
- **端点**: `GET /api/v3/ticker`
- **参数**: 
  - `symbol`: 交易对符号（如 "BTC-PERP"）
- **返回**: 当前价格、24h 变化等

### 获取订单簿
- **端点**: `GET /api/v3/depth`
- **参数**:
  - `symbol`: 交易对符号
  - `limit`: 返回档位数量（默认 20）
- **返回**: 买卖盘深度

### 获取 K 线数据
- **端点**: `GET /api/v3/klines`
- **参数**:
  - `symbol`: 交易对符号
  - `interval`: 时间间隔（1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w）
  - `startTime`: 开始时间（毫秒时间戳）
  - `endTime`: 结束时间（毫秒时间戳）
  - `limit`: 返回条数（默认 100）
- **返回**: K 线数组 `[timestamp, open, high, low, close, volume, ...]`

### 获取资金费率
- **端点**: `GET /api/v3/fundingRate`
- **参数**:
  - `symbol`: 交易对符号
- **返回**: 当前资金费率

## 私有端点（需要签名）

### 下单
- **端点**: `POST /api/v3/orders`
- **参数**:
  - `symbol`: 交易对符号
  - `side`: "BUY" 或 "SELL"
  - `type`: "MARKET" 或 "LIMIT"
  - `size`: 订单数量
  - `price`: 价格（限价单必需）
  - `leverage`: 杠杆倍数（可选）
  - `stopLoss`: 止损价格（可选）
  - `takeProfit`: 止盈价格（可选）
- **返回**: 订单信息

### 取消订单
- **端点**: `DELETE /api/v3/orders/{orderId}`
- **参数**:
  - `orderId`: 订单 ID（路径参数）
  - `symbol`: 交易对符号（查询参数）
- **返回**: 取消结果

### 获取当前委托
- **端点**: `GET /api/v3/openOrders`
- **参数**:
  - `symbol`: 交易对符号（可选，过滤特定币种）
- **返回**: 所有未完成订单列表

### 获取账户余额
- **端点**: `GET /api/v3/accounts`
- **参数**: 无
- **返回**: 账户余额和权益信息

### 获取持仓
- **端点**: `GET /api/v3/positions`
- **参数**:
  - `symbol`: 交易对符号（可选）
- **返回**: 当前持仓列表

### 设置杠杆
- **端点**: `POST /api/v3/leverage`
- **参数**:
  - `symbol`: 交易对符号
  - `leverage`: 杠杆倍数（1-100）
- **返回**: 设置结果

### 设置保证金模式
- **端点**: `POST /api/v3/marginType`
- **参数**:
  - `symbol`: 交易对符号
  - `marginType`: "ISOLATED" 或 "CROSSED"
- **返回**: 设置结果

## 常用交易对符号

- `BTC-PERP`: 比特币永续合约
- `ETH-PERP`: 以太坊永续合约
- `SOL-PERP`: Solana 永续合约
- `BNB-PERP`: BNB 永续合约

## 错误处理

API 可能返回以下错误代码：
- `400`: 请求参数错误
- `401`: 认证失败
- `403`: 无权限
- `404`: 资源不存在
- `429`: 请求过于频繁
- `500`: 服务器内部错误

## 限流

请注意 API 限流规则，避免过于频繁的请求导致被限制访问。

## 参考资源

- [Aster DEX 官方 API 文档](https://github.com/asterdex/api-docs)
- [社区实现示例](https://github.com/asteraiagent/)
