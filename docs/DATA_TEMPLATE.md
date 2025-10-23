# 交易数据模板说明

本文档详细说明了 Vibe Trader 机器人提供给 DeepSeek LLM 的数据结构。这些数据基于 `template.md` 和 `template-description.md` 的要求。

## 完整数据结构

```python
{
    "metadata": {
        "minutes_trading": int,        # 交易开始至今的分钟数
        "current_timestamp": str,      # 当前时间戳 (YYYY-MM-DD HH:MM:SS)
        "invocation_count": int        # 程序被调用的总次数
    },
    
    "coins_data": {
        "BTC-PERP": {
            "symbol": str,             # 交易对符号
            "current_price": float,    # 当前价格
            "funding_rate": float,     # 资金费率
            
            "open_interest": {
                "latest": float,       # 最新持仓量
                "average": float       # 平均持仓量
            },
            
            "order_book": {
                "bids": [[price, size], ...],  # 买盘前 5 档
                "asks": [[price, size], ...]   # 卖盘前 5 档
            },
            
            "intraday": {
                "interval": str,       # 时间间隔（如 "3m"）
                "prices": [float, ...],      # 收盘价序列
                "volumes": [float, ...],     # 成交量序列
                
                "indicators": {
                    # 完整指标序列（从旧到新）
                    "ema20": [float, ...],
                    "ema50": [float, ...],
                    "rsi7": [float, ...],
                    "rsi14": [float, ...],
                    "macd": [float, ...],
                    "macd_signal": [float, ...],
                    "macd_histogram": [float, ...],
                    "bollinger_bands": {
                        "upper": [float, ...],
                        "middle": [float, ...],
                        "lower": [float, ...]
                    },
                    "atr3": [float, ...],
                    "atr14": [float, ...],
                    "vwap": [float, ...],
                    "adx": [float, ...],
                    
                    # 当前值（快速访问）
                    "current": {
                        "ema20": float,
                        "ema50": float,
                        "rsi7": float,
                        "rsi14": float,
                        "macd": float,
                        "macd_signal": float,
                        "macd_histogram": float,
                        "bb_upper": float,
                        "bb_middle": float,
                        "bb_lower": float,
                        "atr3": float,
                        "atr14": float,
                        "vwap": float,
                        "adx": float
                    }
                }
            },
            
            "longterm": {
                "interval": str,       # 时间间隔（如 "4h"）
                "indicators": {
                    # 长期指标结构与 intraday 相同
                    "ema20": [float, ...],
                    "ema50": [float, ...],
                    # ... 等等
                    "current": { ... }
                }
            }
        },
        # 其他币种 (ETH-PERP, SOL-PERP, ...) 结构相同
    },
    
    "account_info": {
        "total_return_percent": float,     # 总回报率百分比
        "available_cash": float,           # 可用现金（USDT）
        "account_value": float,            # 账户总价值
        "sharpe_ratio": float,             # 夏普比率
        
        "positions": [
            {
                "symbol": str,             # 持仓币种
                "side": str,               # "LONG" 或 "SHORT"
                "size": float,             # 持仓数量
                "entry_price": float,      # 开仓价格
                "mark_price": float,       # 标记价格
                "liquidation_price": float,# 强平价格
                "unrealized_pnl": float,   # 未实现盈亏
                "leverage": int            # 杠杆倍数
            },
            # ... 更多持仓
        ]
    }
}
```

## 数据获取流程

### 1. 元数据（Metadata）

从 `DataAggregator` 内部状态生成：

```python
metadata = {
    'minutes_trading': int((time.time() - self.start_time) / 60),
    'current_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
    'invocation_count': self.invocation_count
}
```

### 2. 市场数据（Coins Data）

为每个交易对：

#### a. 获取 K 线数据
```python
# 短期数据（3 分钟间隔）
intraday_klines = aster_client.get_klines(
    symbol="BTC-PERP",
    interval="3m",
    limit=100
)

# 长期数据（4 小时间隔）
longterm_klines = aster_client.get_klines(
    symbol="BTC-PERP",
    interval="4h",
    limit=50
)
```

#### b. 计算技术指标
```python
# 解析 K 线为 OHLCV
ohlcv = indicators.parse_klines(klines)

# 计算指标
ema20 = indicators.calculate_ema(ohlcv['close'], 20)
rsi14 = indicators.calculate_rsi(ohlcv['close'], 14)
macd, signal, hist = indicators.calculate_macd(ohlcv['close'])
# ... 等等
```

#### c. 获取资金费率
```python
funding_data = aster_client.get_funding_rate("BTC-PERP")
funding_rate = funding_data['fundingRate']
```

#### d. 获取订单簿
```python
order_book = aster_client.get_order_book("BTC-PERP", limit=10)
bids = order_book['bids'][:5]  # 前 5 档
asks = order_book['asks'][:5]
```

### 3. 账户信息（Account Info）

```python
# 获取账户余额
balances = aster_client.get_account_balances()
total_equity = balances['totalEquity']
available_cash = balances['availableBalance']

# 获取持仓
positions = aster_client.get_positions()

# 格式化持仓
formatted_positions = [
    {
        'symbol': pos['symbol'],
        'side': pos['side'],
        'size': float(pos['size']),
        'entry_price': float(pos['entryPrice']),
        'mark_price': float(pos['markPrice']),
        'liquidation_price': float(pos['liquidationPrice']),
        'unrealized_pnl': float(pos['unrealizedPnl']),
        'leverage': int(pos['leverage'])
    }
    for pos in positions
]
```

## 技术指标详解

### EMA (Exponential Moving Average)
- **用途**: 趋势识别
- **周期**: 20, 50
- **信号**: 
  - 价格 > EMA: 看涨
  - EMA20 > EMA50: 看涨交叉

### RSI (Relative Strength Index)
- **用途**: 超买超卖识别
- **周期**: 7, 14
- **范围**: 0-100
- **信号**:
  - RSI < 30: 超卖（可能反弹）
  - RSI > 70: 超买（可能回调）

### MACD (Moving Average Convergence Divergence)
- **用途**: 趋势和动量
- **参数**: 12, 26, 9
- **信号**:
  - MACD > Signal: 看涨
  - MACD 柱状图由负转正: 买入信号

### Bollinger Bands
- **用途**: 波动率和价格范围
- **参数**: 20 周期, 2 标准差
- **信号**:
  - 价格触及下轨: 可能超卖
  - 价格触及上轨: 可能超买
  - 带宽收窄: 波动率降低，可能突破

### ATR (Average True Range)
- **用途**: 波动率测量
- **周期**: 3, 14
- **用途**: 
  - 仓位大小调整（高 ATR = 小仓位）
  - 止损距离设定

### VWAP (Volume Weighted Average Price)
- **用途**: 成交量加权平均价
- **信号**:
  - 价格 > VWAP: 买方占优
  - 价格 < VWAP: 卖方占优

### ADX (Average Directional Index)
- **用途**: 趋势强度
- **周期**: 14
- **范围**: 0-100
- **信号**:
  - ADX > 25: 强趋势
  - ADX < 20: 弱趋势/盘整

## 数据格式化为提示词

`SignalGenerator._construct_prompt()` 方法将这些数据格式化为人类可读的提示词：

```python
prompt = f"""
It has been {minutes_trading} minutes since you started trading.
The current time is {current_timestamp} and you've been invoked {invocation_count} times.

ALL BTC-PERP DATA
current_price = 67500.00, current_ema20 = 67200.00, current_macd = 150.50, current_rsi (7 period) = 55.30

Intraday series (3m interval, oldest → latest):
Mid prices: [66800.0, 66850.0, ..., 67500.0]
EMA indicators (20-period): [66500.0, 66550.0, ..., 67200.0]
MACD indicators: [120.5, 125.3, ..., 150.5]
...

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): 2.50%
Available Cash: $9500.00
Current Account Value: $10250.00
...
"""
```

## 数据质量保证

### 处理缺失值
- 指标计算不足时返回 `NaN`
- 在格式化时过滤 `NaN` 值
- API 失败时使用默认值（0.0）

### 数据验证
```python
# 检查 K 线数据
if len(klines) < required_periods:
    logger.warning(f"Insufficient kline data: {len(klines)}")
    
# 验证指标计算
if math.isnan(current_rsi):
    current_rsi = 50.0  # 中性值
```

### 错误处理
```python
try:
    funding_rate = client.get_funding_rate(symbol)
except Exception as e:
    logger.error(f"Failed to fetch funding rate: {e}")
    funding_rate = 0.0  # 默认值
```

## 示例：完整数据快照

```json
{
  "metadata": {
    "minutes_trading": 120,
    "current_timestamp": "2025-10-22 14:30:00",
    "invocation_count": 24
  },
  "coins_data": {
    "BTC-PERP": {
      "symbol": "BTC-PERP",
      "current_price": 67500.00,
      "funding_rate": 0.0001,
      "open_interest": {
        "latest": 1500000000,
        "average": 1450000000
      },
      "intraday": {
        "interval": "3m",
        "prices": [66800, 66850, ..., 67500],
        "indicators": {
          "current": {
            "ema20": 67200.00,
            "ema50": 66800.00,
            "rsi7": 55.3,
            "rsi14": 52.1,
            "macd": 150.5,
            "macd_signal": 145.2,
            "bb_upper": 68000.0,
            "bb_middle": 67300.0,
            "bb_lower": 66600.0,
            "atr14": 250.0,
            "vwap": 67350.0,
            "adx": 28.5
          }
        }
      }
    }
  },
  "account_info": {
    "total_return_percent": 2.5,
    "available_cash": 9500.00,
    "account_value": 10250.00,
    "sharpe_ratio": 1.2,
    "positions": [
      {
        "symbol": "ETH-PERP",
        "side": "LONG",
        "size": 5.0,
        "entry_price": 3500.00,
        "mark_price": 3550.00,
        "liquidation_price": 3200.00,
        "unrealized_pnl": 250.00,
        "leverage": 5
      }
    ]
  }
}
```

这个数据结构完全符合 `template.md` 和 `template-description.md` 的要求，为 DeepSeek LLM 提供了全面的市场信息以生成高质量的交易信号。

